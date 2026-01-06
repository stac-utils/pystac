from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any, Self, override

from . import deprecate, utils

if TYPE_CHECKING:
    from .stac_object import STACObject


class ItemAsset:
    """An asset without a href.

    This was made a "first-class" data structure in STAC v1.1.
    """

    @classmethod
    def from_dict(cls: type[Self], d: dict[str, Any]) -> Self:
        """Creates a new item asset from a dictionary."""
        return cls(**d)

    def __init__(
        self,
        title: str | None = None,
        description: str | None = None,
        type: str | None = None,
        roles: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Creates a new item asset."""
        from .extensions import Extensions

        self.title: str | None = title
        self.description: str | None = description
        self.type: str | None = type
        self.roles: list[str] | None = roles
        self.extra_fields: dict[str, Any] = kwargs

        self.ext: Extensions = Extensions(self)
        """This object's extension manager"""

    def to_dict(self) -> dict[str, Any]:
        """Converts this item asset to a dictionary."""
        d: dict[str, Any] = {}
        if self.title is not None:
            d["title"] = self.title
        if self.description is not None:
            d["description"] = self.description
        if self.type is not None:
            d["type"] = self.type
        if self.roles is not None:
            d["roles"] = self.roles
        d.update(copy.deepcopy(self.extra_fields))
        return d

    def get_fields(self) -> dict[str, Any]:
        return self.extra_fields


class Asset(ItemAsset):
    """An asset, e.g. a geospatial data file."""

    @classmethod
    @override
    def from_dict(cls: type[Self], d: dict[str, Any]) -> Self:
        """Creates an asset from a dictionary."""
        return cls(**d)

    def __init__(
        self,
        href: str,
        title: str | None = None,
        description: str | None = None,
        type: str | None = None,
        roles: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Creates a new asset."""
        self.href: str = href
        super().__init__(
            title=title, description=description, type=type, roles=roles, **kwargs
        )

    @deprecate.function(
        "assets aren't owned anymore, all this method does is make the asset's "
        "relative href absolute using the 'owner's href"
    )
    def set_owner(self, owner: STACObject) -> None:
        if owner.href:
            self.href = utils.make_absolute_href(self.href, owner.href)

    @deprecate.function("prefer to use `STACObject.render()` then `asset.href`")
    def get_absolute_href(self) -> str | None:
        if utils.is_absolute_href(self.href):
            return self.href
        else:
            return None

    @override
    def to_dict(self) -> dict[str, Any]:
        """Converts this asset to a dictionary."""
        d = {"href": self.href}
        d.update(super().to_dict())
        return d
