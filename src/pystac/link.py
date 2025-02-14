from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import Self

from .constants import CHILD, ITEM, PARENT, ROOT, SELF
from .errors import PystacError

if TYPE_CHECKING:
    from .item import Item
    from .stac_object import STACObject


class Link:
    @classmethod
    def from_dict(
        cls: type[Self],
        d: dict[str, Any],
        *,
        owner: STACObject | None = None,
        stac_object: STACObject | None = None,
    ) -> Self:
        return cls(**d, owner=owner, stac_object=stac_object)

    @classmethod
    def root(cls: type[Self], root: STACObject) -> Self:
        return cls(href=root.href, rel=ROOT, stac_object=root)

    @classmethod
    def parent(cls: type[Self], parent: STACObject) -> Self:
        return cls(href=parent.href, rel=PARENT, stac_object=parent)

    @classmethod
    def child(cls: type[Self], child: STACObject) -> Self:
        return cls(href=child.href, rel=CHILD, stac_object=child)

    @classmethod
    def item(cls: type[Self], item: Item) -> Self:
        return cls(href=item.href, rel=ITEM, stac_object=item)

    @classmethod
    def self(cls: type[Self], stac_object: STACObject) -> Self:
        return cls(href=stac_object.href, rel=SELF, stac_object=stac_object)

    def __init__(
        self,
        href: str | None,
        rel: str,
        type: str | None = None,
        title: str | None = None,
        method: str | None = None,
        headers: dict[str, str | list[str]] | None = None,
        body: Any | None = None,
        owner: STACObject | None = None,
        stac_object: STACObject | None = None,
    ) -> None:
        self.href = href
        self.rel = rel
        self.type = type
        self.title = title
        self.method = method
        self.headers = headers
        self.body = body
        self.owner = owner
        self._stac_object = stac_object
        # TODO extra fields

    def is_root(self) -> bool:
        return self.rel == ROOT

    def is_parent(self) -> bool:
        return self.rel == PARENT

    def is_child(self) -> bool:
        return self.rel == CHILD

    def is_item(self) -> bool:
        return self.rel == ITEM

    def is_self(self) -> bool:
        return self.rel == SELF

    def get_stac_object(self) -> STACObject:
        if self._stac_object is None:
            if self.href is None:
                raise PystacError("cannot get a STAC object for a link with no href")
            elif self.owner:
                self._stac_object = self.owner.read_file(self.href)
            else:
                from . import io

                self._stac_object = io.read_file(self.href)

        return self._stac_object

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "href": self.href,
            "rel": self.rel,
        }
        if self.type is not None:
            d["type"] = self.type
        if self.title is not None:
            d["title"] = self.title
        if self.method is not None:
            d["method"] = self.method
        if self.headers is not None:
            d["headers"] = self.headers
        if self.body is not None:
            d["body"] = self.body
        return d

    def __repr__(self) -> str:
        return f"<pystac.Link href={self.href} rel={self.rel} to={self._stac_object}>"
