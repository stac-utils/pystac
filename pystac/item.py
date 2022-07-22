from html import escape
from copy import copy, deepcopy
from datetime import datetime as Datetime
from pystac.catalog import Catalog
from typing import Any, Dict, List, Optional, Union, cast

import pystac
from pystac.html.jinja_env import get_jinja_env
from pystac import STACError, STACObjectType
from pystac.asset import Asset
from pystac.link import Link
from pystac.serialization import (
    identify_stac_object_type,
    identify_stac_object,
    migrate_to_latest,
)
from pystac.stac_object import STACObject
from pystac.utils import (
    is_absolute_href,
    make_absolute_href,
    make_relative_href,
    datetime_to_str,
    str_to_datetime,
)
from pystac.collection import Collection


class Item(STACObject):
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
        assets : A dictionary mapping string keys to :class:`~pystac.Asset` objects. All
            :class:`~pystac.Asset` values in the dictionary will have their
            :attr:`~pystac.Asset.owner` attribute set to the created Item.
    """

    assets: Dict[str, Asset]
    """Dictionary of :class:`~pystac.Asset` objects, each with a unique key."""

    bbox: Optional[List[float]]
    """Bounding Box of the asset represented by this item using either 2D or 3D
    geometries. The length of the array is 2*n where n is the number of dimensions.
    Could also be None in the case of a null geometry."""

    collection: Optional[Collection]
    """:class:`~pystac.Collection` to which this Item belongs, if any."""

    collection_id: Optional[str]
    """The Collection ID that this item belongs to, if any."""

    datetime: Optional[Datetime]
    """Datetime associated with this item. If ``None``, then
    :attr:`~pystac.CommonMetadata.start_datetime` and
    :attr:`~pystac.CommonMetadata.end_datetime` in :attr:`~pystac.Item.common_metadata`
    will supply the datetime range of the Item."""

    extra_fields: Dict[str, Any]
    """Extra fields that are part of the top-level JSON fields the Item."""

    geometry: Optional[Dict[str, Any]]
    """Defines the full footprint of the asset represented by this item, formatted
    according to `RFC 7946, section 3.1 (GeoJSON)
    <https://tools.ietf.org/html/rfc7946>`_."""

    id: str
    """Provider identifier. Unique within the STAC."""

    links: List[Link]
    """A list of :class:`~pystac.Link` objects representing all links associated with
    this Item."""

    properties: Dict[str, Any]
    """A dictionary of additional metadata for the Item."""

    stac_extensions: List[str]
    """List of extensions the Item implements."""

    STAC_OBJECT_TYPE = STACObjectType.ITEM

    def __init__(
        self,
        id: str,
        geometry: Optional[Dict[str, Any]],
        bbox: Optional[List[float]],
        datetime: Optional[Datetime],
        properties: Dict[str, Any],
        stac_extensions: Optional[List[str]] = None,
        href: Optional[str] = None,
        collection: Optional[Union[str, Collection]] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
        assets: Optional[Dict[str, Asset]] = None,
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

        self.assets: Dict[str, Asset] = {}

        self.datetime: Optional[Datetime] = None
        if datetime is None:
            if "start_datetime" not in properties or "end_datetime" not in properties:
                raise STACError(
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
            if isinstance(collection, Collection):
                self.set_collection(collection)
            else:
                self.collection_id = collection

        self.assets = {}
        if assets is not None:
            for k, asset in assets.items():
                self.add_asset(k, asset)

    def __repr__(self) -> str:
        return "<Item id={}>".format(self.id)

    def _repr_html_(self) -> str:
        jinja_env = get_jinja_env()
        if jinja_env:
            template = jinja_env.get_template("Item.jinja2")
            return str(template.render(item=self))
        else:
            return escape(repr(self))

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
                if not is_absolute_href(asset_href):
                    abs_href = make_absolute_href(asset_href, prev_href)
                    new_relative_href = make_relative_href(abs_href, new_href)
                    asset.href = new_relative_href

    def get_datetime(self, asset: Optional[Asset] = None) -> Optional[Datetime]:
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
                return str_to_datetime(asset_dt)

    def set_datetime(self, datetime: Datetime, asset: Optional[Asset] = None) -> None:
        """Set an Item or an Asset datetime.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.datetime = datetime
        else:
            asset.extra_fields["datetime"] = datetime_to_str(datetime)

    def get_assets(self) -> Dict[str, Asset]:
        """Get this item's assets.

        Returns:
            Dict[str, Asset]: A copy of the dictionary of this item's assets.
        """
        return dict(self.assets.items())

    def add_asset(self, key: str, asset: Asset) -> None:
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
            if is_absolute_href(href):
                if self_href is None:
                    self_href = self.get_self_href()
                    if self_href is None:
                        raise STACError(
                            "Cannot make asset HREFs relative "
                            "if no self_href is set."
                        )
                asset.href = make_relative_href(asset.href, self_href)
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
            if not is_absolute_href(href):
                if self_href is None:
                    self_href = self.get_self_href()
                    if self_href is None:
                        raise STACError(
                            "Cannot make relative asset HREFs absolute "
                            "if no self_href is set."
                        )
                asset.href = make_absolute_href(asset.href, self_href)

        return self

    def set_collection(self, collection: Optional[Collection]) -> "Item":
        """Set the collection of this item.

        This method will replace any existing Collection link and attribute for
        this item.

        Args:
            collection : The collection to set as this
                item's collection. If None, will clear the collection.

        Returns:
            Item: self
        """
        self.remove_links(pystac.RelType.COLLECTION)
        self.collection_id = None
        if collection is not None:
            self.add_link(Link.collection(collection))
            self.collection_id = collection.id

        return self

    def get_collection(self) -> Optional[Collection]:
        """Gets the collection of this item, if one exists.

        Returns:
            Collection or None: If this item belongs to a collection, returns
            a reference to the collection. Otherwise returns None.
        """
        collection_link = self.get_single_link(pystac.RelType.COLLECTION)
        if collection_link is None:
            return None
        else:
            return cast(Collection, collection_link.resolve_stac_object().target)

    def to_dict(
        self, include_self_link: bool = True, transform_hrefs: bool = True
    ) -> Dict[str, Any]:
        links = self.links
        if not include_self_link:
            links = [x for x in links if x.rel != pystac.RelType.SELF]

        assets = {k: v.to_dict() for k, v in self.assets.items()}

        if self.datetime is not None:
            self.properties["datetime"] = datetime_to_str(self.datetime)
        else:
            self.properties["datetime"] = None

        d: Dict[str, Any] = {
            "type": "Feature",
            "stac_version": pystac.get_stac_version(),
            "id": self.id,
            "properties": self.properties,
            "geometry": self.geometry,
            "links": [link.to_dict(transform_href=transform_hrefs) for link in links],
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
            assets={k: asset.clone() for k, asset in self.assets.items()},
        )
        for link in self.links:
            clone.add_link(link.clone())

        return clone

    def _object_links(self) -> List[Union[str, pystac.RelType]]:
        return [
            pystac.RelType.COLLECTION,
            *pystac.EXTENSION_HOOKS.get_extended_object_links(self),
        ]

    @classmethod
    def from_dict(
        cls,
        d: Dict[str, Any],
        href: Optional[str] = None,
        root: Optional[Catalog] = None,
        migrate: bool = False,
        preserve_dict: bool = True,
    ) -> "Item":
        if migrate:
            info = identify_stac_object(d)
            d = migrate_to_latest(d, info)

        if not cls.matches_object_type(d):
            raise pystac.STACTypeError(
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
            datetime = str_to_datetime(datetime)
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
            assets={k: Asset.from_dict(v) for k, v in assets.items()},
        )

        has_self_link = False
        for link in links:
            has_self_link |= link["rel"] == pystac.RelType.SELF
            item.add_link(Link.from_dict(link))

        if not has_self_link and href is not None:
            item.add_link(Link.self_href(href))

        if root:
            item.set_root(root)

        return item

    @property
    def common_metadata(self) -> pystac.CommonMetadata:
        """Access the item's common metadata fields as a
        :class:`~pystac.CommonMetadata` object."""
        return pystac.CommonMetadata(self)

    def full_copy(
        self, root: Optional["Catalog"] = None, parent: Optional["Catalog"] = None
    ) -> "Item":
        return cast(Item, super().full_copy(root, parent))

    @classmethod
    def from_file(cls, href: str, stac_io: Optional[pystac.StacIO] = None) -> "Item":
        result = super().from_file(href, stac_io)
        if not isinstance(result, Item):
            raise pystac.STACTypeError(f"{result} is not a {Item}.")
        return result

    @classmethod
    def matches_object_type(cls, d: Dict[str, Any]) -> bool:
        return identify_stac_object_type(d) == STACObjectType.ITEM
