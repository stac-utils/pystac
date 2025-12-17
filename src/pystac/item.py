from __future__ import annotations

import copy
import datetime as dt
import warnings
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from typing_extensions import override

from . import utils
from .asset import Asset
from .constants import COLLECTION, ITEM_TYPE
from .errors import STACWarning
from .link import Link
from .stac_object import STACObject

if TYPE_CHECKING:
    from .collection import Collection


class Item(STACObject):
    """An Item is a GeoJSON Feature augmented with foreign members relevant to a
    STAC object.

    These include fields that identify the time range and assets of the Item.
    An Item is the core object in a STAC Catalog, containing the core metadata
    that enables any client to search or crawl online catalogs of spatial
    'assets' (e.g., satellite imagery, derived data, DEMs)."""

    @classmethod
    @override
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
        self.geometry: dict[str, Any] | None = geometry
        if self.geometry is None and bbox:
            warnings.warn(
                "bbox cannot be set if geometry is None. Setting bbox to None",
                STACWarning,
            )
            self.bbox: Sequence[float | int] | None = None
        else:
            self.bbox = bbox

        self.properties: dict[str, Any] = properties or {}

        self.datetime: dt.datetime | None = None
        self.start_datetime: dt.datetime | None = None
        self.end_datetime: dt.datetime | None = None
        if datetime is None:
            if properties_datetime := self.properties.get("datetime", None):
                self.datetime = utils.str_to_datetime(properties_datetime)
            if properties_start_datetime := self.properties.get("start_datetime", None):
                self.start_datetime = utils.str_to_datetime(properties_start_datetime)
            if properties_end_datetime := self.properties.get("end_datetime", None):
                self.end_datetime = utils.str_to_datetime(properties_end_datetime)
            if (
                self.datetime is None
                and self.start_datetime is None
                and self.end_datetime is None
            ):
                self.datetime = dt.datetime.now(tz=dt.UTC)
        elif isinstance(datetime, dt.datetime):
            self.datetime = datetime
            self.start_datetime = None
            self.end_datetime = None
        elif isinstance(datetime, tuple):
            self.datetime = None
            self.start_datetime = _parse_datetime(datetime[0])
            self.end_datetime = _parse_datetime(datetime[1])

        self.collection_id: str | None = collection

        super().__init__(
            id=id,
            stac_version=stac_version,
            stac_extensions=stac_extensions,
            links=links,
            assets=assets,
            **kwargs,
        )

    @override
    def get_fields(self) -> dict[str, Any]:
        return self.properties

    def set_collection(self, collection: Collection | None) -> None:
        if collection:
            self.collection_id = collection.id
            self.set_link(Link.collection(collection))
        else:
            self.collection_id = None
            self.remove_links(COLLECTION)

    def get_collection(self) -> Collection | None:
        from .collection import Collection

        if link := self.get_link(COLLECTION):
            stac_object = link.get_stac_object()
            if isinstance(stac_object, Collection):
                return stac_object
            else:
                return None
        else:
            return None

    @override
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

        if self.datetime is None:
            d["properties"]["datetime"] = None
        else:
            d["properties"]["datetime"] = utils.datetime_to_str(self.datetime)
        if self.start_datetime:
            d["properties"]["start_datetime"] = utils.datetime_to_str(
                self.start_datetime
            )
        if self.end_datetime:
            d["properties"]["end_datetime"] = utils.datetime_to_str(self.end_datetime)

        d["links"] = [link.to_dict() for link in self.iter_links()]
        d["assets"] = dict((key, asset.to_dict()) for key, asset in self.assets.items())
        if self.collection_id is not None:
            d["collection"] = self.collection_id
        d.update(copy.deepcopy(self.extra_fields))
        return d


def _parse_datetime(value: str | dt.datetime | None) -> dt.datetime | None:
    if value is None or isinstance(value, dt.datetime):
        return value
    else:
        return utils.str_to_datetime(value)
