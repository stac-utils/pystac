from copy import copy, deepcopy
from datetime import datetime as Datetime
from pystac.catalog import Catalog
from typing import Any, Dict, List, Optional, Union, cast

import dateutil.parser

import pystac
from pystac import STACError, STACObjectType
from pystac.asset import Asset
from pystac.link import Link
from pystac.stac_object import STACObject
from pystac.utils import (
    is_absolute_href,
    make_absolute_href,
    make_relative_href,
    datetime_to_str,
    str_to_datetime,
)
from pystac.collection import Collection, Provider


class CommonMetadata:
    """Object containing fields that are not included in core item schema but
    are still commonly used. All attributes are defined within the properties of
    this item and are optional

    Args:
        properties (dict): Dictionary of attributes that is the Item's properties
    """

    def __init__(self, properties: Dict[str, Any]):
        self.properties = properties

    # Basics
    @property
    def title(self) -> Optional[str]:
        """Get or set the item's title

        Returns:
            str: Human readable title describing the item
        """
        return self.properties.get("title")

    @title.setter
    def title(self, v: Optional[str]) -> None:
        self.properties["title"] = v

    @property
    def description(self) -> Optional[str]:
        """Get or set the item's description

        Returns:
            str: Detailed description of the item
        """
        return self.properties.get("description")

    @description.setter
    def description(self, v: Optional[str]) -> None:
        self.properties["description"] = v

    # Date and Time Range
    @property
    def start_datetime(self) -> Optional[Datetime]:
        """Get or set the item's start_datetime.

        Returns:
            datetime: Start date and time for the item
        """
        return self.get_start_datetime()

    @start_datetime.setter
    def start_datetime(self, v: Optional[Datetime]) -> None:
        self.set_start_datetime(v)

    def get_start_datetime(self, asset: Optional[Asset] = None) -> Optional[Datetime]:
        """Gets an Item or an Asset start_datetime.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            datetime
        """
        if asset is None or "start_datetime" not in asset.properties:
            start_datetime = self.properties.get("start_datetime")
        else:
            start_datetime = asset.properties.get("start_datetime")

        if start_datetime:
            start_datetime = str_to_datetime(start_datetime)

        return start_datetime

    def set_start_datetime(
        self, start_datetime: Optional[Datetime], asset: Optional[Asset] = None
    ) -> None:
        """Set an Item or an Asset start_datetime.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["start_datetime"] = (
                None if start_datetime is None else datetime_to_str(start_datetime)
            )
        else:
            asset.properties["start_datetime"] = (
                None if start_datetime is None else datetime_to_str(start_datetime)
            )

    @property
    def end_datetime(self) -> Optional[Datetime]:
        """Get or set the item's end_datetime. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string

        Returns:
            datetime: End date and time for the item
        """
        return self.get_end_datetime()

    @end_datetime.setter
    def end_datetime(self, v: Optional[Datetime]) -> None:
        self.set_end_datetime(v)

    def get_end_datetime(self, asset: Optional[Asset] = None) -> Optional[Datetime]:
        """Gets an Item or an Asset end_datetime.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            datetime
        """
        if asset is None or "end_datetime" not in asset.properties:
            end_datetime = self.properties.get("end_datetime")
        else:
            end_datetime = asset.properties.get("end_datetime")

        if end_datetime:
            end_datetime = str_to_datetime(end_datetime)

        return end_datetime

    def set_end_datetime(
        self, end_datetime: Optional[Datetime], asset: Optional[Asset] = None
    ) -> None:
        """Set an Item or an Asset end_datetime.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["end_datetime"] = (
                None if end_datetime is None else datetime_to_str(end_datetime)
            )
        else:
            asset.properties["end_datetime"] = (
                None if end_datetime is None else datetime_to_str(end_datetime)
            )

    # License
    @property
    def license(self) -> Optional[str]:
        """Get or set the current license

        Returns:
            str: Item's license(s), either SPDX identifier of 'various'
        """
        return self.get_license()

    @license.setter
    def license(self, v: Optional[str]) -> None:
        self.set_license(v)

    def get_license(self, asset: Optional[Asset] = None) -> Optional[str]:
        """Gets an Item or an Asset license.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or "license" not in asset.properties:
            return self.properties.get("license")
        else:
            return asset.properties.get("license")

    def set_license(
        self, license: Optional[str], asset: Optional[Asset] = None
    ) -> None:
        """Set an Item or an Asset license.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["license"] = license
        else:
            asset.properties["license"] = license

    # Providers
    @property
    def providers(self) -> Optional[List[Provider]]:
        """Get or set a list of the item's providers. The setter can take either
        a Provider object or a dict but always stores each provider as a dict

        Returns:
            List[Provider]: List of organizations that captured or processed the data,
            encoded as Provider objects
        """
        return self.get_providers()

    @providers.setter
    def providers(self, v: Optional[List[Provider]]) -> None:
        self.set_providers(v)

    def get_providers(self, asset: Optional[Asset] = None) -> Optional[List[Provider]]:
        """Gets an Item or an Asset providers.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            List[Provider]
        """
        if asset is None or "providers" not in asset.properties:
            providers = self.properties.get("providers")
        else:
            providers = asset.properties.get("providers")

        if providers is not None:
            providers = [Provider.from_dict(d) for d in providers]

        return providers

    def set_providers(
        self, providers: Optional[List[Provider]], asset: Optional[Asset] = None
    ) -> None:
        """Set an Item or an Asset providers.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            if providers is None:
                self.properties.pop("providers", None)
            else:
                providers_dicts = [d.to_dict() for d in providers]
                self.properties["providers"] = providers_dicts
        else:
            if providers is None:
                asset.properties.pop("providers", None)
            else:
                providers_dicts = [d.to_dict() for d in providers]
                asset.properties["providers"] = providers_dicts

    # Instrument
    @property
    def platform(self) -> Optional[str]:
        """Get or set the item's platform attribute

        Returns:
            str: Unique name of the specific platform to which the instrument
            is attached
        """
        return self.get_platform()

    @platform.setter
    def platform(self, v: Optional[str]) -> None:
        self.set_platform(v)

    def get_platform(self, asset: Optional[Asset] = None) -> Optional[str]:
        """Gets an Item or an Asset platform.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or "platform" not in asset.properties:
            return self.properties.get("platform")
        else:
            return asset.properties.get("platform")

    def set_platform(
        self, platform: Optional[str], asset: Optional[Asset] = None
    ) -> None:
        """Set an Item or an Asset platform.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["platform"] = platform
        else:
            asset.properties["platform"] = platform

    @property
    def instruments(self) -> Optional[List[str]]:
        """Get or set the names of the instruments used

        Returns:
            List[str]: Name(s) of instrument(s) used
        """
        return self.get_instruments()

    @instruments.setter
    def instruments(self, v: Optional[List[str]]) -> None:
        self.set_instruments(v)

    def get_instruments(self, asset: Optional[Asset] = None) -> Optional[List[str]]:
        """Gets an Item or an Asset instruments.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            Optional[List[str]]
        """
        if asset is None or "instruments" not in asset.properties:
            return self.properties.get("instruments")
        else:
            return asset.properties.get("instruments")

    def set_instruments(
        self, instruments: Optional[List[str]], asset: Optional[Asset] = None
    ) -> None:
        """Set an Item or an Asset instruments.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["instruments"] = instruments
        else:
            asset.properties["instruments"] = instruments

    @property
    def constellation(self) -> Optional[str]:
        """Get or set the name of the constellation associate with an item

        Returns:
            str: Name of the constellation to which the platform belongs
        """
        return self.get_constellation()

    @constellation.setter
    def constellation(self, v: Optional[str]) -> None:
        self.set_constellation(v)

    def get_constellation(self, asset: Optional[Asset] = None) -> Optional[str]:
        """Gets an Item or an Asset constellation.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or "constellation" not in asset.properties:
            return self.properties.get("constellation")
        else:
            return asset.properties.get("constellation")

    def set_constellation(
        self, constellation: Optional[str], asset: Optional[Asset] = None
    ) -> None:
        """Set an Item or an Asset constellation.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["constellation"] = constellation
        else:
            asset.properties["constellation"] = constellation

    @property
    def mission(self) -> Optional[str]:
        """Get or set the name of the mission associated with an item

        Returns:
            str: Name of the mission in which data are collected
        """
        return self.get_mission()

    @mission.setter
    def mission(self, v: Optional[str]) -> None:
        self.set_mission(v)

    def get_mission(self, asset: Optional[Asset] = None) -> Optional[str]:
        """Gets an Item or an Asset mission.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or "mission" not in asset.properties:
            return self.properties.get("mission")
        else:
            return asset.properties.get("mission")

    def set_mission(
        self, mission: Optional[str], asset: Optional[Asset] = None
    ) -> None:
        """Set an Item or an Asset mission.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["mission"] = mission
        else:
            asset.properties["mission"] = mission

    @property
    def gsd(self) -> Optional[float]:
        """Get or sets the Ground Sample Distance at the sensor.

        Returns:
            [float]: Ground Sample Distance at the sensor
        """
        return self.get_gsd()

    @gsd.setter
    def gsd(self, v: Optional[float]) -> None:
        self.set_gsd(v)

    def get_gsd(self, asset: Optional[Asset] = None) -> Optional[float]:
        """Gets an Item or an Asset gsd.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            float
        """
        if asset is None or "gsd" not in asset.properties:
            return self.properties.get("gsd")
        else:
            return asset.properties.get("gsd")

    def set_gsd(self, gsd: Optional[float], asset: Optional[Asset] = None) -> None:
        """Set an Item or an Asset gsd.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["gsd"] = gsd
        else:
            asset.properties["gsd"] = gsd

    # Metadata
    @property
    def created(self) -> Optional[Datetime]:
        """Get or set the metadata file's creation date. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string

        Returns:
            datetime: Creation date and time of the metadata file
        """
        return self.get_created()

    @created.setter
    def created(self, v: Optional[Datetime]) -> None:
        self.set_created(v)

    def get_created(self, asset: Optional[Asset] = None) -> Optional[Datetime]:
        """Gets an Item or an Asset created time.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value.

        Note:
            ``created`` and ``updated`` have different meaning depending on where they
            are used. If those fields are available in the Item `properties`, it's
            referencing to the creation and update times of the metadata. Having those
            fields in the Item `assets` refers to the creation and update times of the
            actual data linked to in the Asset Object.

        Returns:
            datetime
        """
        if asset is None or "created" not in asset.properties:
            created = self.properties.get("created")
        else:
            created = asset.properties.get("created")

        if created:
            created = str_to_datetime(created)

        return created

    def set_created(
        self, created: Optional[Datetime], asset: Optional[Asset] = None
    ) -> None:
        """Set an Item or an Asset created time.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["created"] = (
                None if created is None else datetime_to_str(created)
            )
        else:
            asset.properties["created"] = (
                None if created is None else datetime_to_str(created)
            )

    @property
    def updated(self) -> Optional[Datetime]:
        """Get or set the metadata file's update date. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string

        Note:
            ``created`` and ``updated`` have different meaning depending on where they
            are used. If those fields are available in the Item `properties`, it's
            referencing to the creation and update times of the metadata. Having those
            fields in the Item `assets` refers to the creation and update times of the
            actual data linked to in the Asset Object.


        Returns:
            datetime: Date and time that the metadata file was most recently
                updated
        """
        return self.get_updated()

    @updated.setter
    def updated(self, v: Optional[Datetime]) -> None:
        self.set_updated(v)

    def get_updated(self, asset: Optional[Asset] = None) -> Optional[Datetime]:
        """Gets an Item or an Asset updated time.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value.

        Note:
            ``created`` and ``updated`` have different meaning depending on where they
            are used. If those fields are available in the Item `properties`, it's
            referencing to the creation and update times of the metadata. Having those
            fields in the Item `assets` refers to the creation and update times of the
            actual data linked to in the Asset Object.

        Returns:
            datetime
        """
        if asset is None or "updated" not in asset.properties:
            updated = self.properties.get("updated")
        else:
            updated = asset.properties.get("updated")

        if updated:
            updated = str_to_datetime(updated)

        return updated

    def set_updated(
        self, updated: Optional[Datetime], asset: Optional[Asset] = None
    ) -> None:
        """Set an Item or an Asset updated time.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["updated"] = (
                None if updated is None else datetime_to_str(updated)
            )
        else:
            asset.properties["updated"] = (
                None if updated is None else datetime_to_str(updated)
            )


class Item(STACObject):
    """An Item is the core granular entity in a STAC, containing the core metadata
    that enables any client to search or crawl online catalogs of spatial 'assets' -
    satellite imagery, derived data, DEM's, etc.

    Args:
        id (str): Provider identifier. Must be unique within the STAC.
        geometry (dict): Defines the full footprint of the asset represented by this
            item, formatted according to
            `RFC 7946, section 3.1 (GeoJSON) <https://tools.ietf.org/html/rfc7946>`_.
        bbox (List[float] or None):  Bounding Box of the asset represented by this item
            using either 2D or 3D geometries. The length of the array must be 2*n
            where n is the number of dimensions. Could also be None in the case of a
            null geometry.
        datetime (datetime or None): Datetime associated with this item. If None,
            a start_datetime and end_datetime must be supplied in the properties.
        properties (dict): A dictionary of additional metadata for the item.
        stac_extensions (List[str]): Optional list of extensions the Item implements.
        href (str or None): Optional HREF for this item, which be set as the item's
            self link's HREF.
        collection (Collection or str): The Collection or Collection ID that this item
            belongs to.
        extra_fields (dict or None): Extra fields that are part of the top-level JSON
            properties of the Item.

    Attributes:
        id (str): Provider identifier. Unique within the STAC.
        geometry (dict): Defines the full footprint of the asset represented by this
            item, formatted according to
            `RFC 7946, section 3.1 (GeoJSON) <https://tools.ietf.org/html/rfc7946>`_.
        bbox (List[float] or None):  Bounding Box of the asset represented by this item
            using either 2D or 3D geometries. The length of the array is 2*n where n
            is the number of dimensions. Could also be None in the case of a null
            geometry.
        datetime (datetime or None): Datetime associated with this item. If None,
            the start_datetime and end_datetime in the common_metadata
            will supply the datetime range of the Item.
        properties (dict): A dictionary of additional metadata for the item.
        stac_extensions (List[str] or None): Optional list of extensions the Item
            implements.
        collection (Collection or None): Collection that this item is a part of.
        links (List[Link]): A list of :class:`~pystac.Link` objects representing
            all links associated with this STACObject.
        assets (Dict[str, Asset]): Dictionary of asset objects that can be downloaded,
            each with a unique key.
        collection_id (str or None): The Collection ID that this item belongs to, if
            any.
        extra_fields (dict or None): Extra fields that are part of the top-level JSON
            properties of the Item.
    """

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
            href (str): The absolute HREF of this object. If the given HREF
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
        if asset is None or "datetime" not in asset.properties:
            return self.datetime
        else:
            asset_dt = asset.properties.get("datetime")
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
            asset.properties["datetime"] = datetime_to_str(datetime)

    def get_assets(self) -> Dict[str, Asset]:
        """Get this item's assets.

        Returns:
            Dict[str, Asset]: A copy of the dictionary of this item's assets.
        """
        return dict(self.assets.items())

    def add_asset(self, key: str, asset: Asset) -> None:
        """Adds an Asset to this item.

        Args:
            key (str): The unique key of this asset.
            asset (Asset): The Asset to add.
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
            collection (Collection or None): The collection to set as this
                item's collection. If None, will clear the collection.

        Returns:
            Item: self
        """
        self.remove_links("collection")
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
        collection_link = self.get_single_link("collection")
        if collection_link is None:
            return None
        else:
            return cast(Collection, collection_link.resolve_stac_object().target)

    def to_dict(self, include_self_link: bool = True) -> Dict[str, Any]:
        links = self.links
        if not include_self_link:
            links = [x for x in links if x.rel != "self"]

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
        clone = Item(
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

    def _object_links(self) -> List[str]:
        return ["collection"] + (pystac.EXTENSION_HOOKS.get_extended_object_links(self))

    @classmethod
    def from_dict(
        cls,
        d: Dict[str, Any],
        href: Optional[str] = None,
        root: Optional[Catalog] = None,
        migrate: bool = False,
    ) -> "Item":
        if migrate:
            result = pystac.read_dict(d, href=href, root=root)
            if not isinstance(result, Item):
                raise pystac.STACError(f"{result} is not a Catalog")
            return result

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
            has_self_link |= link["rel"] == "self"
            item.add_link(Link.from_dict(link))

        if not has_self_link and href is not None:
            item.add_link(Link.self_href(href))

        for k, v in assets.items():
            asset = Asset.from_dict(v)
            asset.set_owner(item)
            item.assets[k] = asset

        return item

    @property
    def common_metadata(self) -> CommonMetadata:
        """Access the item's common metadat fields as a CommonMetadata object

        Returns:
            CommonMetada: contains all common metadata fields in the items properties
        """
        return CommonMetadata(self.properties)

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
