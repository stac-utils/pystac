"""Implements the Electro-Optical (EO) extension.

https://github.com/stac-extensions/eo
"""

import re
from typing import Any, Dict, Generic, List, Optional, Set, Tuple, TypeVar, cast

import pystac
from pystac.collection import RangeSummary
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.extensions import view
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.utils import get_required, map_opt

T = TypeVar("T", pystac.Item, pystac.Asset)

SCHEMA_URI = "https://stac-extensions.github.io/eo/v1.0.0/schema.json"

BANDS_PROP = "eo:bands"
CLOUD_COVER_PROP = "eo:cloud_cover"


class Band:
    """Represents Band information attached to an Item that implements the eo extension.

    Use Band.create to create a new Band.
    """

    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    def apply(
        self,
        name: str,
        common_name: Optional[str] = None,
        description: Optional[str] = None,
        center_wavelength: Optional[float] = None,
        full_width_half_max: Optional[float] = None,
    ) -> None:
        """
        Sets the properties for this Band.

        Args:
            name (str): The name of the band (e.g., "B01", "B02", "B1", "B5", "QA").
            common_name (str): The name commonly used to refer to the band to make it
                easier to search for bands across instruments. See the `list of
                accepted common names <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/eo#common-band-names>`_.
            description (str): Description to fully explain the band.
            center_wavelength (float): The center wavelength of the band, in micrometers (μm).
            full_width_half_max (float): Full width at half maximum (FWHM). The width of the band,
                as measured at half the maximum transmission, in micrometers (μm).
        """  # noqa
        self.name = name
        self.common_name = common_name
        self.description = description
        self.center_wavelength = center_wavelength
        self.full_width_half_max = full_width_half_max

    @classmethod
    def create(
        cls,
        name: str,
        common_name: Optional[str] = None,
        description: Optional[str] = None,
        center_wavelength: Optional[float] = None,
        full_width_half_max: Optional[float] = None,
    ) -> "Band":
        """
        Creates a new band.

        Args:
            name (str): The name of the band (e.g., "B01", "B02", "B1", "B5", "QA").
            common_name (str): The name commonly used to refer to the band to make it easier
                to search for bands across instruments. See the `list of accepted common names
                <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/eo#common-band-names>`_.
            description (str): Description to fully explain the band.
            center_wavelength (float): The center wavelength of the band, in micrometers (μm).
            full_width_half_max (float): Full width at half maximum (FWHM). The width of the band,
                as measured at half the maximum transmission, in micrometers (μm).
        """  # noqa
        b = cls({})
        b.apply(
            name=name,
            common_name=common_name,
            description=description,
            center_wavelength=center_wavelength,
            full_width_half_max=full_width_half_max,
        )
        return b

    @property
    def name(self) -> str:
        """Get or sets the name of the band (e.g., "B01", "B02", "B1", "B5", "QA").

        Returns:
            str
        """
        return get_required(self.properties["name"], self, "name")

    @name.setter
    def name(self, v: str) -> None:
        self.properties["name"] = v

    @property
    def common_name(self) -> Optional[str]:
        """Get or sets the name commonly used to refer to the band to make it easier
            to search for bands across instruments. See the `list of accepted common names
            <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/eo#common-band-names>`_.

        Returns:
            Optional[str]
        """  # noqa
        return self.properties.get("common_name")

    @common_name.setter
    def common_name(self, v: Optional[str]) -> None:
        if v is not None:
            self.properties["common_name"] = v
        else:
            self.properties.pop("common_name", None)

    @property
    def description(self) -> Optional[str]:
        """Get or sets the description to fully explain the band. CommonMark 0.29 syntax MAY be
        used for rich text representation.

        Returns:
            str
        """
        return self.properties.get("description")

    @description.setter
    def description(self, v: Optional[str]) -> None:
        if v is not None:
            self.properties["description"] = v
        else:
            self.properties.pop("description", None)

    @property
    def center_wavelength(self) -> Optional[float]:
        """Get or sets the center wavelength of the band, in micrometers (μm).

        Returns:
            float
        """
        return self.properties.get("center_wavelength")

    @center_wavelength.setter
    def center_wavelength(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties["center_wavelength"] = v
        else:
            self.properties.pop("center_wavelength", None)

    @property
    def full_width_half_max(self) -> Optional[float]:
        """Get or sets the full width at half maximum (FWHM). The width of the band,
            as measured at half the maximum transmission, in micrometers (μm).

        Returns:
            [float]
        """
        return self.properties.get("full_width_half_max")

    @full_width_half_max.setter
    def full_width_half_max(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties["full_width_half_max"] = v
        else:
            self.properties.pop("full_width_half_max", None)

    def __repr__(self) -> str:
        return "<Band name={}>".format(self.name)

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of this Band.

        Returns:
            dict: The wrapped dict of the Band that can be written out as JSON.
        """
        return self.properties

    @staticmethod
    def band_range(common_name: str) -> Optional[Tuple[float, float]]:
        """Gets the band range for a common band name.

        Args:
            common_name (str): The common band name. Must be one of the `list of accepted common names <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/eo#common-band-names>`_.

        Returns:
            Tuple[float, float] or None: The band range for this name as (min, max), or
            None if this is not a recognized common name.
        """  # noqa E501
        name_to_range = {
            "coastal": (0.40, 0.45),
            "blue": (0.45, 0.50),
            "green": (0.50, 0.60),
            "red": (0.60, 0.70),
            "yellow": (0.58, 0.62),
            "pan": (0.50, 0.70),
            "rededge": (0.70, 0.75),
            "nir": (0.75, 1.00),
            "nir08": (0.75, 0.90),
            "nir09": (0.85, 1.05),
            "cirrus": (1.35, 1.40),
            "swir16": (1.55, 1.75),
            "swir22": (2.10, 2.30),
            "lwir": (10.5, 12.5),
            "lwir11": (10.5, 11.5),
            "lwir12": (11.5, 12.5),
        }

        return name_to_range.get(common_name)

    @staticmethod
    def band_description(common_name: str) -> Optional[str]:
        """Returns a description of the band for one with a common name.

        Args:
            common_name (str): The common band name. Must be one of the `list of accepted common names <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/eo#common-band-names>`_.

        Returns:
            str or None: If a recognized common name, returns a description including the
            band range. Otherwise returns None.
        """  # noqa E501
        r = Band.band_range(common_name)
        if r is not None:
            return "Common name: {}, Range: {} to {}".format(common_name, r[0], r[1])
        return None


class EOExtension(
    Generic[T], PropertiesExtension, ExtensionManagementMixin[pystac.Item]
):
    """EOItemExt is the extension of the Item in the eo extension which
    represents a snapshot of the earth for a single date and time.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The Item that is being extended.

    Note:
        Using EOItemExt to directly wrap an item will add the 'eo' extension ID to
        the item's stac_extensions.
    """

    def apply(self, bands: List[Band], cloud_cover: Optional[float] = None) -> None:
        """Applies label extension properties to the extended Item.

        Args:
            bands (List[Band]): a list of :class:`~pystac.Band` objects that represent
                the available bands.
            cloud_cover (float or None): The estimate of cloud cover as a percentage
                (0-100) of the entire scene. If not available the field should not be
                provided.
        """
        self.bands = bands
        self.cloud_cover = cloud_cover

    @property
    def bands(self) -> Optional[List[Band]]:
        """Get or sets a list of :class:`~pystac.Band` objects that represent
        the available bands.
        """
        return self._get_bands()

    def _get_bands(self) -> Optional[List[Band]]:
        return map_opt(
            lambda bands: [Band(b) for b in bands],
            self._get_property(BANDS_PROP, List[Dict[str, Any]]),
        )

    @bands.setter
    def bands(self, v: Optional[List[Band]]) -> None:
        self._set_property(
            BANDS_PROP, map_opt(lambda bands: [b.to_dict() for b in bands], v)
        )

    @property
    def cloud_cover(self) -> Optional[float]:
        """Get or sets the estimate of cloud cover as a percentage (0-100) of the
            entire scene. If not available the field should not be provided.

        Returns:
            float or None
        """
        return self._get_property(CLOUD_COVER_PROP, float)

    @cloud_cover.setter
    def cloud_cover(self, v: Optional[float]) -> None:
        self._set_property(CLOUD_COVER_PROP, v)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @staticmethod
    def ext(obj: T) -> "EOExtension[T]":
        if isinstance(obj, pystac.Item):
            return cast(EOExtension[T], ItemEOExtension(obj))
        elif isinstance(obj, pystac.Asset):
            return cast(EOExtension[T], AssetEOExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"EO extension does not apply to type {type(obj)}"
            )

    @staticmethod
    def summaries(obj: pystac.Collection) -> "SummariesEOExtension":
        return SummariesEOExtension(obj)


class ItemEOExtension(EOExtension[pystac.Item]):
    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def _get_bands(self) -> Optional[List[Band]]:
        """Get or sets a list of :class:`~pystac.Band` objects that represent
        the available bands.
        """
        bands = self._get_property(BANDS_PROP, List[Dict[str, Any]])

        # get assets with eo:bands even if not in item
        if bands is None:
            asset_bands: List[Dict[str, Any]] = []
            for _, value in self.item.get_assets().items():
                if BANDS_PROP in value.properties:
                    asset_bands.extend(
                        cast(List[Dict[str, Any]], value.properties.get(BANDS_PROP))
                    )
            if any(asset_bands):
                bands = asset_bands

        if bands is not None:
            return [Band(b) for b in bands]
        return None

    def __repr__(self) -> str:
        return "<ItemEOExtension Item id={}>".format(self.item.id)


class AssetEOExtension(EOExtension[pystac.Asset]):
    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.properties
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return "<AssetEOExtension Item id={}>".format(self.asset_href)


class SummariesEOExtension(SummariesExtension):
    @property
    def bands(self) -> Optional[List[Band]]:
        """Get or sets a list of :class:`~pystac.Band` objects that represent
        the available bands.
        """
        return map_opt(
            lambda bands: [Band(b) for b in bands],
            self.summaries.get_list(BANDS_PROP, Dict[str, Any]),
        )

    @bands.setter
    def bands(self, v: Optional[List[Band]]) -> None:
        self._set_summary(BANDS_PROP, map_opt(lambda x: [b.to_dict() for b in x], v))

    @property
    def cloud_cover(self) -> Optional[RangeSummary[float]]:
        """Get or sets the range of cloud cover from the summary."""
        return self.summaries.get_range(CLOUD_COVER_PROP, float)

    @cloud_cover.setter
    def cloud_cover(self, v: Optional[RangeSummary[float]]) -> None:
        self._set_summary(CLOUD_COVER_PROP, v)


class EOExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: Set[str] = set(["eo"])
    stac_object_types: Set[pystac.STACObjectType] = set([pystac.STACObjectType.ITEM])

    def migrate(
        self, obj: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        if version < "0.5":
            if "eo:crs" in obj["properties"]:
                # Try to pull out the EPSG code.
                # Otherwise, just leave it alone.
                wkt = obj["properties"]["eo:crs"]
                matches = list(re.finditer(r'AUTHORITY\[[^\]]*\"(\d+)"\]', wkt))
                if len(matches) > 0:
                    epsg_code = matches[-1].group(1)
                    obj["properties"].pop("eo:crs")
                    obj["properties"]["eo:epsg"] = int(epsg_code)

        if version < "0.6":
            # Change eo:bands from a dict to a list. eo:bands on an asset
            # is an index instead of a dict key. eo:bands is in properties.
            bands_dict = obj["eo:bands"]
            keys_to_indices: Dict[str, int] = {}
            bands: List[Dict[str, Any]] = []
            for i, (k, band) in enumerate(bands_dict.items()):
                keys_to_indices[k] = i
                bands.append(band)

            obj.pop("eo:bands")
            obj["properties"]["eo:bands"] = bands
            for k, asset in obj["assets"].items():
                if "eo:bands" in asset:
                    asset_band_indices: List[int] = []
                    for bk in asset["eo:bands"]:
                        asset_band_indices.append(keys_to_indices[bk])
                    asset["eo:bands"] = sorted(asset_band_indices)

        if version < "0.9":
            # Some eo fields became common_metadata
            if (
                "eo:platform" in obj["properties"]
                and "platform" not in obj["properties"]
            ):
                obj["properties"]["platform"] = obj["properties"]["eo:platform"]
                del obj["properties"]["eo:platform"]

            if (
                "eo:instrument" in obj["properties"]
                and "instruments" not in obj["properties"]
            ):
                obj["properties"]["instruments"] = [obj["properties"]["eo:instrument"]]
                del obj["properties"]["eo:instrument"]

            if (
                "eo:constellation" in obj["properties"]
                and "constellation" not in obj["properties"]
            ):
                obj["properties"]["constellation"] = obj["properties"][
                    "eo:constellation"
                ]
                del obj["properties"]["eo:constellation"]

            # Some eo fields became view extension fields
            eo_to_view_fields = [
                "off_nadir",
                "azimuth",
                "incidence_angle",
                "sun_azimuth",
                "sun_elevation",
            ]

            for field in eo_to_view_fields:
                if "eo:{}".format(field) in obj["properties"]:
                    if "stac_extensions" not in obj:
                        obj["stac_extensions"] = []
                    if view.SCHEMA_URI not in obj["stac_extensions"]:
                        obj["stac_extensions"].append(view.SCHEMA_URI)
                    if not "view:{}".format(field) in obj["properties"]:
                        obj["properties"]["view:{}".format(field)] = obj["properties"][
                            "eo:{}".format(field)
                        ]
                        del obj["properties"]["eo:{}".format(field)]

        if version < "1.0.0-beta.1" and info.object_type == pystac.STACObjectType.ITEM:
            # gsd moved from eo to common metadata
            if "eo:gsd" in obj["properties"]:
                obj["properties"]["gsd"] = obj["properties"]["eo:gsd"]
                del obj["properties"]["eo:gsd"]

            # The way bands were declared in assets changed.
            # In 1.0.0-beta.1 they are inlined into assets as
            # opposed to having indices back into a property-level array.
            if "eo:bands" in obj["properties"]:
                bands = obj["properties"]["eo:bands"]
                for asset in obj["assets"].values():
                    if "eo:bands" in asset:
                        new_bands: List[Dict[str, Any]] = []
                        for band_index in asset["eo:bands"]:
                            new_bands.append(bands[band_index])
                        asset["eo:bands"] = new_bands

        super().migrate(obj, version, info)


EO_EXTENSION_HOOKS: ExtensionHooks = EOExtensionHooks()
