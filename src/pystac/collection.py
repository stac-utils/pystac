from __future__ import annotations

import copy
import datetime as dt
import warnings
from collections.abc import Iterable
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Self,
    TypedDict,
    cast,
    override,
)

from typing_extensions import deprecated

from .asset import Asset, Assets, ItemAsset
from .band import Band
from .constants import DEFAULT_LICENSE, DEFAULT_STAC_VERSION, STAC_OBJECT_TYPE
from .container import Container
from .link import Link
from .provider import Provider
from .summaries import Summaries
from .utils import to_datetime_str

if TYPE_CHECKING:
    from .item import Item
    from .item_collection import ItemCollection

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
        summaries: Summaries | dict[str, Any] | None = None,
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

        if extent is None:
            warnings.warn(
                "Collection is missing extent, setting default spatial and "
                "temporal extents"
            )
        self.extent: Extent = Extent.try_from(extent)
        self.summaries: Summaries = Summaries.try_from(summaries)

        self.assets: dict[str, Asset] = {}
        if assets is not None:
            for key, value in assets.items():
                asset = Asset.try_from(value)
                asset.set_owner(self)
                self.assets[key] = asset

        self.item_assets: dict[str, ItemAsset] | None = (
            {key: ItemAsset.try_from(value) for (key, value) in item_assets.items()}
            if item_assets is not None
            else None
        )

    @override
    @classmethod
    def from_dict[T: Collection](
        cls: type[T],
        data: dict[str, Any],
        preserve_dict: bool = True,
        migrate: bool | None = None,
        root: Container | None = None,
    ) -> T:
        if preserve_dict:
            data = copy.deepcopy(data)
        return cls(**data)

    @classmethod
    def from_items[T: Collection](
        cls: type[T],
        items: Iterable[Item] | ItemCollection,
        *,
        id: str | None = None,
    ) -> T:
        """Create a :class:`Collection` from iterable of items or an
        :class:`~pystac.ItemCollection`.

        Will try to pull collection attributes from
        :attr:`~pystac.ItemCollection.extra_fields` and items when possible.

        Args:
            items : Iterable of :class:`~pystac.Item` instances to include in the
                :class:`Collection`. This can be a :class:`~pystac.ItemCollection`.
            id : Identifier for the collection. If not set, must be available on the
                items and they must all match.
        """
        from .item_collection import ItemCollection

        if id is None:
            values = {item.collection_id for item in items}
            if len(values) == 1:
                id = next(iter(values))
        if id is None:
            raise ValueError(
                "Collection id must be defined. Either by specifying collection_id "
                "on every item, or as a keyword argument to this function."
            )

        kwargs: dict[str, Any] = {}
        if isinstance(items, ItemCollection):
            kwargs = copy.deepcopy(items.extra_fields)

        if "description" not in kwargs:
            values = {item.properties.description for item in items}
            if len(values) == 1:
                kwargs["description"] = next(iter(values))

        if "title" not in kwargs:
            values = {item.properties.title for item in items}
            if len(values) == 1:
                kwargs["title"] = next(iter(values))

        collection = cls(
            id=id,
            description=kwargs.pop("description"),
            extent=Extent.from_items(items),
            **kwargs,
        )

        _ = collection.add_items(items)

        return collection

    @property
    @deprecated("use .type instead")
    def STAC_OBJECT_TYPE(self) -> STAC_OBJECT_TYPE:
        return self.type

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
            data["summaries"] = self.summaries.to_dict()
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

    def update_extent_from_items(self) -> None:
        """
        Update datetime and bbox based on all items to a single bbox and time window.
        """
        self.extent = Extent.from_items(self.get_items(recursive=True))


class Extent:
    def __init__(
        self,
        spatial: SpatialExtent | SpatialExtentDict | None = None,
        temporal: TemporalExtent | TemporalExtentDict | None = None,
        **kwargs: Any,
    ):
        self.spatial: SpatialExtent = SpatialExtent.try_from(spatial)
        self.temporal: TemporalExtent = TemporalExtent.try_from(temporal)
        self.extra_fields: dict[str, Any] = kwargs

    @classmethod
    def try_from(cls, extent: Extent | dict[str, Any] | None) -> Extent:
        if isinstance(extent, Extent):
            return extent
        elif isinstance(extent, dict):
            return Extent.from_dict(extent)
        else:
            return Extent()

    @classmethod
    def from_dict[T: Extent](cls: type[T], data: dict[str, Any]) -> T:
        return cls(**data)

    @classmethod
    def from_items(cls: type[Self], items: Iterable[Item]) -> Extent:
        """Create an Extent based on the datetimes and bboxes of a list of items.

        Args:
            items : A list of items to derive the extent from.

        Returns:
            Extent: An Extent that spatially and temporally covers all of the
            given items.
        """
        bounds_values: list[list[float]] = [
            [float("inf")],
            [float("inf")],
            [float("-inf")],
            [float("-inf")],
        ]
        datetimes: list[dt.datetime] = []
        starts: list[dt.datetime] = []
        ends: list[dt.datetime] = []

        for item in items:
            if item.bbox is not None:
                for i in range(0, 4):
                    bounds_values[i].append(item.bbox[i])
            if item.datetime is not None:
                datetimes.append(item.datetime)
            if item.properties.start_datetime is not None:
                starts.append(item.properties.start_datetime)
            if item.properties.end_datetime is not None:
                ends.append(item.properties.end_datetime)

        if not any(datetimes + starts):
            start_timestamp = None
        else:
            start_timestamp = min(
                [
                    d if d.tzinfo else d.replace(tzinfo=dt.UTC)
                    for d in datetimes + starts
                ]
            )
        if not any(datetimes + ends):
            end_timestamp = None
        else:
            end_timestamp = max(
                [d if d.tzinfo else d.replace(tzinfo=dt.UTC) for d in datetimes + ends]
            )

        spatial = SpatialExtent(
            [
                [
                    min(bounds_values[0]),
                    min(bounds_values[1]),
                    max(bounds_values[2]),
                    max(bounds_values[3]),
                ]
            ]
        )
        temporal = TemporalExtent(
            [
                [
                    to_datetime_str(start_timestamp),
                    to_datetime_str(end_timestamp),
                ]
            ]
        )

        return Extent(spatial=spatial, temporal=temporal)

    def clone[T: Extent](self: T) -> T:
        return self.from_dict(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        data = copy.deepcopy(self.extra_fields)
        return {
            "spatial": self.spatial.to_dict(),
            "temporal": self.temporal.to_dict(),
            **data,
        }


class TemporalExtent:
    def __init__(
        self,
        interval: TemporalExtentIntervalType | str | dt.datetime | None = None,
        **kwargs: Any,
    ) -> None:
        if interval is None and "intervals" in kwargs:
            warnings.warn(
                "intervals is deprecated and will be removed in a future version. "
                "Use interval instead",
                FutureWarning,
            )
            interval = kwargs.pop("intervals")

        self.interval: list[list[str | None]]
        if interval is None:
            self.interval = [[None, None]]
        elif isinstance(interval, (str, dt.datetime)):
            self.interval = [to_interval([interval, None])]
        elif isinstance(interval[0], list):
            self.interval = [
                to_interval(cast(list[dt.datetime | str | None], dates))
                for dates in interval
            ]
        else:
            self.interval = [
                to_interval(cast(list[dt.datetime | str | None], interval))
            ]

        self.extra_fields: dict[str, Any] = kwargs

    @classmethod
    def try_from(
        cls,
        data: TemporalExtent | TemporalExtentDict | None,
    ) -> TemporalExtent:
        if isinstance(data, TemporalExtent):
            return data
        elif not data:
            return TemporalExtent()
        else:
            return TemporalExtent(**data)

    @property
    @deprecated("Use interval instead")
    def intervals(self) -> list[list[str | None]]:
        return self.interval

    @classmethod
    @deprecated("Use `TemporalExtent(dt.datetime.now())` instead")
    def from_now(cls) -> TemporalExtent:
        return TemporalExtent(interval=dt.datetime.now())

    def to_dict(self) -> dict[str, Any]:
        data = copy.deepcopy(self.extra_fields)
        return {"interval": self.interval, **data}


class SpatialExtent:
    def __init__(
        self, bbox: SpatialExtentBboxType | None = None, **kwargs: Any
    ) -> None:
        if bbox is None and "bboxes" in kwargs:
            warnings.warn(
                "bboxes is deprecated and will be removed in a future version. "
                "Use bbox instead",
                FutureWarning,
            )
            bbox = kwargs.pop("bboxes")

        self.bbox: list[list[float | int]]
        if bbox is None:
            self.bbox = [[-180, -90, 180, 90]]
        elif isinstance(bbox[0], list):
            self.bbox = cast(list[list[float | int]], bbox)
        else:
            self.bbox = [cast(list[float | int], bbox)]
        self.extra_fields: dict[str, Any] = kwargs

    @classmethod
    def try_from(
        cls,
        data: SpatialExtent | SpatialExtentDict | None,
    ) -> SpatialExtent:
        if isinstance(data, SpatialExtent):
            return data
        elif not data:
            return SpatialExtent()
        else:
            return SpatialExtent(**data)

    @property
    @deprecated("Use bbox instead")
    def bboxes(self) -> list[list[float | int]]:
        return self.bbox

    def to_dict(self) -> dict[str, Any]:
        data = copy.deepcopy(self.extra_fields)
        return {"bbox": self.bbox, **data}


def to_interval(interval: list[dt.datetime | str | None]) -> list[str | None]:
    if len(interval) != 2:
        raise ValueError("Interval must have exactly two elements")
    return [to_datetime_str(interval[0]), to_datetime_str(interval[1])]
