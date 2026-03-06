from __future__ import annotations

import copy
import datetime as dt
from typing import Any, ClassVar, TypedDict, cast, override

from typing_extensions import deprecated

from .asset import Asset, Assets, ItemAsset
from .band import Band
from .constants import DEFAULT_LICENSE, DEFAULT_STAC_VERSION, STAC_OBJECT_TYPE
from .container import Container
from .link import Link
from .provider import Provider
from .utils import datetime_to_str

SpatialExtentBboxType = list[float | int] | list[list[float | int]]
TemporalExtentIntervalType = (
    list[dt.datetime | str | None] | list[list[dt.datetime | str | None]]
)


class SpatialExtentDict(TypedDict):
    bbox: SpatialExtentBboxType


class TemporalExtentDict(TypedDict):
    interval: TemporalExtentIntervalType


class Collection(Container, Assets):
    type: ClassVar[STAC_OBJECT_TYPE] = "Collection"

    def __init__(
        self,
        id: str,
        description: str,
        extent: dict[str, Any] | Extent | None = None,
        type: str = "Collection",
        title: str | None = None,
        keywords: list[str] | None = None,
        license: str = DEFAULT_LICENSE,
        providers: list[Provider | dict[str, Any]] | None = None,
        summaries: dict[str, Any] | None = None,
        assets: dict[str, Asset | dict[str, Any]] | None = None,
        item_assets: dict[str, ItemAsset] | None = None,
        stac_version: str = DEFAULT_STAC_VERSION,
        stac_extensions: list[str] | None = None,
        links: list[Link] | list[dict[str, Any]] | None = None,
        bands: list[Band] | list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(type, id, stac_version, stac_extensions, links, **kwargs)
        self.description: str = description
        self.title: str | None = title
        self.keywords: list[str] | None = keywords
        self.license: str = license
        self.providers: list[Provider] | None = (
            [Provider.try_from(provider) for provider in providers]
            if providers is not None
            else None
        )
        if bands is not None:
            self.bands: list[Band] | None = [Band.try_from(band) for band in bands]
        else:
            self.bands = None
        self.extent: Extent = Extent.try_from(extent)
        self.summaries: dict[str, Any] | None = summaries
        self.assets: dict[str, Asset] = (
            {key: Asset.try_from(value) for (key, value) in assets.items()}
            if assets is not None
            else {}
        )
        self.item_assets: dict[str, ItemAsset] | None = (
            {key: ItemAsset.try_from(value) for (key, value) in item_assets.items()}
            if item_assets is not None
            else None
        )

    @override
    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        preserve_dict: bool = True,
        migrate: bool | None = None,
        root: Container | None = None,
    ) -> Collection:
        if preserve_dict:
            data = copy.deepcopy(data)
        return Collection(**data)

    @override
    def set_self_href(self, href: str | None) -> None:
        if self.assets:
            Asset.update_hrefs(self.assets, self.get_self_href(), href)
        return super().set_self_href(href)

    @override
    def to_dict(
        self, include_self_link: bool = True, transform_hrefs: bool | None = None
    ) -> dict[str, Any]:
        data = super().to_dict(
            include_self_link=include_self_link, transform_hrefs=transform_hrefs
        )
        data["description"] = self.description
        if self.title:
            data["title"] = self.title
        if self.keywords:
            data["keywords"] = self.keywords
        data["license"] = self.license
        if self.providers:
            data["providers"] = [provider.to_dict() for provider in self.providers]
        data["extent"] = self.extent.to_dict()
        if self.summaries:
            data["summaries"] = self.summaries
        if self.bands is not None:
            data["bands"] = [band.to_dict() for band in self.bands]
        if self.assets:
            data["assets"] = {
                key: asset.to_dict() for key, asset in self.assets.items()
            }
        if self.item_assets:
            data["item_assets"] = {
                key: item_asset.to_dict()
                for key, item_asset in self.item_assets.items()
            }
        return data


class Extent:
    def __init__(
        self,
        spatial: SpatialExtent | SpatialExtentDict | None = None,
        temporal: TemporalExtent | TemporalExtentDict | None = None,
    ):
        self.spatial: SpatialExtent = SpatialExtent.try_from(spatial)
        self.temporal: TemporalExtent = TemporalExtent.try_from(temporal)

    @classmethod
    def try_from(cls, extent: Extent | dict[str, Any] | None) -> Extent:
        if isinstance(extent, Extent):
            return extent
        elif isinstance(extent, dict):
            return Extent.from_dict(extent)
        else:
            return Extent()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Extent:
        return Extent(**data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "spatial": self.spatial.to_dict(),
            "temporal": self.temporal.to_dict(),
        }


class TemporalExtent:
    def __init__(self, interval: list[list[str | None]] | None = None) -> None:
        self.interval: list[list[str | None]] = interval or [
            [datetime_to_str(dt.datetime.now()), None]
        ]

    @classmethod
    def try_from(
        cls,
        data: TemporalExtent | TemporalExtentDict | None,
    ) -> TemporalExtent:
        if isinstance(data, TemporalExtent):
            return data
        elif not data:
            return TemporalExtent()
        elif isinstance(data["interval"][0], list):
            return TemporalExtent(
                [
                    to_interval(cast(list[dt.datetime | str | None], interval))
                    for interval in data["interval"]
                ]
            )
        else:
            return TemporalExtent(
                [to_interval(cast(list[dt.datetime | str | None], data["interval"]))]
            )

    @classmethod
    @deprecated("Use default initializer instead")
    def from_now(cls) -> TemporalExtent:
        return TemporalExtent()

    def to_dict(self) -> dict[str, Any]:
        return {"interval": self.interval}


class SpatialExtent:
    def __init__(self, bbox: list[list[float | int]] | None = None) -> None:
        self.bbox: list[list[float | int]] = bbox or [[-180, -90, 180, 90]]

    @classmethod
    def try_from(
        cls,
        data: SpatialExtent | SpatialExtentDict | None,
    ) -> SpatialExtent:
        if isinstance(data, SpatialExtent):
            return data
        elif not data:
            return SpatialExtent()
        elif isinstance(data["bbox"][0], list):
            return SpatialExtent(cast(list[list[float | int]], data["bbox"]))
        else:
            return SpatialExtent([cast(list[float | int], data["bbox"])])

    @classmethod
    @deprecated("Use try_from instead")
    def from_coordinates(cls, coordinates: Any) -> SpatialExtent:
        return SpatialExtent.try_from({"bbox": coordinates})

    def to_dict(self) -> dict[str, Any]:
        return {"bbox": self.bbox}


def to_interval(interval: list[dt.datetime | str | None]) -> list[str | None]:
    if len(interval) != 2:
        raise ValueError("Interval must have exactly two elements")
    return [to_datetime_str(interval[0]), to_datetime_str(interval[1])]


def to_datetime_str(datetime: dt.datetime | str | None) -> str | None:
    if datetime is None:
        return None
    elif isinstance(datetime, str):
        return datetime
    else:
        return datetime_to_str(datetime)
