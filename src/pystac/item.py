from __future__ import annotations

import copy
import datetime as dt
import warnings
from typing import Any, Sequence

from .asset import Asset, AssetsMixin
from .constants import ITEM_TYPE
from .errors import StacWarning
from .link import Link
from .stac_object import STACObject


class Item(STACObject, AssetsMixin):
    """An Item is a GeoJSON Feature augmented with foreign members relevant to a
    STAC object.

    These include fields that identify the time range and assets of the Item.
    An Item is the core object in a STAC Catalog, containing the core metadata
    that enables any client to search or crawl online catalogs of spatial
    'assets' (e.g., satellite imagery, derived data, DEMs)."""

    @classmethod
    def get_type(cls: type[Item]) -> str:
        return ITEM_TYPE

    def __init__(
        self,
        id: str,
        geometry: dict[str, Any] | None = None,
        bbox: Sequence[float | int] | None = None,
        datetime: dt.datetime
        | tuple[dt.datetime | None, dt.datetime | None]
        | str
        | tuple[str | None, str | None]
        | None = None,
        properties: dict[str, Any] | None = None,
        assets: dict[str, Asset | dict[str, Any]] | None = None,
        collection: str | None = None,
        stac_version: str | None = None,
        stac_extensions: list[str] | None = None,
        links: list[Link | dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        """Creates a new item.

        Args:
            id: The item id
            geometry: The item geometry
            bbox: The item bbox. Will be automatically set to None, with a
                warning, if the geometry is none.
            datetime: The item datetime, or start and end datetimes, as a string
                or as a datetime object.
        """
        self.geometry = geometry
        if self.geometry is None and bbox:
            warnings.warn(
                "bbox cannot be set if geometry is None. Setting bbox to None",
                StacWarning,
            )
            self.bbox = None
        else:
            self.bbox = bbox
        if properties is None:
            properties = {}

        # TODO test this out better
        if isinstance(datetime, dt.datetime):
            properties["datetime"] = datetime.isoformat()
        elif isinstance(datetime, tuple):
            properties["datetime"] = None
            for key, value in (
                ("start_datetime", datetime[0]),
                ("end_datetime", datetime[1]),
            ):
                if value is None or isinstance(value, str):
                    properties[key] = value
                else:
                    properties[key] = value.isoformat
        self.properties = properties
        if not any(
            key in self.properties
            for key in ("datetime", "start_datetime", "end_datetime")
        ):
            self.properties["datetime"] = dt.datetime.now(
                tz=dt.timezone.utc
            ).isoformat()

        if assets is None:
            self.assets = dict()
        else:
            self.assets = dict(
                (key, asset if isinstance(asset, Asset) else Asset.from_dict(asset))
                for key, asset in assets.items()
            )

        self.collection = collection

        super().__init__(id, stac_version, stac_extensions, links, **kwargs)

    def get_fields(self) -> dict[str, Any]:
        return self.properties

    def _to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "type": self.get_type(),
            "stac_version": self.stac_version,
        }
        if self.stac_extensions is not None:
            d["stac_extensions"] = self.stac_extensions
        d["id"] = self.id
        d["geometry"] = self.geometry
        if self.bbox is not None:
            d["bbox"] = self.bbox
        d["properties"] = copy.deepcopy(self.properties)
        d["links"] = [link.to_dict() for link in self.iter_links()]
        d["assets"] = dict((key, asset.to_dict()) for key, asset in self.assets.items())
        if self.collection is not None:
            d["collection"] = self.collection
        d.update(copy.deepcopy(self.extra_fields))
        return d
