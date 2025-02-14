from __future__ import annotations

import urllib.parse
import warnings
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

from typing_extensions import Self

from . import deprecate, utils
from .asset import Asset
from .constants import (
    CATALOG_TYPE,
    CHILD,
    COLLECTION_TYPE,
    DEFAULT_STAC_VERSION,
    ITEM,
    ITEM_TYPE,
    PARENT,
    ROOT,
    SELF,
)
from .errors import PySTACError, STACError
from .link import Link

if TYPE_CHECKING:
    from .catalog import Catalog
    from .container import Container
    from .io import Read, Write
    from .render import Render


class STACObject(ABC):
    """The base class for all STAC objects."""

    @classmethod
    @abstractmethod
    def get_type(cls: type[Self]) -> str:
        """Returns the `type` field for this STAC object.

        Examples:
            >>> print(Item.get_type())
            "Feature"
        """

    @classmethod
    def from_file(
        cls: type[Self],
        href: str | Path,
        stac_io: Any = None,
        *,
        reader: Read | None = None,
    ) -> Self:
        """Reads a STAC object from a JSON file.

        Args:
            href: The file to read
            reader: The reader to use for the read. This will be saved as the
                `.reader` attribute of the read object.

        Raises:
            STACError: Raised if the object's type does not match the calling class.

        Examples:
            >>> catalog = Catalog.from_file("catalog.json")
            >>> Item.from_file("catalog.json") # Will raise a `STACError`
        """
        from .io import DefaultReader

        if stac_io:
            deprecate.argument("stac_io")
            # TODO build reader

        if reader is None:
            reader = DefaultReader()

        if isinstance(href, Path):
            d = reader.read_json_from_path(href)
        else:
            url = urllib.parse.urlparse(href)
            if url.scheme:
                d = reader.read_json_from_url(href)
            else:
                d = reader.read_json_from_path(Path(href))

        if not isinstance(d, dict):
            raise PySTACError(f"JSON is not a dict: {type(d)}")

        stac_object = cls.from_dict(d)
        stac_object.href = str(href)
        stac_object.reader = reader
        if isinstance(stac_object, cls):
            return stac_object
        else:
            raise STACError(f"expected {cls}, read {type(stac_object)} from {href}")

    @classmethod
    def from_dict(
        cls: type[Self],
        d: dict[str, Any],
        href: str | None = None,
        root: Catalog | None = None,
        migrate: bool | None = None,
        preserve_dict: bool | None = None,
    ) -> Self:
        """Creates a STAC object from a dictionary.

        If you already know what type of STAC object your dictionary represents,
        use the initializer directly, e.g. `Catalog(**d)`.

        Args:
            d: A JSON dictionary

        Returns:
            A STAC object

        Raises:
            STACError: If the type field is not present or not a value we recognize.

        Examples:
            >>> # Use this when you don't know what type of object it is
            >>> stac_object = STACObject.from_dict(d)
            >>> # Use this when you know you have a catalog
            >>> catalog = Catalog(**d)
        """
        if href is not None:
            deprecate.argument("href")
        if root is not None:
            deprecate.argument("root")
        if migrate is not None:
            deprecate.argument("migrate")
        else:
            migrate = False
        if preserve_dict is not None:
            deprecate.argument("preserve_dict")
        else:
            preserve_dict = True

        if type_value := d.get("type"):
            if type_value == CATALOG_TYPE:
                from .catalog import Catalog

                stac_object: STACObject = Catalog(
                    **d,
                    href=href,
                )
            elif type_value == COLLECTION_TYPE:
                from .collection import Collection

                stac_object = Collection(**d, href=href)
            elif type_value == ITEM_TYPE:
                from .item import Item

                stac_object = Item(**d, href=href)
            else:
                raise STACError(f"invalid type field: {type_value}")
            if isinstance(stac_object, cls):
                if root:
                    stac_object.set_link(Link.root(root))
                return stac_object
            else:
                raise PySTACError(f"expected {cls} but got a {type(stac_object)}")
        else:
            raise STACError("missing type field on dictionary")

    def __init__(
        self,
        id: str,
        stac_version: str | None = None,
        stac_extensions: list[str] | None = None,
        links: list[Link | dict[str, Any]] | None = None,
        assets: dict[str, Asset | dict[str, Any]] | None = None,
        href: str | None = None,
        reader: Read | None = None,
        writer: Write | None = None,
        **kwargs: Any,
    ) -> None:
        """Creates a new STAC object."""
        from .extensions import Extensions

        super().__init__()

        self.id: str = id
        """The object's id."""

        self.stac_version: str = stac_version or DEFAULT_STAC_VERSION
        """The object's STAC version."""

        self.stac_extensions: list[str] | None = stac_extensions
        """The object's STAC extension schema urls."""

        self.extra_fields: dict[str, Any] = kwargs
        """Any extra fields on this object."""

        self.ext = Extensions(self)
        """This object's extension manager"""

        self.reader: Read
        """This object's reader."""
        if reader:
            self.reader = reader
        else:
            from .io import DefaultReader

            self.reader = DefaultReader()

        self.writer: Write
        """This object's writer."""
        if writer:
            self.writer = writer
        else:
            from .io import DefaultWriter

            self.writer = DefaultWriter()

        self._links: list[Link] = []
        if links is not None:
            for link in links:
                if isinstance(link, Link):
                    link.owner = self
                else:
                    link = Link.from_dict(link, owner=self)
                self._links.append(link)

        self.assets: dict[str, Asset] = {}
        if assets is not None:
            for key, value in assets.items():
                if isinstance(value, Asset):
                    asset = value
                else:
                    asset = Asset.from_dict(value)
                self.assets[key] = asset

        self.href: str | None
        """This object's href

        This is where it was read from, or where it should be written to. We
        don't use the `self` link (like PySTAC v1.0 did) because there's time
        you don't want a self link, but you still want to track an object's
        location.
        """
        if href is None and (self_link := self.get_link(SELF)):
            self.href = self_link.href
        else:
            self.href = href

    def read_file(self, href: str) -> STACObject:
        """Reads a new STAC object from a file.

        This method will resolve relative hrefs by using this STAC object's href
        or, if not set, its `self` link.
        """

        base = self.href
        if base is None and (link := self.get_link(SELF)):
            base = link.href

        href = utils.make_absolute_href(href, base)
        stac_object = STACObject.from_file(href, reader=self.reader)
        stac_object.writer = self.writer
        return stac_object

    def save_object(
        self,
        include_self_link: bool | None = None,
        dest_href: str | Path | None = None,
        stac_io: Any = None,
        *,
        writer: Write | None = None,
    ) -> None:
        from . import io

        if include_self_link is not None:
            deprecate.argument("include_self_link")
            self.set_self_link()
        if stac_io:
            deprecate.argument("stac_io")
        if not dest_href:
            dest_href = self.href
        if not writer:
            writer = self.writer
        if dest_href:
            io.write_file(self, dest_href=dest_href, writer=self.writer)
        else:
            raise PySTACError("cannot save an object without an href")

    def get_root(self) -> Container | None:
        """Returns the container at this object's root link, if there is one."""
        from .container import Container

        if link := self.get_root_link():
            stac_object = link.get_stac_object()
            if isinstance(stac_object, Container):
                return stac_object
            else:
                return None
        else:
            return None

    def get_link(self, rel: str) -> Link | None:
        return next((link for link in self._links if link.rel == rel), None)

    def get_fields(self) -> dict[str, Any]:
        return self.extra_fields

    def iter_links(self, *rels: str) -> Iterator[Link]:
        """Iterate over links, optionally filtering by one or more relation types.

        Examples:

            >>> from pystac import CHILD, ITEM
            >>> links = list(item.iter_links())
            >>> child_links = list(item.iter_links(CHILD))
            >>> sub_links = list(item.iter_links(CHILD, ITEM))
        """
        for link in self._links:
            if not rels or link.rel in rels:
                yield link

    def set_link(self, link: Link) -> None:
        self.remove_links(link.rel)
        link.owner = self
        self._links.append(link)

    def set_self_link(self) -> None:
        if self.href is None:
            raise PySTACError("cannot set a self link without an href")
        else:
            self.set_link(Link.self(self))

    @deprecate.function("Prefer to get the href directly")
    def get_self_href(self) -> str | None:
        return self.href

    @deprecate.function("Prefer to set href directly, and then use `render()`")
    def set_self_href(self, href: str | None = None) -> None:
        self.href = href
        if self.href:
            self.render(include_self_link=True)
        else:
            self.remove_links(SELF)

    @deprecate.function("Prefer to set the asset directly")
    def add_asset(self, key: str, asset: Asset) -> None:
        self.assets[key] = asset

    def migrate(self) -> None:
        # TODO do more
        self.stac_version = DEFAULT_STAC_VERSION

    def render(
        self,
        root: str | Path | None = None,
        *,
        renderer: Render | None = None,
        include_self_link: bool = True,
        use_relative_asset_hrefs: bool = False,
    ) -> None:
        from .container import Container

        if renderer is None:
            from .render import BestPracticesRenderer

            renderer = BestPracticesRenderer()

        if self.assets:
            for asset in self.assets.values():
                asset.href = utils.make_absolute_href(asset.href, self.href)

        if root:
            self.href = str(root) + "/" + renderer.get_file_name(self)
        if include_self_link:
            self.set_self_link()

        if isinstance(self, Container):
            if not self.href:
                raise PySTACError(
                    "cannot render a container if the STAC object's href is None "
                    "and no root is provided"
                )
            elif "/" in self.href:
                base = self.href.rsplit("/", 1)[0]
            else:
                base = "."

            root_link = self.get_root_link()
            if root_link is None:
                root_link = Link.root(self)
            for link in self.iter_links(CHILD, ITEM):
                leaf = link.get_stac_object()
                leaf.set_link(root_link)
                leaf.set_link(Link.parent(self))
                leaf.href = renderer.get_href(leaf, base)
                link.href = leaf.href
                leaf.render()

        if use_relative_asset_hrefs and self.assets:
            for asset in self.assets.values():
                assert self.href
                asset.href = utils.make_relative_href(asset.href, self.href)

    def remove_links(self, rel: str) -> None:
        self._links = [link for link in self._links if link.rel != rel]

    def add_link(self, link: Link) -> None:
        link.owner = self
        self._links.append(link)

    def get_root_link(self) -> Link | None:
        return self.get_link(ROOT)

    def get_parent_link(self) -> Link | None:
        return self.get_link(PARENT)

    def to_dict(
        self, include_self_link: bool | None = None, transform_hrefs: bool | None = None
    ) -> dict[str, Any]:
        if include_self_link is not None:
            warnings.warn(
                "The include_self_link argument to `to_dict` is deprecated as of "
                "PySTAC v2.0 and will be removed in a future version. It will be "
                "ignored. Prefer to add "
                "or remove a self link directly before calling `to_dict`.",
                FutureWarning,
            )
        if transform_hrefs is not None:
            warnings.warn(
                "The transform_hrefs argument to `to_dict` is deprecated as of "
                "PySTAC v2.0 and will be removed in a future version. It will "
                "be ignored. Prefer to transform "
                "hrefs directly, e.g. with `render()`, before calling `to_dict`.",
                FutureWarning,
            )
        return self._to_dict()

    @abstractmethod
    def _to_dict(self) -> dict[str, Any]:
        """Private method that is used to actually implement to_dict until we
        can remove the old arguments."""

    def validate(self) -> None:
        """Validates this STAC object using the default validator (jsonschema).

        If you want to validate multiple objects, it can be more efficient to
        create a validator directly, as the validator caches fetched schemas:

        ```python
        validator = pystac.validate.DefaultValidator()
        for stac_object in stac_objects:
            validator.validate(stac_object)
        ```

        Raises:
            ValidationError: If the STAC object is invalid, this error will
                contain all the underlying validation errors.
            ImportError: If pystac has not been installed with the `validate`
                extra dependency set (e.g. with `python -m pip install
                'pystac[validate]'`)
        """
        from .validate.jsonschema import JsonschemaValidator

        validator = JsonschemaValidator()
        validator.validate(self)

    def __repr__(self) -> str:
        return f"<pystac.{self.__class__.__name__} id={self.id}>"
