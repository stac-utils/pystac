from __future__ import annotations

import copy
import warnings
from typing import TYPE_CHECKING, Any, override

from typing_extensions import deprecated

from pystac.errors import STACError
from pystac.rel_type import RelType
from pystac.utils import make_absolute_href

from .reader import Reader

if TYPE_CHECKING:
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
        # target is mostly for backwards compatibility, if we were to design it
        # from scratch we wouldn't do it this way,
        target: str | STACObject | None = None,
        href: str | None = None,
        type: str | None = None,
        title: str | None = None,
        method: str | None = None,
        headers: dict[str, str | list[str]] | None = None,
        body: Any | None = None,
        **kwargs: Any,
    ):
        from .stac_object import STACObject

        self.rel: str = rel
        self.type: str | None = type
        self.title: str | None = title
        self.method: str | None = method
        self.headers: dict[str, str | list[str]] | None = headers
        self.body: Any | None = body
        self.extra_fields: dict[str, Any] = kwargs

        if isinstance(target, STACObject):
            self._href: str | None = href or target.get_self_href()
            self.target: STACObject | None = target
        elif href and target:
            raise ValueError("Both target and href were provided as strings")
        elif not href and not target:
            raise ValueError("Neither href nor target were provided")
        else:
            self._href = href or target
            self.target = None

    @classmethod
    def try_from(cls, data: dict[str, Any] | Link) -> Link:
        if isinstance(data, Link):
            return data
        else:
            return cls(**data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Link:
        return cls(**data)

    @property
    @deprecated("media_type is now called type")
    def media_type(self) -> str | None:
        return self.type

    def is_hierarchical(self) -> bool:
        return self.rel in HIERARCHICAL_LINKS

    def is_self(self) -> bool:
        return self.rel == RelType.SELF

    def is_item(self) -> bool:
        return self.rel == RelType.ITEM

    def is_child(self) -> bool:
        return self.rel == RelType.CHILD

    def is_derived_from(self) -> bool:
        return self.rel == RelType.DERIVED_FROM

    def get_href(self) -> str | None:
        return self._href or self.target and self.target.get_self_href()

    def get_target(self, start_href: str | None, reader: Reader) -> STACObject:
        from .stac_object import STACObject

        if not self.target:
            if not self._href:
                raise ValueError("No target and no href on the link")

            href = make_absolute_href(self._href, start_href, start_is_dir=False)
            try:
                self.target = STACObject.from_file(href, reader=reader)
            except Exception as e:
                raise STACError(f"Error while resolving link: {e}")

        return self.target

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
        elif self.target and (href := self.target.get_self_href()):
            data["href"] = href
        else:
            raise ValueError("No href or target self href on the link")
        data["rel"] = self.rel
        if self.type is not None:
            data["type"] = self.type
        if self.title is not None:
            data["title"] = self.title
        if self.method is not None:
            data["method"] = self.method
        if self.headers is not None:
            data["headers"] = self.headers
        if self.body is not None:
            data["body"] = self.body
        return data

    @override
    def __repr__(self) -> str:
        return f"Link(rel={self.rel}, href={self._href})"
