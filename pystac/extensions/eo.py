"""Implements the :stac-ext:`Electro-Optical Extension <eo>`."""

from __future__ import annotations

from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import pystac
from pystac.extensions import projection, view
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.summaries import RangeSummary
from pystac.utils import get_required, map_opt

T = TypeVar("T", pystac.Item, pystac.Asset)

SCHEMA_URI: str = "https://stac-extensions.github.io/eo/v1.0.0/schema.json"
PREFIX: str = "eo:"

# Field names
BANDS_PROP: str = PREFIX + "bands"
CLOUD_COVER_PROP: str = PREFIX + "cloud_cover"


class Band:
    """Represents Band information attached to an Item that implements the eo extension.

    Use :meth:`Band.create` to create a new Band.
    """

    properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    def apply(
        self,
        name: str,
        common_name: Optional[str] = None,
        description: Optional[str] = None,
        center_wavelength: Optional[float] = None,
        full_width_half_max: Optional[float] = None,
        solar_illumination: Optional[float] = None,
    ) -> None:
        """
        Sets the properties for this Band.

        Args:
            name : The name of the band (e.g., "B01", "B02", "B1", "B5", "QA").
            common_name : The name commonly used to refer to the band to make it
                easier to search for bands across instruments. See the :stac-ext:`list
                of accepted common names <eo#common-band-names>`.
            description : Description to fully explain the band.
            center_wavelength : The center wavelength of the band, in micrometers (μm).
            full_width_half_max : Full width at half maximum (FWHM). The width of the
                band, as measured at half the maximum transmission, in micrometers (μm).
            solar_illumination: The solar illumination of the band,
                as measured at half the maximum transmission, in W/m2/micrometers.
        """
        self.name = name
        self.common_name = common_name
        self.description = description
        self.center_wavelength = center_wavelength
        self.full_width_half_max = full_width_half_max
        self.solar_illumination = solar_illumination

    @classmethod
    def create(
        cls,
        name: str,
        common_name: Optional[str] = None,
        description: Optional[str] = None,
        center_wavelength: Optional[float] = None,
        full_width_half_max: Optional[float] = None,
        solar_illumination: Optional[float] = None,
    ) -> Band:
        """
        Creates a new band.

        Args:
            name : The name of the band (e.g., "B01", "B02", "B1", "B5", "QA").
            common_name : The name commonly used to refer to the band to make it easier
                to search for bands across instruments. See the :stac-ext:`list of
                accepted common names <eo#common-band-names>`.
            description : Description to fully explain the band.
            center_wavelength : The center wavelength of the band, in micrometers (μm).
            full_width_half_max : Full width at half maximum (FWHM). The width of the
                band, as measured at half the maximum transmission, in micrometers (μm).
            solar_illumination: The solar illumination of the band,
                as measured at half the maximum transmission, in W/m2/micrometers.
        """
        b = cls({})
        b.apply(
            name=name,
            common_name=common_name,
            description=description,
            center_wavelength=center_wavelength,
            full_width_half_max=full_width_half_max,
            solar_illumination=solar_illumination,
        )
        return b

    @property
    def name(self) -> str:
        """Get or sets the name of the band (e.g., "B01", "B02", "B1", "B5", "QA").

        Returns:
            str
        """
        return get_required(self.properties.get("name"), self, "name")

    @name.setter
    def name(self, v: str) -> None:
        self.properties["name"] = v

    @property
    def common_name(self) -> Optional[str]:
        """Get or sets the name commonly used to refer to the band to make it easier
            to search for bands across instruments. See the :stac-ext:`list of accepted
            common names <eo#common-band-names>`.

        Returns:
            Optional[str]
        """
        return self.properties.get("common_name")

    @common_name.setter
    def common_name(self, v: Optional[str]) -> None:
        if v is not None:
            self.properties["common_name"] = v
        else:
            self.properties.pop("common_name", None)

    @property
    def description(self) -> Optional[str]:
        """Get or sets the description to fully explain the band. CommonMark 0.29
        syntax MAY be used for rich text representation.

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

    @property
    def solar_illumination(self) -> Optional[float]:
        """Get or sets the solar illumination of the band,
            as measured at half the maximum transmission, in W/m2/micrometers.

        Returns:
            [float]
        """
        return self.properties.get("solar_illumination")

    @solar_illumination.setter
    def solar_illumination(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties["solar_illumination"] = v
        else:
            self.properties.pop("solar_illumination", None)

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
            common_name : The common band name. Must be one of the :stac-ext:`list of
                accepted common names <eo#common-band-names>`.

        Returns:
            Tuple[float, float] or None: The band range for this name as (min, max), or
            None if this is not a recognized common name.
        """
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
            common_name : The common band name. Must be one of the :stac-ext:`list of
                accepted common names <eo#common-band-names>`.

        Returns:
            str or None: If a recognized common name, returns a description including
            the band range. Otherwise returns None.
        """
        r = Band.band_range(common_name)
        if r is not None:
            return "Common name: {}, Range: {} to {}".format(common_name, r[0], r[1])
        return None


class EOExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Union[pystac.Item, pystac.Collection]],
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Item` or :class:`~pystac.Asset` with properties from the
    :stac-ext:`Electro-Optical Extension <eo>`. This class is generic over the type of
    STAC Object to be extended (e.g. :class:`~pystac.Item`,
    :class:`~pystac.Asset`).

    To create a concrete instance of :class:`EOExtension`, use the
    :meth:`EOExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> eo_ext = EOExtension.ext(item)
    """

    def apply(
        self, bands: Optional[List[Band]] = None, cloud_cover: Optional[float] = None
    ) -> None:
        """Applies Electro-Optical Extension properties to the extended
        :class:`~pystac.Item` or :class:`~pystac.Asset`.

        Args:
            bands : A list of available bands where each item is a :class:`~Band`
                object. If given, requires at least one band.
            cloud_cover : The estimate of cloud cover as a percentage
                (0-100) of the entire scene. If not available the field should not
                be provided.
        """
        self.bands = bands
        self.cloud_cover = cloud_cover

    @property
    def bands(self) -> Optional[List[Band]]:
        """Gets or sets a list of available bands where each item is a :class:`~Band`
        object (or ``None`` if no bands have been set). If not available the field
        should not be provided.
        """
        return self._get_bands()

    @bands.setter
    def bands(self, v: Optional[List[Band]]) -> None:
        self._set_property(
            BANDS_PROP, map_opt(lambda bands: [b.to_dict() for b in bands], v)
        )

    def _get_bands(self) -> Optional[List[Band]]:
        return map_opt(
            lambda bands: [Band(b) for b in bands],
            self._get_property(BANDS_PROP, List[Dict[str, Any]]),
        )

    @property
    def cloud_cover(self) -> Optional[float]:
        """Get or sets the estimate of cloud cover as a percentage
        (0-100) of the entire scene. If not available the field should not be provided.

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

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> EOExtension[T]:
        """Extends the given STAC Object with properties from the
        :stac-ext:`Electro-Optical Extension <eo>`.

        This extension can be applied to instances of :class:`~pystac.Item` or
        :class:`~pystac.Asset`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Item):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(EOExtension[T], ItemEOExtension(obj))
        elif isinstance(obj, pystac.Asset):
            cls.validate_owner_has_extension(obj, add_if_missing)
            return cast(EOExtension[T], AssetEOExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"EO extension does not apply to type '{type(obj).__name__}'"
            )

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesEOExtension:
        """Returns the extended summaries object for the given collection."""
        cls.validate_has_extension(obj, add_if_missing)
        return SummariesEOExtension(obj)


class ItemEOExtension(EOExtension[pystac.Item]):
    """A concrete implementation of :class:`EOExtension` on an :class:`~pystac.Item`
    that extends the properties of the Item to include properties defined in the
    :stac-ext:`Electro-Optical Extension <eo>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`EOExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: pystac.Item
    """The :class:`~pystac.Item` being extended."""

    properties: Dict[str, Any]
    """The :class:`~pystac.Item` properties, including extension properties."""

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
                if BANDS_PROP in value.extra_fields:
                    asset_bands.extend(
                        cast(List[Dict[str, Any]], value.extra_fields.get(BANDS_PROP))
                    )
            if any(asset_bands):
                bands = asset_bands

        if bands is not None:
            return [Band(b) for b in bands]
        return None

    def __repr__(self) -> str:
        return "<ItemEOExtension Item id={}>".format(self.item.id)


class AssetEOExtension(EOExtension[pystac.Asset]):
    """A concrete implementation of :class:`EOExtension` on an :class:`~pystac.Asset`
    that extends the Asset fields to include properties defined in the
    :stac-ext:`Electro-Optical Extension <eo>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`EOExtension.ext` on an :class:`~pystac.Asset` to extend it.
    """

    asset_href: str
    """The ``href`` value of the :class:`~pystac.Asset` being extended."""

    properties: Dict[str, Any]
    """The :class:`~pystac.Asset` fields, including extension properties."""

    additional_read_properties: Optional[Iterable[Dict[str, Any]]] = None
    """If present, this will be a list containing 1 dictionary representing the
    properties of the owning :class:`~pystac.Item`."""

    def _get_bands(self) -> Optional[List[Band]]:
        if BANDS_PROP not in self.properties:
            return None
        return list(
            map(
                lambda band: Band(band),
                cast(List[Dict[str, Any]], self.properties.get(BANDS_PROP)),
            )
        )

    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return "<AssetEOExtension Asset href={}>".format(self.asset_href)


class SummariesEOExtension(SummariesExtension):
    """A concrete implementation of :class:`~SummariesExtension` that extends
    the ``summaries`` field of a :class:`~pystac.Collection` to include properties
    defined in the :stac-ext:`Electro-Optical Extension <eo>`.
    """

    @property
    def bands(self) -> Optional[List[Band]]:
        """Get or sets the summary of :attr:`EOExtension.bands` values
        for this Collection.
        """

        return map_opt(
            lambda bands: [Band(b) for b in bands],
            self.summaries.get_list(BANDS_PROP),
        )

    @bands.setter
    def bands(self, v: Optional[List[Band]]) -> None:
        self._set_summary(BANDS_PROP, map_opt(lambda x: [b.to_dict() for b in x], v))

    @property
    def cloud_cover(self) -> Optional[RangeSummary[float]]:
        """Get or sets the summary of :attr:`EOExtension.cloud_cover` values
        for this Collection.
        """
        return self.summaries.get_range(CLOUD_COVER_PROP)

    @cloud_cover.setter
    def cloud_cover(self, v: Optional[RangeSummary[float]]) -> None:
        self._set_summary(CLOUD_COVER_PROP, v)


class EOExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"eo"}
    stac_object_types = {pystac.STACObjectType.ITEM}

    def migrate(
        self, obj: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
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
                    if "view:{}".format(field) not in obj["properties"]:
                        obj["properties"]["view:{}".format(field)] = obj["properties"][
                            "eo:{}".format(field)
                        ]
                        del obj["properties"]["eo:{}".format(field)]

            # eo:epsg became proj:epsg
            eo_epsg = PREFIX + "epsg"
            proj_epsg = projection.PREFIX + "epsg"
            if eo_epsg in obj["properties"] and proj_epsg not in obj["properties"]:
                obj["properties"][proj_epsg] = obj["properties"].pop(eo_epsg)
                obj["stac_extensions"] = obj.get("stac_extensions", [])
                if (
                    projection.ProjectionExtension.get_schema_uri()
                    not in obj["stac_extensions"]
                ):
                    obj["stac_extensions"].append(
                        projection.ProjectionExtension.get_schema_uri()
                    )
                if not any(prop.startswith(PREFIX) for prop in obj["properties"]):
                    obj["stac_extensions"].remove(EOExtension.get_schema_uri())

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
