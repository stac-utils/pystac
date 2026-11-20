from datetime import datetime
from typing import Any

from pystac import Collection, Extent, Item, SpatialExtent, TemporalExtent
from pystac.utils import get_opt

from ._base import Bench

NUM_BANDS = 13


def _band(i: int) -> dict[str, Any]:
    return {
        "name": f"B{i:02}",
        "data_type": "uint16",
        "nodata": 0,
        "statistics": {"minimum": 0, "maximum": 10000, "mean": 2000.0},
        "raster:histogram": {
            "count": 256,
            "min": 0,
            "max": 10000,
            "buckets": list(range(256)),
        },
    }


def _item_dict() -> dict[str, Any]:
    return {
        "type": "Feature",
        "stac_version": "1.1.0",
        "stac_extensions": [],
        "id": "item",
        "geometry": None,
        "properties": {
            "datetime": "2020-01-01T00:00:00Z",
            "bands": [_band(i) for i in range(NUM_BANDS)],
        },
        "links": [],
        "assets": {
            f"B{i:02}": {"href": f"B{i:02}.tif", "bands": [_band(i)]}
            for i in range(NUM_BANDS)
        },
    }


def _collection_dict() -> dict[str, Any]:
    collection = Collection(
        id="collection",
        description="Collection with bands in its item asset definitions",
        extent=Extent(
            SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
            TemporalExtent([[datetime(2020, 1, 1), None]]),
        ),
    )
    collection.extra_fields["item_assets"] = {
        f"B{i:02}": {"type": "image/tiff", "bands": [_band(i)]}
        for i in range(NUM_BANDS)
    }
    return collection.to_dict(include_self_link=False)


class BandsBench(Bench):
    """Objects with bands that are only accessed as dictionaries."""

    def setup(self) -> None:
        self.item_dict = _item_dict()
        self.item = Item.from_dict(self.item_dict)
        self.collection_dict = _collection_dict()
        self.collection = Collection.from_dict(self.collection_dict)
        _ = self.collection.item_assets

    def time_item_from_dict(self) -> None:
        Item.from_dict(self.item_dict)

    def time_item_to_dict(self) -> None:
        self.item.to_dict(include_self_link=False)

    def time_item_properties(self) -> None:
        _ = self.item.properties

    def time_collection_from_dict(self) -> None:
        Collection.from_dict(self.collection_dict)

    def time_collection_to_dict(self) -> None:
        self.collection.to_dict(include_self_link=False)


class ReadBandsBench(Bench):
    """Objects whose bands were read as :class:`~pystac.Band` objects."""

    def setup(self) -> None:
        if not hasattr(Item, "bands"):
            raise NotImplementedError("Bands are not supported")
        self.item = Item.from_dict(_item_dict())
        _ = self.item.bands
        for asset in self.item.assets.values():
            _ = asset.bands
        self.collection = Collection.from_dict(_collection_dict())
        for item_asset in self.collection.item_assets.values():
            _ = item_asset.bands
        self.band = get_opt(self.item.assets["B00"].bands)[0]

    def time_item_to_dict(self) -> None:
        self.item.to_dict(include_self_link=False)

    def time_item_properties(self) -> None:
        _ = self.item.properties

    def time_collection_to_dict(self) -> None:
        self.collection.to_dict(include_self_link=False)

    def time_edit_band_and_item_to_dict(self) -> None:
        self.band.unit = "m" if self.band.unit != "m" else "cm"
        self.item.to_dict(include_self_link=False)
