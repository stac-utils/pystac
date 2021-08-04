from copy import copy, deepcopy
from datetime import datetime as Datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

import dateutil.parser

import pystac
from pystac import asset as asset_mod
from pystac import collection as collection_mod
from pystac import common_metadata, errors
from pystac import link as link_mod
from pystac import rel_type, stac_object, utils
from pystac.serialization import identify
from pystac.serialization import migrate as migrate_mod

if TYPE_CHECKING:
    from pystac.asset import Asset as Asset_Type
    from pystac.catalog import Catalog as Catalog_Type
    from pystac.collection import Collection as Collection_Type
    from pystac.stac_io import StacIO as StacIO_Type


class Item(stac_object.STACObject):
    """An Item is the core granular entity in a STAC, containing the core metadata
    that enables any client to search or crawl online catalogs of spatial 'assets' -
    satellite imagery, derived data, DEM's, etc.

    Args:
        id : Provider identifier. Must be unique within the STAC.
        geometry : Defines the full footprint of the asset represented by this
            item, formatted according to
            `RFC 7946, section 3.1 (GeoJSON) <https://tools.ietf.org/html/rfc7946>`_.
        bbox :  Bounding Box of the asset represented by this item
            using either 2D or 3D geometries. The length of the array must be 2*n
            where n is the number of dimensions. Could also be None in the case of a
            null geometry.
        datetime : Datetime associated with this item. If None,
            a start_datetime and end_datetime must be supplied in the properties.
        properties : A dictionary of additional metadata for the item.
        stac_extensions : Optional list of extensions the Item implements.
        href : Optional HREF for this item, which be set as the item's
            self link's HREF.
        collection : The Collection or Collection ID that this item
            belongs to.
        extra_fields : Extra fields that are part of the top-level JSON
            properties of the Item.

    Attributes:
        id : Provider identifier. Unique within the STAC.
        geometry : Defines the full footprint of the asset represented by this
            item, formatted according to
            `RFC 7946, section 3.1 (GeoJSON) <https://tools.ietf.org/html/rfc7946>`_.
        bbox :  Bounding Box of the asset represented by this item
            using either 2D or 3D geometries. The length of the array is 2*n where n
            is the number of dimensions. Could also be None in the case of a null
            geometry.
        datetime : Datetime associated with this item. If None,
            the start_datetime and end_datetime in the common_metadata
            will supply the datetime range of the Item.
        properties : A dictionary of additional metadata for the item.
        stac_extensions : Optional list of extensions the Item
            implements.
        collection : Collection that this item is a part of.
        links : A list of :class:`~pystac.Link` objects representing
            all links associated with this STACObject.
        assets : Dictionary of asset objects that can be downloaded,
            each with a unique key.
        collection_id : The Collection ID that this item belongs to, if
            any.
        extra_fields : Extra fields that are part of the top-level JSON
            properties of the Item.
    """

    STAC_OBJECT_TYPE = stac_object.STACObjectType.ITEM

    def __init__(
        self,
        id: str,
        geometry: Optional[Dict[str, Any]],
        bbox: Optional[List[float]],
        datetime: Optional[Datetime],
        properties: Dict[str, Any],
        stac_extensions: Optional[List[str]] = None,
        href: Optional[str] = None,
        collection: Optional[Union[str, "Collection_Type"]] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(stac_extensions or [])

        self.id = id
        self.geometry = geometry
        self.bbox = bbox
        self.properties = properties
        if extra_fields is None:
            self.extra_fields = {}
        else:
            self.extra_fields = extra_fields

        self.assets: Dict[str, "Asset_Type"] = {}

        self.datetime: Optional[Datetime] = None
        if datetime is None:
            if "start_datetime" not in properties or "end_datetime" not in properties:
                raise errors.STACError(
                    "Invalid Item: If datetime is None, "
                    "a start_datetime and end_datetime "
                    "must be supplied in "
                    "the properties."
                )
            self.datetime = None
        else:
            self.datetime = datetime

        if href is not None:
            self.set_self_href(href)

        self.collection_id: Optional[str] = None
        if collection is not None:
            if isinstance(collection, collection_mod.Collection):
                self.set_collection(collection)
            else:
                self.collection_id = collection

    def __repr__(self) -> str:
        return "<Item id={}>".format(self.id)

    def set_self_href(self, href: Optional[str]) -> None:
        """Sets the absolute HREF that is represented by the ``rel == 'self'``
        :class:`~pystac.Link`.

        Changing the self HREF of the item will ensure that all asset HREFs
        remain valid. If asset HREFs are relative, the HREFs will change
        to point to the same location based on the new item self HREF,
        either by making them relative to the new location or making them
        absolute links if the new location does not share the same protocol
        as the old location.

        Args:
            href : The absolute HREF of this object. If the given HREF
                is not absolute, it will be transformed to an absolute
                HREF based on the current working directory. If this is None
                the call will clear the self HREF link.
        """
        prev_href = self.get_self_href()
        super().set_self_href(href)
        new_href = self.get_self_href()  # May have been made absolute.

        if prev_href is not None and new_href is not None:
            # Make sure relative asset links remain valid.
            for asset in self.assets.values():
                asset_href = asset.href
                if not utils.is_absolute_href(asset_href):
                    abs_href = utils.make_absolute_href(asset_href, prev_href)
                    new_relative_href = utils.make_relative_href(abs_href, new_href)
                    asset.href = new_relative_href

    def get_datetime(self, asset: Optional["Asset_Type"] = None) -> Optional[Datetime]:
        """Gets an Item or an Asset datetime.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value.

        Returns:
            datetime or None
        """
        if asset is None or "datetime" not in asset.extra_fields:
            return self.datetime
        else:
            asset_dt = asset.extra_fields.get("datetime")
            if asset_dt is None:
                return None
            else:
                return utils.str_to_datetime(asset_dt)

    def set_datetime(
        self, datetime: Datetime, asset: Optional["Asset_Type"] = None
    ) -> None:
        """Set an Item or an Asset datetime.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.datetime = datetime
        else:
            asset.extra_fields["datetime"] = utils.datetime_to_str(datetime)

    def get_assets(self) -> Dict[str, "Asset_Type"]:
        """Get this item's assets.

        Returns:
            Dict[str, Asset]: A copy of the dictionary of this item's assets.
        """
        return dict(self.assets.items())

    def add_asset(self, key: str, asset: "Asset_Type") -> None:
        """Adds an Asset to this item.

        Args:
            key : The unique key of this asset.
            asset : The Asset to add.
        """
        asset.set_owner(self)
        self.assets[key] = asset

    def make_asset_hrefs_relative(self) -> "Item":
        """Modify each asset's HREF to be relative to this item's self HREF.

        Returns:
            Item: self
        """

        self_href = None
        for asset in self.assets.values():
            href = asset.href
            if utils.is_absolute_href(href):
                if self_href is None:
                    self_href = self.get_self_href()
                    if self_href is None:
                        raise errors.STACError(
                            "Cannot make asset HREFs relative "
                            "if no self_href is set."
                        )
                asset.href = utils.make_relative_href(asset.href, self_href)
        return self

    def make_asset_hrefs_absolute(self) -> "Item":
        """Modify each asset's HREF to be absolute.

        Any asset HREFs that are relative will be modified to absolute based on this
        item's self HREF.

        Returns:
            Item: self
        """
        self_href = None
        for asset in self.assets.values():
            href = asset.href
            if not utils.is_absolute_href(href):
                if self_href is None:
                    self_href = self.get_self_href()
                    if self_href is None:
                        raise errors.STACError(
                            "Cannot make relative asset HREFs absolute "
                            "if no self_href is set."
                        )
                asset.href = utils.make_absolute_href(asset.href, self_href)

        return self

    def set_collection(self, collection: Optional["Collection_Type"]) -> "Item":
        """Set the collection of this item.

        This method will replace any existing Collection link and attribute for
        this item.

        Args:
            collection : The collection to set as this
                item's collection. If None, will clear the collection.

        Returns:
            Item: self
        """
        self.remove_links(rel_type.RelType.COLLECTION)
        self.collection_id = None
        if collection is not None:
            self.add_link(link_mod.Link.collection(collection))
            self.collection_id = collection.id

        return self

    def get_collection(self) -> Optional["Collection_Type"]:
        """Gets the collection of this item, if one exists.

        Returns:
            Collection or None: If this item belongs to a collection, returns
            a reference to the collection. Otherwise returns None.
        """
        collection_link = self.get_single_link(rel_type.RelType.COLLECTION)
        if collection_link is None:
            return None
        else:
            return cast("Collection_Type", collection_link.resolve_stac_object().target)

    def to_dict(self, include_self_link: bool = True) -> Dict[str, Any]:
        links = self.links
        if not include_self_link:
            links = [x for x in links if x.rel != rel_type.RelType.SELF]

        assets = {k: v.to_dict() for k, v in self.assets.items()}

        if self.datetime is not None:
            self.properties["datetime"] = utils.datetime_to_str(self.datetime)
        else:
            self.properties["datetime"] = None

        d: Dict[str, Any] = {
            "type": "Feature",
            "stac_version": pystac.get_stac_version(),
            "id": self.id,
            "properties": self.properties,
            "geometry": self.geometry,
            "links": [link.to_dict() for link in links],
            "assets": assets,
        }

        if self.bbox is not None:
            d["bbox"] = self.bbox

        if self.stac_extensions is not None:
            d["stac_extensions"] = self.stac_extensions

        if self.collection_id:
            d["collection"] = self.collection_id

        for key in self.extra_fields:
            d[key] = self.extra_fields[key]

        return d

    def clone(self) -> "Item":
        cls = self.__class__
        clone = cls(
            id=self.id,
            geometry=deepcopy(self.geometry),
            bbox=copy(self.bbox),
            datetime=copy(self.datetime),
            properties=deepcopy(self.properties),
            stac_extensions=deepcopy(self.stac_extensions),
            collection=self.collection_id,
        )
        for link in self.links:
            clone.add_link(link.clone())

        for k, asset in self.assets.items():
            clone.add_asset(k, asset.clone())

        return clone

    def _object_links(self) -> List[Union[str, rel_type.RelType]]:
        return [
            rel_type.RelType.COLLECTION,
            *pystac.EXTENSION_HOOKS.get_extended_object_links(self),
        ]

    @classmethod
    def from_dict(
        cls,
        d: Dict[str, Any],
        href: Optional[str] = None,
        root: Optional["Catalog_Type"] = None,
        migrate: bool = False,
        preserve_dict: bool = True,
    ) -> "Item":
        if migrate:
            info = identify.identify_stac_object(d)
            d = migrate_mod.migrate_to_latest(d, info)

        if not cls.matches_object_type(d):
            raise errors.STACTypeError(
                f"{d} does not represent a {cls.__name__} instance"
            )

        if preserve_dict:
            d = deepcopy(d)

        id = d.pop("id")
        geometry = d.pop("geometry")
        properties = d.pop("properties")
        bbox = d.pop("bbox", None)
        stac_extensions = d.get("stac_extensions")
        collection_id = d.pop("collection", None)

        datetime = properties.get("datetime")
        if datetime is not None:
            datetime = dateutil.parser.parse(datetime)
        links = d.pop("links")
        assets = d.pop("assets")

        d.pop("type")
        d.pop("stac_version")

        item = cls(
            id=id,
            geometry=geometry,
            bbox=bbox,
            datetime=datetime,
            properties=properties,
            stac_extensions=stac_extensions,
            collection=collection_id,
            extra_fields=d,
        )

        has_self_link = False
        for link in links:
            has_self_link |= link["rel"] == rel_type.RelType.SELF
            item.add_link(link_mod.Link.from_dict(link))

        if not has_self_link and href is not None:
            item.add_link(link_mod.Link.self_href(href))

        for k, v in assets.items():
            asset = asset_mod.Asset.from_dict(v)
            asset.set_owner(item)
            item.assets[k] = asset

        if root:
            item.set_root(root)

        return item

    @property
    def common_metadata(self) -> common_metadata.CommonMetadata:
        """Access the item's common metadata fields as a
        :class:`~pystac.CommonMetadata` object."""
        return common_metadata.CommonMetadata(self)

    def full_copy(
        self,
        root: Optional["Catalog_Type"] = None,
        parent: Optional["Catalog_Type"] = None,
    ) -> "Item":
        return cast(Item, super().full_copy(root, parent))

    @classmethod
    def from_file(cls, href: str, stac_io: Optional["StacIO_Type"] = None) -> "Item":
        result = super().from_file(href, stac_io)
        if not isinstance(result, Item):
            raise errors.STACTypeError(f"{result} is not a {Item}.")
        return result

    @classmethod
    def matches_object_type(cls, d: Dict[str, Any]) -> bool:
        return identify.identify_stac_object_type(d) == stac_object.STACObjectType.ITEM
