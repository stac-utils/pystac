from __future__ import annotations

import copy
import os
import shutil
from typing import TYPE_CHECKING, Any, Protocol, override

from typing_extensions import deprecated

from .media_type import MediaType
from .utils import (
    get_absolute_href,
    is_absolute_href,
    make_absolute_href,
    make_relative_href,
)
from .writer import Writer

if TYPE_CHECKING:
    from .stac_object import STACObject


class ItemAsset:
    def __init__(
        self,
        title: str | None = None,
        description: str | None = None,
        type: str | None = None,
        roles: list[str] | None = None,
        **kwargs: Any,
    ):
        self.title: str | None = title
        self.description: str | None = description
        self.type: str | None = type
        self.roles: list[str] | None = roles
        self.extra_fields: dict[str, Any] = kwargs

    @classmethod
    def try_from[T: ItemAsset](cls: type[T], data: T | dict[str, Any]) -> T:
        if isinstance(data, cls):
            return data
        elif isinstance(data, dict):
            return cls.from_dict(data)
        else:
            raise ValueError(f"Invalid data type for item asset: {type(data)}")

    @classmethod
    def from_dict[T: ItemAsset](cls: type[T], data: dict[str, Any]) -> T:
        return cls(**data)

    def clone[T: ItemAsset](self: T) -> T:
        return self.from_dict(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        data = copy.deepcopy(self.extra_fields)
        if self.title is not None:
            data["title"] = self.title
        if self.description is not None:
            data["description"] = self.description
        if self.type is not None:
            data["type"] = self.type
        if self.roles is not None:
            data["roles"] = self.roles
        return data


class Asset(ItemAsset):
    def __init__(
        self,
        href: str,
        title: str | None = None,
        description: str | None = None,
        type: str | None = None,
        roles: list[str] | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            title=title, description=description, type=type, roles=roles, **kwargs
        )
        self.href: str = href

        self.owner: STACObject | None = None

    @staticmethod
    def update_hrefs(
        assets: dict[str, Asset], start_href: str | None, end_href: str | None
    ) -> None:
        if start_href and end_href:
            for asset in assets.values():
                if not is_absolute_href(asset.href):
                    asset.href = make_relative_href(
                        make_absolute_href(asset.href, start_href), end_href
                    )

    def set_owner(self, owner: STACObject | None) -> None:
        self.owner = owner

    def get_absolute_href(self) -> str | None:
        owner_href = self.owner.get_self_href() if self.owner else None
        return get_absolute_href(self.href, owner_href)

    @override
    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["href"] = self.href
        return data

    def move(self, href: str) -> Asset:
        owner_href = self.owner.get_self_href() if self.owner else None
        src = get_absolute_href(self.href, owner_href)
        dst = get_absolute_href(href, owner_href)
        if src is None or dst is None:
            raise ValueError(
                f"Cannot move file if source ('{self.href}') or destination "
                f"('{href}') is relative and owner is not set."
            )

        _ = shutil.move(src, dst)
        self.href = href
        return self

    def copy(self, href: str) -> Asset:
        owner_href = self.owner.get_self_href() if self.owner else None
        src = get_absolute_href(self.href, owner_href)
        dst = get_absolute_href(href, owner_href)
        if src is None or dst is None:
            raise ValueError(
                f"Cannot copy file if source ('{self.href}') or destination "
                f"('{href}') is relative and owner is not set."
            )
        _ = shutil.copy2(src, dst)
        self.href = href
        return self

    def delete(self) -> None:
        href = self.get_absolute_href()
        if href is None:
            raise ValueError(
                f"Cannot delete file if asset href ('{self.href}') is relative "
                "and owner is not set."
            )
        os.remove(href)


class Assets(Protocol):
    assets: dict[str, Asset]
    writer: Writer

    def get_self_href(self) -> str | None: ...

    def get_assets(
        self, media_type: MediaType | None = None, role: str | None = None
    ) -> dict[str, Asset]:
        return {
            key: copy.deepcopy(asset)
            for (key, asset) in self.assets.items()
            if (not media_type or asset.type == media_type)
            and (not role or (asset.roles and role in asset.roles))
        }

    @deprecated(
        "add_asset is deprecated, just add the asset directly to the assets dictionary"
    )
    def add_asset(self, key: str, asset: Asset) -> None:
        self.assets[key] = asset

    def make_asset_hrefs_relative(self) -> None:
        if owner_href := self.get_self_href():
            for asset in self.assets.values():
                if is_absolute_href(asset.href, owner_href):
                    asset.href = make_relative_href(asset.href, owner_href)
        else:
            raise ValueError(
                "Cannot make asset hrefs relative, item does not have a self href"
            )

    def make_asset_hrefs_absolute(self) -> None:
        if owner_href := self.get_self_href():
            for asset in self.assets.values():
                if not is_absolute_href(asset.href, owner_href):
                    asset.href = make_absolute_href(asset.href, owner_href)
        else:
            raise ValueError(
                "Cannot make asset hrefs absolute, item does not have a self href"
            )

    # TODO do we want to deprecate this? I think so...
    def delete_asset(self, key: str) -> None:
        asset = self.assets[key]
        try:
            self.writer.delete(make_absolute_href(asset.href, self.get_self_href()))
        except Exception as e:
            raise ValueError(f"Cannot delete file {asset.href}: {e}")
        del self.assets[key]
