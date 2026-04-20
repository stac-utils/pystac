"""Implements the :stac-ext:`Electro-Optical Extension <eo>`."""

from __future__ import annotations

import warnings
from collections import Counter
from collections.abc import Iterable
from typing import (
    Any,
    Generic,
    Literal,
    TypeVar,
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
from pystac.utils import StringEnum


def __getattr__(name: str) -> object:
    if name == "Band":
        warnings.warn(
            "eo.Band is deprecated and will be removed in v2.0. "
            "Use pystac.Band with band.ext.eo for spectral fields instead:\n"
            "  band = pystac.Band.create('B01')\n"
            "  band.ext.eo.common_name = 'red'\n"
            "  band.ext.eo.center_wavelength = 0.65",
            DeprecationWarning,
            stacklevel=2,
        )
        from pystac import Band

        return Band
    raise AttributeError(f"module 'pystac.extensions.eo' has no attribute {name!r}")


#: Generalized version of :class:`~pystac.Item`, :class:`~pystac.Asset`,
#: pr :class:`~pystac.ItemAssetDefinition`
T = TypeVar("T", pystac.Item, pystac.Asset, pystac.ItemAssetDefinition, pystac.Band)

SCHEMA_URI: str = "https://stac-extensions.github.io/eo/v2.0.0/schema.json"
SCHEMA_URIS: list[str] = [
    "https://stac-extensions.github.io/eo/v1.1.0/schema.json",
    "https://stac-extensions.github.io/eo/v1.0.0/schema.json",
    SCHEMA_URI,
]
PREFIX: str = "eo:"

# Field names
BANDS_PROP: str = PREFIX + "bands"  # Deprecated
CLOUD_COVER_PROP: str = PREFIX + "cloud_cover"
SNOW_COVER_PROP: str = PREFIX + "snow_cover"
COMMON_NAME_PROP: str = PREFIX + "common_name"
CENTER_WAVELENGTH_PROP: str = PREFIX + "center_wavelength"
FULL_WIDTH_HALF_MAX_PROP: str = PREFIX + "full_width_half_max"
SOLAR_ILLUMINATION_PROP: str = PREFIX + "solar_illumination"


def validated_percentage(v: float | None) -> float | None:
    if v is not None and not isinstance(v, (float, int)) or isinstance(v, bool):
        raise ValueError(f"Invalid percentage: {v} must be number")
    if v is not None and not 0 <= v <= 100:
        raise ValueError(f"Invalid percentage: {v} must be between 0 and 100")
    return v


class EOCommonName(StringEnum):
    PAN = "pan"
    COASTAL = "coastal"
    BLUE = "blue"
    GREEN = "green"
    GREEN05 = "green05"
    YELLOW = "yellow"
    RED = "red"
    REDEDGE = "rededge"
    REDEDGE071 = "rededge071"
    REDEDGE075 = "rededge075"
    REDEDGE078 = "rededge078"
    NIR = "nir"
    NIR08 = "nir08"
    NIR09 = "nir09"
    CIRRUS = "cirrus"
    SWIR16 = "swir16"
    SWIR22 = "swir22"
    LWIR = "lwir"
    LWIR11 = "lwir11"
    LWIR12 = "lwir12"


def band_range(common_name: EOCommonName) -> tuple[float, float] | None:
    """Gets the band range for a common band name.
    Args:
        common_name : The common band name. Must be one of the :stac-ext:`list of
            accepted common names <eo#common-band-names>`.
    Returns:
        Tuple[float, float] or None: The band range for this name as (min, max), or
        None if this is not a recognized common name.
    """
    name_to_range = {
        "pan": (0.40, 1.00),
        "coastal": (0.40, 0.45),
        "blue": (0.45, 0.53),
        "green": (0.51, 0.60),
        "green05": (0.51, 0.55),
        "yellow": (0.58, 0.62),
        "red": (0.62, 0.69),
        "rededge": (0.69, 0.79),
        "rededge071": (0.69, 0.73),
        "rededge075": (0.73, 0.76),
        "rededge078": (0.76, 0.79),
        "nir": (0.76, 1.00),
        "nir08": (0.80, 0.90),
        "nir09": (0.90, 1.00),
        "cirrus": (1.35, 1.40),
        "swir16": (1.55, 1.75),
        "swir22": (2.08, 2.35),
        "lwir": (10.4, 12.5),
        "lwir11": (10.5, 11.5),
        "lwir12": (11.5, 12.5),
    }

    return name_to_range.get(common_name)


def band_description(common_name: EOCommonName) -> str | None:
    """Returns a description of the band for one with a common name.
    Args:
        common_name : The common band name. Must be one of the :stac-ext:`list of
            accepted common names <eo#common-band-names>`.
    Returns:
        str or None: If a recognized common name, returns a description including
        the band range. Otherwise, returns None.
    """
    r = band_range(common_name)
    if r is not None:
        return f"Common name: {common_name}, Range: {r[0]} to {r[1]}"
    return None


class EOExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
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

    name: Literal["eo"] = "eo"

    def apply(
        self,
        cloud_cover: float | None = None,
        snow_cover: float | None = None,
        # These are meant to be applied on a `pystac.Band` instance
        common_name: EOCommonName | None = None,
        center_wavelength: float | None = None,
        full_width_half_max: float | None = None,
        solar_illumination: float | None = None,
    ) -> None:
        """Applies Electro-Optical Extension properties to the extended
        :class:`~pystac.Item` or :class:`~pystac.Asset`.

        Args:
            cloud_cover : The estimate of cloud cover as a percentage
                (0-100) of the entire scene. If not available the field should not
                be provided.
            snow_cover : The estimate of snow cover as a percentage
                (0-100) of the entire scene. If not available the field should not
                be provided.
            common_name : The name commonly used to refer to the band to make it
                easier to search for bands across instruments. Must be an accepted
                common name from `EOCommonName`
            center_wavelength : The center wavelength of the band, in micrometers (μm).
            full_width_half_max : Full width at half maximum (FWHM). The width of the
                band, as measured at half the maximum transmission, in micrometers (μm).
            solar_illumination : The solar illumination of the band, as measured at
                half the maximum transmission, in W/m2/micrometers.
        """
        self.cloud_cover = validated_percentage(cloud_cover)
        self.snow_cover = validated_percentage(snow_cover)
        self.common_name = common_name
        self.center_wavelength = center_wavelength
        self.full_width_half_max = full_width_half_max
        self.solar_illumination = solar_illumination

    @property
    def cloud_cover(self) -> float | None:
        """Get or sets the estimate of cloud cover as a percentage
        (0-100) of the entire scene. If not available the field should not be provided.

        Returns:
            float or None
        """
        return self._get_property(CLOUD_COVER_PROP, float)

    @cloud_cover.setter
    def cloud_cover(self, v: float | None) -> None:
        self._set_property(CLOUD_COVER_PROP, validated_percentage(v), pop_if_none=True)

    @property
    def snow_cover(self) -> float | None:
        """Get or sets the estimate of snow cover as a percentage
        (0-100) of the entire scene. If not available the field should not be provided.

        Returns:
            float or None
        """
        return self._get_property(SNOW_COVER_PROP, float)

    @snow_cover.setter
    def snow_cover(self, v: float | None) -> None:
        self._set_property(SNOW_COVER_PROP, validated_percentage(v), pop_if_none=True)

    # common_name
    @property
    def common_name(self) -> EOCommonName | None:
        """Gets or sets the name commonly used to refer to the band to make it
        easier to search for bands across instruments. Must be an accepted
        common name from `EOCommonName`:

        - pan
        - coastal
        - blue
        - green
        - green05
        - yellow
        - red
        - rededge
        - rededge071
        - rededge075
        - rededge078
        - nir
        - nir08
        - nir09
        - cirrus
        - swir16
        - swir22
        - lwir
        - lwir11
        - lwir12

        Raises:
            pystac.ExtensionTypeError

        Returns:
            EOCommonName or None
        """
        return self._get_property(COMMON_NAME_PROP, EOCommonName)

    @common_name.setter
    def common_name(self, v: EOCommonName | None) -> None:
        self._set_property(COMMON_NAME_PROP, v, pop_if_none=True)

    # center_wavelength
    @property
    def center_wavelength(self) -> float | None:
        """Gets or sets The center wavelength of the band, in micrometers (μm).

        Returns:
            float | None
        """
        return self._get_property(CENTER_WAVELENGTH_PROP, float)

    @center_wavelength.setter
    def center_wavelength(self, v: float | None) -> None:
        self._set_property(CENTER_WAVELENGTH_PROP, v, pop_if_none=True)

    # full_width_half_max
    @property
    def full_width_half_max(self) -> float | None:
        """Gets or sets Full width at half maximum (FWHM). The width of the
        band, as measured at half the maximum transmission, in micrometers (μm).

        Returns:
            float | None
        """
        return self._get_property(FULL_WIDTH_HALF_MAX_PROP, float)

    @full_width_half_max.setter
    def full_width_half_max(self, v: float | None) -> None:
        self._set_property(FULL_WIDTH_HALF_MAX_PROP, v, pop_if_none=True)

    # solar_illumination
    @property
    def solar_illumination(self) -> float | None:
        """Gets or sets the solar illumination of the band, as measured at
        half the maximum transmission, in W/m2/micrometers.

        Returns:
            float | None
        """
        return self._get_property(SOLAR_ILLUMINATION_PROP, float)

    @solar_illumination.setter
    def solar_illumination(self, v: float | None) -> None:
        self._set_property(SOLAR_ILLUMINATION_PROP, v, pop_if_none=True)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def get_schema_uris(cls) -> list[str]:
        import warnings

        warnings.warn(
            "get_schema_uris is deprecated and will be removed in v2",
            DeprecationWarning,
        )
        return SCHEMA_URIS

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
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(EOExtension[T], ItemEOExtension(obj))
        elif isinstance(obj, pystac.Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(EOExtension[T], AssetEOExtension(obj))
        elif isinstance(obj, pystac.ItemAssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(EOExtension[T], ItemAssetsEOExtension(obj))
        elif isinstance(obj, pystac.Band):
            # Band doesn't need owners, for now
            return cast(EOExtension[T], BandEOExtension(obj))
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    # Utils for bands
    def get_bands(self) -> list[EOExtension[pystac.Band]] | None:
        """Returns bands with the EO Extension loaded"""
        pass

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesEOExtension:
        """Returns the extended summaries object for the given collection."""
        cls.ensure_has_extension(obj, add_if_missing)
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

    properties: dict[str, Any]
    """The :class:`~pystac.Item` properties, including extension properties."""

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def get_assets(
        self,
        name: str | None = None,
        common_name: str | None = None,
    ) -> dict[str, pystac.Asset]:
        """Get the item's assets where Bands are defined.

        Args:
            name: If set, filter the assets such that only those with a
                matching ``band.name`` are returned.
            common_name: If set, filter the assets such that only those with a matching
                ``band.eo:common_name`` are returned.

        Returns:
            Dict[str, Asset]: A dictionary of assets that match ``name``
                and/or ``common_name`` if set or else all of this item's assets were
                bands are defined.
        """

        kwargs = {"band_name": name, "common_name": common_name}
        return {
            key: asset
            for key, asset in self.item.get_assets().items()
            if all(
                # If no filter is passed, only retrieve the assets who explicitly have
                # the eo extension
                v is None
                and (
                    any([ka.startswith(PREFIX) for ka in asset.to_dict().keys()])
                    or any(
                        any([kv.startswith(PREFIX) for kv in b.to_dict()])
                        for b in asset.common_metadata.bands or []
                    )
                )
                # If the filters have a value, directly look into the extension
                or (
                    (
                        hasattr(EOExtension.ext(asset), k)
                        and getattr(EOExtension.ext(asset), k) == v
                    )
                    or (
                        EOExtension.ext(asset).get_bands() is not None
                        and any(
                            v == getattr(b, k)
                            for b in EOExtension.ext(asset).get_bands() or []
                        )
                    )
                )
                for k, v in kwargs.items()
            )
        }

    def get_bands(self) -> list[EOExtension[pystac.Band]] | None:
        bands = self.item.common_metadata.bands

        # Look into the assets
        if bands is None:
            asset_bands: list[pystac.Bands] = []
            for _, asset in self.item.get_assets().items():
                current_asset_bands = asset.common_metadata.bands
                if current_asset_bands is not None:
                    asset_bands.extend(current_asset_bands)
            if any(asset_bands):
                bands = asset_bands

        if bands is not None:
            return [EOExtension.ext(b) for b in bands]
        return None

    def __repr__(self) -> str:
        return f"<ItemEOExtension Item id={self.item.id}>"


class AssetEOExtension(EOExtension[pystac.Asset]):
    """A concrete implementation of :class:`EOExtension` on an :class:`~pystac.Asset`
    that extends the Asset fields to include properties defined in the
    :stac-ext:`Electro-Optical Extension <eo>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`EOExtension.ext` on an :class:`~pystac.Asset` to extend it.
    """

    asset_href: str
    """The ``href`` value of the :class:`~pystac.Asset` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Asset` fields, including extension properties."""

    additional_read_properties: Iterable[dict[str, Any]] | None = None
    """If present, this will be a list containing 1 dictionary representing the
    properties of the owning :class:`~pystac.Item`."""

    def get_bands(self) -> list[EOExtension[pystac.Band]] | None:
        if "bands" not in self.properties:
            return None
        return list(
            map(
                lambda band: EOExtension.ext(pystac.Band.from_dict(band)),
                cast(list[dict[str, Any]], self.properties.get("bands")),
            )
        )

    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.common_metadata.bands is not None:
            self.properties["bands"] = [
                b.to_dict() for b in asset.common_metadata.bands
            ]
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return f"<AssetEOExtension Asset href={self.asset_href}>"


class BandEOExtension(EOExtension[pystac.Band]):
    def __init__(self, band: pystac.Band) -> None:
        self.band_name = band.name
        self.description = band.description
        self.properties = band.extra_fields

    def __repr__(self) -> str:
        return f"<BandEOExtension Band name={self.band_name}>"

    # common_name
    @property
    def common_name(self) -> EOCommonName | None:
        """The name commonly used to refer to the band to make it
        easier to search for bands across instruments. Must be an accepted
        common name from `EOCommonName`:

        - pan
        - coastal
        - blue
        - green
        - green05
        - yellow
        - red
        - rededge
        - rededge071
        - rededge075
        - rededge078
        - nir
        - nir08
        - nir09
        - cirrus
        - swir16
        - swir22
        - lwir
        - lwir11
        - lwir12

        Raises:
            pystac.ExtensionTypeError: _description_

        Returns:
            EOCommonName or None
        """
        return self._get_property(COMMON_NAME_PROP, EOCommonName)

    @common_name.setter
    def common_name(self, v: EOCommonName | None) -> None:
        self._set_property(COMMON_NAME_PROP, v, pop_if_none=True)

    # center_wavelength
    @property
    def center_wavelength(self) -> float | None:
        """Gets or sets The center wavelength of the band, in micrometers (μm).

        Returns:
            float | None
        """
        return self._get_property(CENTER_WAVELENGTH_PROP, float)

    @center_wavelength.setter
    def center_wavelength(self, v: float | None) -> None:
        self._set_property(CENTER_WAVELENGTH_PROP, v, pop_if_none=True)

    # full_width_half_max
    @property
    def full_width_half_max(self) -> float | None:
        """Gets or sets Full width at half maximum (FWHM). The width of the
        band, as measured at half the maximum transmission, in micrometers (μm).

        Returns:
            float | None
        """
        return self._get_property(FULL_WIDTH_HALF_MAX_PROP, float)

    @full_width_half_max.setter
    def full_width_half_max(self, v: float | None) -> None:
        self._set_property(FULL_WIDTH_HALF_MAX_PROP, v, pop_if_none=True)

    # solar_illumination
    @property
    def solar_illumination(self) -> float | None:
        """Gets or sets the solar illumination of the band, as measured at
        half the maximum transmission, in W/m2/micrometers.

        Returns:
            float | None
        """
        return self._get_property(SOLAR_ILLUMINATION_PROP, float)

    @solar_illumination.setter
    def solar_illumination(self, v: float | None) -> None:
        self._set_property(SOLAR_ILLUMINATION_PROP, v, pop_if_none=True)


class ItemAssetsEOExtension(EOExtension[pystac.ItemAssetDefinition]):
    properties: dict[str, Any]
    asset_defn: pystac.ItemAssetDefinition

    def get_bands(self) -> list[EOExtension[pystac.Band]] | None:
        if "bands" not in self.properties:
            return None
        return list(
            map(
                lambda band: EOExtension.ext(pystac.Band.from_dict(band)),
                cast(list[dict[str, Any]], self.properties.get("bands")),
            )
        )

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        self.asset_defn = item_asset
        self.properties = item_asset.properties


class SummariesEOExtension(SummariesExtension):
    """A concrete implementation of :class:`~pystac.extensions.base.SummariesExtension`
    that extends the ``summaries`` field of a :class:`~pystac.Collection` to include
    properties defined in the :stac-ext:`Electro-Optical Extension <eo>`.
    """

    def get_bands(self) -> list[EOExtension[pystac.Band]] | None:
        bands = self.summaries.get_list("bands")

        if bands is not None:
            return [EOExtension.ext(pystac.Band.from_dict(b)) for b in bands]

        return None

    @property
    def cloud_cover(self) -> RangeSummary[float] | None:
        """Get or sets the summary of :attr:`EOExtension.cloud_cover` values
        for this Collection.
        """
        return self.summaries.get_range(CLOUD_COVER_PROP)

    @cloud_cover.setter
    def cloud_cover(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(CLOUD_COVER_PROP, v)

    @property
    def snow_cover(self) -> RangeSummary[float] | None:
        """Get or sets the summary of :attr:`EOExtension.snow_cover` values
        for this Collection.
        """
        return self.summaries.get_range(SNOW_COVER_PROP)

    @snow_cover.setter
    def snow_cover(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(SNOW_COVER_PROP, v)


class EOExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {
        "eo",
        *[uri for uri in SCHEMA_URIS if uri != SCHEMA_URI],
    }
    stac_object_types = {pystac.STACObjectType.ITEM}

    def migrate(
        self, obj: dict[str, Any], version: STACVersionID, info: STACJSONDescription
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
                if f"eo:{field}" in obj["properties"]:
                    if "stac_extensions" not in obj:
                        obj["stac_extensions"] = []
                    if view.SCHEMA_URI not in obj["stac_extensions"]:
                        obj["stac_extensions"].append(view.SCHEMA_URI)
                    if f"view:{field}" not in obj["properties"]:
                        obj["properties"][f"view:{field}"] = obj["properties"][
                            f"eo:{field}"
                        ]
                        del obj["properties"][f"eo:{field}"]

            # eo:epsg became proj:epsg in Projection Extension <2.0.0 and became
            # proj:code in Projection Extension 2.0.0
            eo_epsg = PREFIX + "epsg"
            proj_epsg = projection.PREFIX + "epsg"
            proj_code = projection.PREFIX + "code"
            if (
                eo_epsg in obj["properties"]
                and proj_epsg not in obj["properties"]
                and proj_code not in obj["properties"]
            ):
                obj["stac_extensions"] = obj.get("stac_extensions", [])
                if set(obj["stac_extensions"]).intersection(
                    projection.ProjectionExtensionHooks.pre_2
                ):
                    obj["properties"][proj_epsg] = obj["properties"].pop(eo_epsg)
                else:
                    obj["properties"][proj_code] = (
                        f"EPSG:{obj['properties'].pop(eo_epsg)}"
                    )
                    if not projection.ProjectionExtensionHooks().has_extension(obj):
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

            # The way EObands were declared in assets changed.
            # In 1.0.0-beta.1 they are inlined into assets as
            # opposed to having indices back into a property-level array.
            if "eo:bands" in obj["properties"]:
                eo_bands = obj["properties"]["eo:bands"]
                for asset in obj["assets"].values():
                    if "eo:bands" in asset:
                        new_eo_bands: list[dict[str, Any]] = []
                        for band_index in asset["eo:bands"]:
                            new_eo_bands.append(eo_bands[band_index])
                        asset["eo:bands"] = new_eo_bands

        # Bands moved to common metadata
        if version < "2.0.0":
            if "eo:bands" in obj.get("properties", {}):
                old_bands = obj["properties"]["eo:bands"]
                to_be_renamed = [
                    "common_name",
                    "center_wavelength",
                    "full_width_half_max",
                    "solar_illumination",
                ]
                if "bands" not in obj["properties"]:
                    obj["properties"]["bands"] = [
                        {
                            PREFIX + k if k in to_be_renamed else k: v
                            for k, v in band.items()
                        }
                        for band in old_bands
                    ]

                # Bands from Raster already exist and have been processed
                elif "bands" in obj["properties"] and len(
                    obj["properties"]["bands"]
                ) == len(old_bands):
                    for band, old_band in zip(obj["properties"]["bands"], old_bands):
                        band.update(
                            {
                                PREFIX + k if k in to_be_renamed else k: v
                                for k, v in old_band.items()
                            }
                        )

                # If "band" has been instantiated before but needs an update
                else:
                    old_band_names = {band["name"] for band in old_bands}
                    saw_band_names = set()

                    for idx_band, band in enumerate(obj["properties"]["bands"]):
                        band_name = band["name"]
                        if band_name in old_band_names:
                            saw_band_names.add(band_name)
                            old_band = next(
                                b for b in old_bands if b["name"] == band_name
                            )
                            for k, v in old_band.items():
                                new_k = PREFIX + k if k in to_be_renamed else k
                                obj["properties"]["bands"][idx_band][new_k] = v

                    # Add the bands that weren't seen
                    obj["properties"]["bands"].extend(
                        [
                            {
                                PREFIX + k if k in to_be_renamed else k: v
                                for k, v in band.items()
                            }
                            for band in obj["properties"]["eo:bands"]
                            if band["name"] not in saw_band_names
                        ]
                    )

                del obj["properties"]["eo:bands"]
                # Once "bands" is created, identify and remove duplicates
                # Dominant element must be set on the property
                # Minor elements can stay in the bands
                n_elements = len(obj["properties"]["bands"])
                # One band, most metadata goes back up into the asset/item
                if n_elements == 1:
                    for k, v in obj["properties"]["bands"][0].items():
                        if k not in ["name", "description"]:
                            obj["properties"][k] = v

                    obj["properties"]["bands"][0] = {
                        k: v
                        for k, v in obj["properties"]["bands"][0].items()
                        if k not in ["name", "description"]
                    }
                else:
                    counters: dict[str, Counter[Any]] = {
                        PREFIX + eo_field: Counter() for eo_field in to_be_renamed
                    }

                    for band in obj["properties"]["bands"]:
                        for k in counters.keys():
                            # If missing, skip
                            if k in band.keys():
                                counters[k] += Counter([band[k]])

                    for k, v in counters.items():
                        # Element is unique and isn't missing
                        # Move everything up and
                        if len(counters[k]) == 1 and counters[k].total() == n_elements:
                            obj["properties"][k] = list(v)[0]
                            for band in obj["properties"]["bands"]:
                                del band[k]
                        # A dominant element is present
                        elif (
                            0 < len(counters[k]) < n_elements
                            and counters[k].total() == n_elements
                        ):
                            dom_el = counters[k].most_common()[0][0]
                            obj["properties"][k] = dom_el
                            for band in obj["properties"]["bands"]:
                                if band[k] != dom_el:
                                    del band[k]

        super().migrate(obj, version, info)


EO_EXTENSION_HOOKS: ExtensionHooks = EOExtensionHooks()
