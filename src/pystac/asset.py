from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any, Protocol, override

from typing_extensions import deprecated

from .common import DataValue, Instrument
from .media_type import MediaType
from .utils import is_absolute_href, make_absolute_href, make_relative_href
from .writer import Writer

if TYPE_CHECKING:
    from .stac_object import STACObject


class ItemAsset(DataValue, Instrument):
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
        data: dict[str, Any] = copy.deepcopy(self.extra_fields)
        data["title"] = self.title
        data["description"] = self.description
        data["type"] = self.type
        data["roles"] = self.roles
        data["statistics"] = self.statistics.to_dict() or None
        return {k: v for k, v in data.items() if v is not None}


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

        self._owner: STACObject | None = None

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

    @property
    def owner(self) -> STACObject | None:
        return self._owner

    def set_owner(self, owner: STACObject | None) -> None:
        self._owner = owner

    def get_absolute_href(self) -> str | None:
        if is_absolute_href(self.href):
            return self.href
        elif self._owner and (owner_href := self._owner.get_self_href()):
            return make_absolute_href(self.href, owner_href, False)
        else:
            return None

    @override
    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        return {"href": self.href, **data}


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
        if self.get_self_href():
            # TODO actually implement
            pass
        else:
            raise ValueError(
                "Cannot make asset hrefs relative, item does not have a self href"
            )

    # TODO do we want to deprecate this? I think so...
    def delete_asset(self, key: str) -> None:
        asset = self.assets[key]
        try:
            self.writer.delete(make_absolute_href(asset.href, self.get_self_href()))
        except Exception as e:
            raise ValueError(f"Cannot delete file {asset.href}: {e}")
        del self.assets[key]
