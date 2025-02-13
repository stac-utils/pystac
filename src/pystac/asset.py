from __future__ import annotations

import copy
from typing import Any

from typing_extensions import Self


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
        self.title = title
        self.description = description
        self.type = type
        self.roles = roles
        self.extra_fields = kwargs

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


class Asset(ItemAsset):
    """An asset, e.g. a geospatial data file."""

    @classmethod
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
        self.href = href
        super().__init__(
            title=title, description=description, type=type, roles=roles, **kwargs
        )

    def to_dict(self) -> dict[str, Any]:
        """Converts this asset to a dictionary."""
        d = {"href": self.href}
        d.update(super().to_dict())
        return d
