from __future__ import annotations

import urllib.parse
import warnings
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

from typing_extensions import Self

from .constants import (
    CATALOG_TYPE,
    COLLECTION_TYPE,
    DEFAULT_STAC_VERSION,
    ITEM_TYPE,
    PARENT_REL,
    ROOT_REL,
    SELF_REL,
)
from .errors import PystacError, StacError
from .link import Link

if TYPE_CHECKING:
    from .catalog import Catalog
    from .container import Container
    from .io import Read, Write


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
        reader: Read | None = None,
        writer: Write | None = None,
    ) -> Self:
        """Reads a STAC object from a JSON file.

        Raises:
            StacError: Raised if the object's type does not match the calling class.

        Examples:
            >>> catalog = Catalog.from_file("catalog.json")
            >>> Item.from_file("catalog.json") # Will raise a `StacError`
        """
        from .io import DefaultReader

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
            raise PystacError(f"JSON is not a dict: {type(d)}")

        stac_object = cls.from_dict(d, href=str(href), reader=reader, writer=writer)
        if isinstance(stac_object, cls):
            return stac_object
        else:
            raise StacError(f"expected {cls}, read {type(stac_object)} from {href}")

    @classmethod
    def from_dict(
        cls: type[Self],
        d: dict[str, Any],
        *,
        href: str | None = None,
        root: Catalog | None = None,
        migrate: bool = False,
        preserve_dict: bool = True,  # TODO deprecation warning
        reader: Read | None = None,
        writer: Write | None = None,
    ) -> Self:
        """Creates a STAC object from a dictionary.

        If you already know what type of STAC object your dictionary represents,
        use the initializer directly, e.g. `Catalog(**d)`.

        Args:
            d: A JSON dictionary

        Returns:
            A STAC object

        Raises:
            StacError: If the type field is not present or not a value we recognize.

        Examples:
            >>> # Use this when you don't know what type of object it is
            >>> stac_object = STACObject.from_dict(d)
            >>> # Use this when you know you have a catalog
            >>> catalog = Catalog(**d)
        """
        if type_value := d.get("type"):
            if type_value == CATALOG_TYPE:
                from .catalog import Catalog

                stac_object: STACObject = Catalog(
                    **d, href=href, reader=reader, writer=writer
                )
            elif type_value == COLLECTION_TYPE:
                from .collection import Collection

                stac_object = Collection(**d, href=href, reader=reader, writer=writer)
            elif type_value == ITEM_TYPE:
                from .item import Item

                stac_object = Item(**d, href=href, reader=reader, writer=writer)
            else:
                raise StacError(f"unknown type field: {type_value}")

            if isinstance(stac_object, cls):
                if root:
                    warnings.warn(
                        "The `root` argument is deprecated in PySTAC v2 and "
                        "will be removed in a future version. Prefer to use "
                        "`stac_object.set_link(Link.root(catalog))` "
                        "after object creation.",
                        FutureWarning,
                    )
                    stac_object.set_link(Link.root(root))
                return stac_object
            else:
                raise PystacError(f"Expected {cls} but got a {type(stac_object)}")
        else:
            raise StacError("missing type field on dictionary")

    def __init__(
        self,
        id: str,
        stac_version: str | None = None,
        stac_extensions: list[str] | None = None,
        links: list[Link | dict[str, Any]] | None = None,
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

        self.href: str | None
        """This object's href

        This is where it was read from, or where it should be written to. We
        don't use the `self` link (like PySTAC v1.0 did) because there's time
        you don't want a self link, but you still want to track an object's
        location.
        """
        if href is None and (self_link := self.get_link(SELF_REL)):
            self.href = self_link.href
        else:
            self.href = href

    def read_file(self, href: str) -> STACObject:
        """Reads a new STAC object from a file.

        This method will resolve relative hrefs by using this STAC object's href
        or, if not set, its `self` link.
        """
        from . import io

        base = self.href
        if base is None and (link := self.get_link(SELF_REL)):
            base = link.href

        href = io.make_absolute_href(href, base)
        return STACObject.from_file(href, reader=self.reader, writer=self.writer)

    def save_object(
        self,
        include_self_link: bool | None = None,
        dest_href: str | Path | None = None,
        stac_io: Any = None,
    ) -> None:
        from . import io

        if include_self_link is not None:
            warnings.warn(
                "The include_self_link argument to `save_object` is deprecated as of "
                "PySTAC v2.0 and will be removed in a future version. Prefer to add "
                "or remove a self link directly before calling `save_object`.",
                FutureWarning,
            )
            self.set_self_link()
        if stac_io:
            warnings.warn("Discarding StacIO. TODO either use it or error")
        if not dest_href:
            dest_href = self.href
        if dest_href:
            io.write_file(self, href=dest_href, writer=self.writer)
        else:
            raise PystacError("cannot save an object without an href")

    def get_root(self) -> Container | None:
        """Returns the container at this object's root link, if there is one."""
        from .container import Container

        if link := self.get_link(ROOT_REL):
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

    def iter_links(self, rel: str | None = None) -> Iterator[Link]:
        for link in self._links:
            if rel is None or rel == link.rel:
                yield link

    def set_link(self, link: Link) -> None:
        self.remove_links(link.rel)
        link.owner = self
        self._links.append(link)

    def set_self_link(self) -> None:
        if self.href is None:
            raise PystacError("cannot set a self link without an href")
        else:
            self.set_link(Link.self(self))

    def remove_links(self, rel: str) -> None:
        self._links = [link for link in self._links if link.rel != rel]

    def add_link(self, link: Link) -> None:
        link.owner = self
        self._links.append(link)

    def get_root_link(self) -> Link | None:
        return self.get_link(ROOT_REL)

    def get_parent_link(self) -> Link | None:
        return self.get_link(PARENT_REL)

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
