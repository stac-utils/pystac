from __future__ import annotations

import copy
import datetime as dt
import warnings
from typing import TYPE_CHECKING, Any, ClassVar, override

from typing_extensions import deprecated

from pystac.rel_type import RelType

from .asset import Asset, Assets
from .constants import DEFAULT_STAC_VERSION, STAC_OBJECT_TYPE
from .container import Container
from .geo_interface import GeoInterface
from .link import Link
from .stac_object import STACObject
from .utils import datetime_to_str, str_to_datetime

if TYPE_CHECKING:
    from .collection import Collection


class Item(STACObject, Assets):
    """The STAC Item object is the most important object in a STAC system.

    An Item is the entity that contains metadata for a scene and links to the
    assets. Item objects are the leaf nodes for a graph of Catalog and
    Collection objects.
    """

    type: ClassVar[STAC_OBJECT_TYPE] = "Feature"

    def __init__(
        self,
        id: str,
        geometry: dict[str, Any] | GeoInterface | None = None,
        bbox: list[float | int] | None = None,
        datetime: dt.datetime | str | None = None,
        properties: dict[str, Any] | Properties | None = None,
        type: str = "Feature",
        stac_version: str = DEFAULT_STAC_VERSION,
        stac_extensions: list[str] | None = None,
        links: list[Link] | list[dict[str, Any]] | None = None,
        assets: dict[str, Asset] | dict[str, dict[str, Any]] | None = None,
        collection: str | Collection | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            type=type,
            id=id,
            stac_version=stac_version,
            stac_extensions=stac_extensions,
            links=links,
            **kwargs,
        )

        if isinstance(geometry, GeoInterface):
            self.geometry: dict[str, Any] | None = copy.deepcopy(
                geometry.__geo_interface__
            )
        else:
            self.geometry = geometry

        # TODO add validation
        self.bbox: list[float | int] | None = list(bbox) if bbox else None

        self.properties: Properties = Properties.try_from(properties)
        if isinstance(datetime, dt.datetime):
            self.properties.datetime = datetime
        elif isinstance(datetime, str):
            self.properties.datetime = str_to_datetime(datetime)

        if assets:
            self.assets: dict[str, Asset] = {}
            for key, value in assets.items():
                asset = Asset.try_from(value)
                asset.set_owner(self)
                self.assets[key] = asset
        else:
            self.assets = {}

        self._collection: Collection | str | None = collection

    @override
    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        preserve_dict: bool = True,
        migrate: bool | None = None,
        root: Container | None = None,
    ) -> Item:
        if preserve_dict:
            data = copy.deepcopy(data)
        item = cls(**data)

        # TODO deprecate migrate
        if migrate:
            raise NotImplementedError
        if root:
            warnings.warn(
                "The root parameter is deprecated, call `set_root` directly after "
                "creating the item",
                DeprecationWarning,
            )
            item.set_root(root)
        return item

    @property
    def datetime(self) -> dt.datetime | None:
        return self.properties.datetime

    @deprecated("Get the datetime from the asset directly")
    def get_datetime(self, asset: Asset | None = None) -> dt.datetime | None:
        if asset and (datetime := asset.extra_fields.get("datetime")):
            return str_to_datetime(datetime)
        else:
            return self.datetime

    @deprecated("Set the datetime on the asset directly")
    def set_datetime(self, datetime: dt.datetime, asset: Asset | None = None) -> None:
        if asset:
            asset.extra_fields["datetime"] = datetime_to_str(datetime)
        else:
            self.properties.datetime = datetime

    @override
    def set_self_href(self, href: str | None) -> None:
        Asset.update_hrefs(self.assets, self.get_self_href(), href)
        return super().set_self_href(href)

    def get_collection(self) -> Collection | None:
        from .collection import Collection

        if isinstance(self._collection, Collection):
            return self._collection
        elif self._collection is None and (
            collection_link := self.get_link(RelType.COLLECTION)
        ):
            # TODO can we just make get_target just take a STACObject?
            stac_object = collection_link.get_target(self.get_self_href(), self.reader)
            if isinstance(stac_object, Collection):
                if root := self.get_root():
                    stac_object.set_root(root)
                self._collection = stac_object
                return stac_object
            else:
                return None
        else:
            return None

    @property
    @deprecated("Use get_collection")
    def collection(self) -> Collection | None:
        return self.get_collection()

    @property
    def collection_id(self) -> str | None:
        from .collection import Collection

        if isinstance(self._collection, Collection):
            return self._collection.id
        elif isinstance(self._collection, str):
            return self._collection
        else:
            return None

    def set_collection(self, collection: Collection | str | None) -> None:
        self._collection = collection
        self.remove_links("collection")

    @override
    def to_dict(
        self,
        include_self_link: bool = True,
        transform_hrefs: bool | None = None,
        order_keys: bool = True,
    ) -> dict[str, Any]:
        data = super().to_dict(
            include_self_link=include_self_link, transform_hrefs=transform_hrefs
        )
        data.update(
            {
                "geometry": copy.deepcopy(self.geometry),
                "properties": self.properties.to_dict(),
                "assets": {key: asset.to_dict() for key, asset in self.assets.items()},
            }
        )
        if self.bbox:
            data["bbox"] = self.bbox
        if self.collection_id:
            data["collection"] = self.collection_id
        if order_keys:
            ordered_data: dict[str, Any] = {}
            for key in (
                "type",
                "stac_version",
                "stac_extensions",
                "id",
                "geometry",
                "bbox",
                "properties",
                "links",
                "assets",
                "collection",
            ):
                if key in data:
                    ordered_data[key] = data.pop(key)
            ordered_data.update(data)
            return ordered_data
        else:
            return data

    @property
    def __geo_interface__(self) -> dict[str, Any]:
        return self.to_dict(include_self_link=False)


class Properties:
    def __init__(self, datetime: dt.datetime | str | None = None, **kwargs: Any):
        if isinstance(datetime, str):
            self.datetime: dt.datetime | None = str_to_datetime(datetime)
        elif isinstance(datetime, dt.datetime):
            self.datetime = datetime
        else:
            # TODO check for start and end datetime
            self.datetime = dt.datetime.now(tz=dt.UTC)

        self.extra_fields: dict[str, Any] = kwargs

    def __getitem__(self, key: str) -> Any:
        return self.extra_fields[key]

    def __getattr__(self, key: str) -> Any:
        return self.extra_fields[key]

    def __contains__(self, key: str) -> bool:
        return key == "datetime" or key in self.extra_fields

    @classmethod
    def try_from(
        cls,
        data: Properties | dict[str, Any] | None,
    ) -> Properties:
        if isinstance(data, Properties):
            return data
        elif not data:
            return Properties()
        else:
            return Properties.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Properties:
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        data = copy.deepcopy(self.extra_fields)
        data["datetime"] = datetime_to_str(self.datetime) if self.datetime else None
        return data
