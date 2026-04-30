from __future__ import annotations

import copy
import warnings
from typing import TYPE_CHECKING, Any, Self, override

from typing_extensions import deprecated

import pystac
from pystac.errors import STACError
from pystac.media_type import MediaType
from pystac.rel_type import RelType
from pystac.utils import is_absolute_href, make_absolute_href, make_posix_style

from .reader import Reader

if TYPE_CHECKING:
    from . import Catalog, Collection, Item
    from .extensions.ext import LinkExt
    from .stac_object import STACObject

HIERARCHICAL_LINKS = [
    RelType.SELF,
    RelType.CHILD,
    RelType.PARENT,
    RelType.ROOT,
    RelType.COLLECTION,
]


class Link:
    def __init__(
        self,
        rel: str,
        target: str | STACObject | None = None,
        href: str | None = None,
        media_type: str | None = None,
        title: str | None = None,
        method: str | None = None,
        headers: dict[str, str | list[str]] | None = None,
        body: Any | None = None,
        **kwargs: Any,
    ):
        from .stac_object import STACObject

        self.rel: str = rel
        self.media_type: str | None = media_type
        self.title: str | None = title
        self.method: str | None = method
        self.headers: dict[str, str | list[str]] | None = headers
        self.body: Any | None = body
        extra_fields = kwargs.pop("extra_fields", None)
        self.extra_fields: dict[str, Any] = kwargs
        if extra_fields:
            warnings.warn(
                "Pass extra_fields entries as kwargs "
                "instead of extra_fields as keyword argument."
            )
            self.extra_fields.update(extra_fields)

        if isinstance(target, STACObject):
            self._href: str | None = href or target.get_self_href()
            self.title = title or getattr(target, "title", None)
            self._target: STACObject | None = target
        elif href and target:
            raise ValueError("Both target and href were provided as strings")
        elif not href and not target:
            raise ValueError("Neither href nor target were provided")
        else:
            self._href = href or target
            self._target = None
        # backwards compat allows 'target' parameter to be str,
        # so we delay in posix conversion until here
        if self._href is not None:
            self._href = make_posix_style(self._href)

    def __fspath__(self) -> str:
        if self._target and (href := self._target.get_self_href()):
            return href
        elif self._href:
            return self._href
        else:
            raise ValueError(
                "Link cannot be used for an __fspath__, target does not have a self "
                "link and _href is not set"
            )

    @override
    def __getattribute__(self, name: str, /) -> Any:
        if name == "owner":
            warnings.warn("Link.owner is deprecated, and is always None in pystac v2")
            return None
        else:
            return super().__getattribute__(name)

    def clone(self: Self) -> Self:
        return copy.deepcopy(self)

    @classmethod
    def try_from(cls, data: dict[str, Any] | Link) -> Link:
        if isinstance(data, Link):
            return data
        else:
            return cls(**data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Link:
        return cls(**data)

    def is_hierarchical(self) -> bool:
        return self.rel in HIERARCHICAL_LINKS

    def is_self(self) -> bool:
        return self.rel == RelType.SELF

    def is_root(self) -> bool:
        return self.rel == RelType.ROOT

    def is_item(self) -> bool:
        return self.rel == RelType.ITEM and self.media_type is None or self.is_json()

    def is_child(self) -> bool:
        return self.rel == RelType.CHILD and self.media_type is None or self.is_json()

    def is_derived_from(self) -> bool:
        return self.rel == RelType.DERIVED_FROM

    def is_resolved(self) -> bool:
        return self._target is not None

    def is_json(self) -> bool:
        return self.media_type in (MediaType.JSON, MediaType.GEOJSON)

    def get_href(self) -> str | None:
        return self._href or self._target and self._target.get_self_href()

    def get_absolute_href(self, start_href: str = "") -> str | None:
        href = self.get_href()
        if href is None:
            return href
        return make_absolute_href(href, start_href, start_is_dir=False)

    def set_href(self, href: str) -> None:
        self._href = href

    @property
    @deprecated("href is deprecated, use .get_href()")
    def href(self) -> str | None:
        return self.get_href()

    @property
    @deprecated("target is deprecated, either use .get_href() or .get_target()")
    def target(self) -> str | STACObject | None:
        return self._target or self._href

    @target.setter
    @deprecated("target is deprecated, either use .set_href() or .set_target()")
    def target(self, value: str | STACObject) -> None:
        if isinstance(value, str):
            warnings.warn(
                "Setting Link.target to href is no longer supported pystac v2.  "
                "Assigning value to href instead."
            )
            self.set_href(value)
        else:
            self.set_target(value)
            if href := value.get_self_href():
                self.set_href(href)

    @deprecated("use .get_href()")
    def get_target_str(self) -> str | None:
        """Returns this link's target as a string.

        If a string href was provided, returns that. If not, tries to resolve
        the self link of the target object.
        """
        return self.get_href()

    @deprecated("use bool(link.get_href())")
    def has_target_href(self) -> bool:
        """Returns true if this link has a string href in its target information."""
        return bool(self.get_href())

    def get_target(self, start_href: str | None, reader: Reader) -> STACObject:
        from .stac_object import STACObject

        if not self._target:
            if not self._href:
                raise ValueError("No target and no href on the link")

            href = make_absolute_href(self._href, start_href, start_is_dir=False)
            try:
                self._target = STACObject.from_file(href, reader=reader)
            except Exception as e:
                raise STACError(f"Error while resolving link: {e}")

        return self._target

    def maybe_get_target(self) -> STACObject | None:
        return self._target

    def set_target(self, target: STACObject) -> None:
        self._target = target

    def to_dict(self, transform_href: bool | None = None) -> dict[str, Any]:
        if transform_href is not None:
            warnings.warn(
                "Transforming href is deprecated and will be removed in a "
                "future version.",
                DeprecationWarning,
            )
            if transform_href:
                raise NotImplementedError
        data = copy.deepcopy(self.extra_fields)
        if self._href:
            data["href"] = self._href
        elif self._target and (href := self._target.get_self_href()):
            data["href"] = href
        else:
            raise ValueError("No href or target self href on the link")
        data["rel"] = self.rel
        if self.media_type is not None:
            data["type"] = self.media_type
        if self.title is not None:
            data["title"] = self.title
        if self.method is not None:
            data["method"] = self.method
        if self.headers is not None:
            data["headers"] = self.headers
        if self.body is not None:
            data["body"] = self.body
        return data

    def resolve_stac_object(self, start_href: str = "") -> Link:
        """Resolves a STAC object from the HREF of this link, if the link is not
        already resolved.

        Args:
            start_href : Optional string to put ahead of the href in this Link.

        NOTE: This uses reader.DEFAULT_READER to read the HREF, if necessary.
        """
        if self._target:
            return self
        elif self._href:
            # If it's a relative link, base it off the parent.
            target_href = self._href
            if not is_absolute_href(target_href):
                target_href = make_absolute_href(self._href, start_href=start_href)
            try:
                obj = pystac.read_file(target_href)
            except Exception as e:
                raise STACError(
                    f"HREF: '{target_href}' does not resolve to a STAC object"
                ) from e
            self._target = obj
        else:
            raise ValueError("Cannot resolve STAC object without a target")

        return self

    @override
    def __repr__(self) -> str:
        return f"Link(rel={self.rel}, href={self._href})"

    ##### Convenience methods for Link creation #####
    @classmethod
    def root(cls: type[Self], c: Catalog) -> Self:
        """Creates a link to a root Catalog or Collection."""
        return cls(RelType.ROOT, c, media_type=MediaType.JSON)

    @classmethod
    def parent(cls: type[Self], c: Catalog, title: str | None = None) -> Self:
        """Creates a link to a parent Catalog or Collection."""
        return cls(RelType.PARENT, c, title=title, media_type=MediaType.JSON)

    @classmethod
    def collection(cls: type[Self], c: Collection) -> Self:
        """Creates a link to a Collection."""
        return cls(RelType.COLLECTION, c, media_type=MediaType.JSON)

    @classmethod
    def self_href(cls: type[Self], href: str) -> Self:
        """Creates a self link to a file's location."""
        return cls(RelType.SELF, href, media_type=MediaType.JSON)

    @classmethod
    def child(cls: type[Self], c: Catalog, title: str | None = None) -> Self:
        """Creates a link to a child Catalog or Collection."""
        return cls(RelType.CHILD, c, title=title, media_type=MediaType.JSON)

    @classmethod
    def item(cls: type[Self], item: Item, title: str | None = None) -> Self:
        """Creates a link to an Item."""
        return cls(RelType.ITEM, item, title=title, media_type=MediaType.GEOJSON)

    @classmethod
    def derived_from(
        cls: type[Self], item: Item | str, title: str | None = None
    ) -> Self:
        """Creates a link to a derived_from Item."""
        return cls(
            RelType.DERIVED_FROM,
            item,
            title=title,
            media_type=MediaType.JSON,
        )

    @classmethod
    def canonical(
        cls: type[Self],
        item_or_collection: Item | Collection,
        title: str | None = None,
    ) -> Self:
        """Creates a canonical link to an Item or Collection."""
        return cls(
            RelType.CANONICAL,
            item_or_collection,
            title=title,
            media_type=MediaType.JSON,
        )

    @property
    def ext(self) -> LinkExt:
        """Accessor for extension classes on this link

        Example::

            link.ext.file.size = 8675309
        """
        from pystac.extensions.ext import LinkExt

        return LinkExt(stac_object=self)
