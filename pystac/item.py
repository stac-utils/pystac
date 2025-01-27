from __future__ import annotations

import warnings
from copy import copy, deepcopy
from typing import TYPE_CHECKING, Any, TypeVar, cast

import pystac
from pystac import RelType, STACError, STACObjectType
from pystac.asset import Asset, Assets
from pystac.catalog import Catalog
from pystac.collection import Collection
from pystac.errors import DeprecatedWarning, ExtensionNotImplemented
from pystac.link import Link
from pystac.serialization import (
    identify_stac_object,
    identify_stac_object_type,
    migrate_to_latest,
)
from pystac.stac_object import STACObject
from pystac.utils import (
    datetime_to_str,
    is_absolute_href,
    make_absolute_href,
    make_relative_href,
    str_to_datetime,
)

#: Generalized version of :class:`Item`
T = TypeVar("T", bound="Item")

if TYPE_CHECKING:
    # avoids conflicts since there are also kwargs and attrs called `datetime`
    from datetime import datetime as Datetime

    from pystac.extensions.ext import ItemExt


class Item(STACObject, Assets):
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
        datetime : datetime associated with this item. If None,
            a start_datetime and end_datetime must be supplied.
        properties : A dictionary of additional metadata for the item.
        start_datetime : Optional inclusive start datetime, part of common metadata.
            This value will override any `start_datetime` key in properties.
        end_datetime : Optional inclusive end datetime, part of common metadata.
            This value will override any `end_datetime` key in properties.
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

    assets: dict[str, Asset]
    """Dictionary of :class:`~pystac.Asset` objects, each with a unique key."""

    bbox: list[float] | None
    """Bounding Box of the asset represented by this item using either 2D or 3D
    geometries. The length of the array is 2*n where n is the number of dimensions.
    Could also be None in the case of a null geometry."""

    collection: Collection | None
    """:class:`~pystac.Collection` to which this Item belongs, if any."""

    collection_id: str | None
    """The Collection ID that this item belongs to, if any."""

    datetime: Datetime | None
    """Datetime associated with this item. If ``None``, then
    :attr:`~pystac.CommonMetadata.start_datetime` and
    :attr:`~pystac.CommonMetadata.end_datetime` in :attr:`~pystac.Item.common_metadata`
    will supply the datetime range of the Item."""

    extra_fields: dict[str, Any]
    """Extra fields that are part of the top-level JSON fields the Item."""

    geometry: dict[str, Any] | None
    """Defines the full footprint of the asset represented by this item, formatted
    according to `RFC 7946, section 3.1 (GeoJSON)
    <https://tools.ietf.org/html/rfc7946>`_."""

    id: str
    """Provider identifier. Unique within the STAC."""

    links: list[Link]
    """A list of :class:`~pystac.Link` objects representing all links associated with
    this Item."""

    properties: dict[str, Any]
    """A dictionary of additional metadata for the Item."""

    stac_extensions: list[str]
    """List of extensions the Item implements."""

    STAC_OBJECT_TYPE = STACObjectType.ITEM

    def __init__(
        self,
        id: str,
        geometry: dict[str, Any] | None,
        bbox: list[float] | None,
        datetime: Datetime | None,
        properties: dict[str, Any],
        start_datetime: Datetime | None = None,
        end_datetime: Datetime | None = None,
        stac_extensions: list[str] | None = None,
        href: str | None = None,
        collection: str | Collection | None = None,
        extra_fields: dict[str, Any] | None = None,
        assets: dict[str, Asset] | None = None,
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

        self.assets: dict[str, Asset] = {}

        self.datetime: Datetime | None = None
        if start_datetime:
            properties["start_datetime"] = datetime_to_str(start_datetime)
        if end_datetime:
            properties["end_datetime"] = datetime_to_str(end_datetime)
        if datetime is None:
            if "start_datetime" not in properties or "end_datetime" not in properties:
                raise STACError(
                    "Invalid Item: If datetime is None, "
                    "a start_datetime and end_datetime "
                    "must be supplied."
                )
            self.datetime = None
        else:
            self.datetime = datetime

        if href is not None:
            self.set_self_href(href)

        self.collection_id: str | None = None
        if collection is None:
            self.collection = None
        else:
            if isinstance(collection, Collection):
                self.set_collection(collection)
            else:
                self.collection_id = collection

        self.assets = {}
        if assets is not None:
            for k, asset in assets.items():
                self.add_asset(k, asset)

    def __repr__(self) -> str:
        return f"<Item id={self.id}>"

    def __getstate__(self) -> dict[str, Any]:
        """Ensure that pystac does not encode too much information when pickling"""
        d = self.__dict__.copy()

        d["links"] = [
            (
                link.to_dict(transform_href=False)
                if link.get_href(transform_href=False)
                else link
            )
            for link in d["links"]
        ]

        return d

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Ensure that pystac knows how to decode the pickled object"""
        d = state.copy()

        d["links"] = [
            Link.from_dict(link).set_owner(self) if isinstance(link, dict) else link
            for link in d["links"]
        ]

        self.__dict__ = d

    def set_self_href(self, href: str | None) -> None:
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

    def get_datetime(self, asset: Asset | None = None) -> Datetime | None:
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

    def set_datetime(self, datetime: Datetime, asset: Asset | None = None) -> None:
        """Set an Item or an Asset datetime.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.datetime = datetime
        else:
            asset.extra_fields["datetime"] = datetime_to_str(datetime)

    def set_collection(self, collection: Collection | None) -> Item:
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

    def get_collection(self) -> Collection | None:
        """Gets the collection of this item, if one exists.

        Returns:
            Collection or None: If this item belongs to a collection, returns
            a reference to the collection. Otherwise returns None.
        """
        collection_link = self.get_single_link(pystac.RelType.COLLECTION)
        if collection_link is None:
            return None
        else:
            return cast(
                Collection, collection_link.resolve_stac_object(self.get_root()).target
            )

    def add_derived_from(self, *items: Item | str) -> Item:
        """Add one or more items that this is derived from.

        This method will add to any existing "derived_from" links.

        Args:
            items : Items (or href of items) to add to derived_from links.

        Returns:
            Item: self
        """
        for item in items:
            self.add_link(Link.derived_from(item))
        return self

    def remove_derived_from(self, item_id: str) -> None:
        """Remove an item that this is derived from.

        This method will remove from existing "derived_from" links.

        Args:
            item_id : ID of item to remove from derived_from links.
        """
        new_links: list[pystac.Link] = []

        for link in self.links:
            if link.rel != pystac.RelType.DERIVED_FROM:
                new_links.append(link)
            else:
                try:
                    item = cast(Item, link.resolve_stac_object().target)
                except Exception as e:
                    raise pystac.STACError(
                        "Link failed to resolve. Use remove_links instead."
                    ) from e
                if item.id != item_id:
                    new_links.append(link)
        self.links = new_links

    def get_derived_from(self) -> list[Item]:
        """Get the items that this is derived from.

        Returns:
            List[Item]: Returns a reference to the derived_from items.
        """
        links = self.get_links(pystac.RelType.DERIVED_FROM)
        try:
            return [cast(Item, link.resolve_stac_object().target) for link in links]
        except Exception as e:
            raise pystac.STACError(
                "Link failed to resolve. Use get_links instead."
            ) from e

    def to_dict(
        self, include_self_link: bool = True, transform_hrefs: bool = True
    ) -> dict[str, Any]:
        links = self.links
        if not include_self_link:
            links = [x for x in links if x.rel != pystac.RelType.SELF]

        assets = {k: v.to_dict() for k, v in self.assets.items()}

        if self.datetime is not None:
            self.properties["datetime"] = datetime_to_str(self.datetime)
        else:
            self.properties["datetime"] = None

        d: dict[str, Any] = {
            "type": "Feature",
            "stac_version": pystac.get_stac_version(),
            "stac_extensions": self.stac_extensions if self.stac_extensions else [],
            "id": self.id,
            "geometry": self.geometry,
            "bbox": self.bbox if self.bbox is not None else [],
            "properties": self.properties,
            "links": [link.to_dict(transform_href=transform_hrefs) for link in links],
            "assets": assets,
        }

        if self.collection_id:
            d["collection"] = self.collection_id

        for key in self.extra_fields:
            d[key] = self.extra_fields[key]

        # This field is prohibited if there's no geometry
        if not self.geometry:
            d.pop("bbox")

        return d

    def clone(self) -> Item:
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

    def _object_links(self) -> list[str | pystac.RelType]:
        return [
            pystac.RelType.COLLECTION,
            *pystac.EXTENSION_HOOKS.get_extended_object_links(self),
        ]

    @classmethod
    def from_dict(
        cls: type[T],
        d: dict[str, Any],
        href: str | None = None,
        root: Catalog | None = None,
        migrate: bool = True,
        preserve_dict: bool = True,
    ) -> T:
        from pystac.extensions.version import ItemVersionExtension

        if preserve_dict:
            d = deepcopy(d)

        if migrate:
            info = identify_stac_object(d)
            d = migrate_to_latest(d, info)

        if not cls.matches_object_type(d):
            raise pystac.STACTypeError(d, cls)

        # some fields are passed through to __init__
        pass_through_fields = [
            "id",
            "geometry",
            "bbox",
            "stac_extensions",
            "collection",
        ]

        # some fields need some parsing or special handling
        parse_fields = ["links", "assets", "properties"]
        links = d.get("links", [])
        assets = d.get("assets", {})
        properties = d.get("properties", {})
        datetime = properties.get("datetime")
        if datetime is not None:
            datetime = str_to_datetime(datetime)

        # some fields are excluded from __init__ entirely
        exclude_fields = ["type", "stac_version"]

        # get all the fields that are not passed through, parsed, or excluded
        extra_fields = {
            k: v
            for k, v in d.items()
            if k not in [*pass_through_fields, *parse_fields, *exclude_fields]
        }

        item = cls(
            **{k: d.get(k) for k in pass_through_fields},  # type: ignore
            datetime=datetime,
            properties=properties,
            extra_fields=extra_fields,
            href=href,
            assets={k: Asset.from_dict(v) for k, v in assets.items()},
        )

        for link in links:
            if href is None or link.get("rel", None) != RelType.SELF:
                item.add_link(Link.from_dict(link))

        if root:
            item.set_root(root)

        try:
            version = ItemVersionExtension.ext(item)
            if version.deprecated:
                warnings.warn(
                    f"The item '{item.id}' is deprecated.",
                    DeprecatedWarning,
                )
            # Item asset deprecation checks pending version extension support
        except ExtensionNotImplemented:
            pass

        return item

    @property
    def common_metadata(self) -> pystac.CommonMetadata:
        """Access the item's common metadata fields as a
        :class:`~pystac.CommonMetadata` object."""
        return pystac.CommonMetadata(self)

    def full_copy(
        self, root: Catalog | None = None, parent: Catalog | None = None
    ) -> Item:
        return cast(Item, super().full_copy(root, parent))

    @classmethod
    def matches_object_type(cls, d: dict[str, Any]) -> bool:
        for field in ("type", "stac_version"):
            if field not in d:
                raise pystac.STACTypeError(d, cls, f"'{field}' is missing.")
        return identify_stac_object_type(d) == STACObjectType.ITEM

    @property
    def __geo_interface__(self) -> dict[str, Any]:
        """Returns this item as a dictionary.

        This just calls `to_dict` without self links or transforming any hrefs.

        https://gist.github.com/sgillies/2217756

        Returns:
            Dict[str, Any]: This item as a dictionary.
        """
        return self.to_dict(include_self_link=False, transform_hrefs=False)

    @property
    def ext(self) -> ItemExt:
        """Accessor for extension classes on this item

        Example::

            item.ext.proj.code = "EPSG:4326"
        """
        from pystac.extensions.ext import ItemExt

        return ItemExt(stac_object=self)
