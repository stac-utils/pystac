"""Implements the :stac-ext:`Electro-Optical Extension <eo>`."""

from __future__ import annotations

import warnings
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
from pystac.serialization.migrate import (
    has_extension_fields,
    migrate_extension_bands,
)
from pystac.summaries import RangeSummary
from pystac.utils import get_required, map_opt

#: Generalized version of :class:`~pystac.Item`, :class:`~pystac.Asset`,
#: :class:`~pystac.ItemAssetDefinition` or :class:`~pystac.Band`
T = TypeVar("T", pystac.Item, pystac.Asset, pystac.ItemAssetDefinition, pystac.Band)

SCHEMA_URI: str = "https://stac-extensions.github.io/eo/v2.0.0/schema.json"
V1_SCHEMA_URI: str = "https://stac-extensions.github.io/eo/v1.1.0/schema.json"
SCHEMA_URIS: list[str] = [
    "https://stac-extensions.github.io/eo/v1.0.0/schema.json",
    V1_SCHEMA_URI,
    SCHEMA_URI,
]
PREFIX: str = "eo:"

# Field names
BANDS_PROP: str = PREFIX + "bands"
CLOUD_COVER_PROP: str = PREFIX + "cloud_cover"
SNOW_COVER_PROP: str = PREFIX + "snow_cover"
COMMON_NAME_PROP: str = PREFIX + "common_name"
CENTER_WAVELENGTH_PROP: str = PREFIX + "center_wavelength"
FULL_WIDTH_HALF_MAX_PROP: str = PREFIX + "full_width_half_max"
SOLAR_ILLUMINATION_PROP: str = PREFIX + "solar_illumination"
V1_BAND_FIELDS: set[str] = {
    "common_name",
    "center_wavelength",
    "full_width_half_max",
    "solar_illumination",
}


def validated_percentage(v: float | None) -> float | None:
    if v is not None and not isinstance(v, (float, int)) or isinstance(v, bool):
        raise ValueError(f"Invalid percentage: {v} must be number")
    if v is not None and not 0 <= v <= 100:
        raise ValueError(f"Invalid percentage: {v} must be between 0 and 100")
    return v


class Band:
    """Represents Band information attached to an Item that implements the eo extension.

    Use :meth:`Band.create` to create a new Band.
    """

    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]) -> None:
        self.properties = properties

    def apply(
        self,
        name: str,
        common_name: str | None = None,
        description: str | None = None,
        center_wavelength: float | None = None,
        full_width_half_max: float | None = None,
        solar_illumination: float | None = None,
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
        common_name: str | None = None,
        description: str | None = None,
        center_wavelength: float | None = None,
        full_width_half_max: float | None = None,
        solar_illumination: float | None = None,
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
        return cast(str, get_required(self.properties.get("name"), self, "name"))

    @name.setter
    def name(self, v: str) -> None:
        self.properties["name"] = v

    @property
    def common_name(self) -> str | None:
        """Get or sets the name commonly used to refer to the band to make it easier
            to search for bands across instruments. See the :stac-ext:`list of accepted
            common names <eo#common-band-names>`.

        Returns:
            Optional[str]
        """
        return self.properties.get("common_name")

    @common_name.setter
    def common_name(self, v: str | None) -> None:
        if v is not None:
            self.properties["common_name"] = v
        else:
            self.properties.pop("common_name", None)

    @property
    def description(self) -> str | None:
        """Get or sets the description to fully explain the band. CommonMark 0.29
        syntax MAY be used for rich text representation.

        Returns:
            str
        """
        return self.properties.get("description")

    @description.setter
    def description(self, v: str | None) -> None:
        if v is not None:
            self.properties["description"] = v
        else:
            self.properties.pop("description", None)

    @property
    def center_wavelength(self) -> float | None:
        """Get or sets the center wavelength of the band, in micrometers (μm).

        Returns:
            float
        """
        return self.properties.get("center_wavelength")

    @center_wavelength.setter
    def center_wavelength(self, v: float | None) -> None:
        if v is not None:
            self.properties["center_wavelength"] = v
        else:
            self.properties.pop("center_wavelength", None)

    @property
    def full_width_half_max(self) -> float | None:
        """Get or sets the full width at half maximum (FWHM). The width of the band,
            as measured at half the maximum transmission, in micrometers (μm).

        Returns:
            [float]
        """
        return self.properties.get("full_width_half_max")

    @full_width_half_max.setter
    def full_width_half_max(self, v: float | None) -> None:
        if v is not None:
            self.properties["full_width_half_max"] = v
        else:
            self.properties.pop("full_width_half_max", None)

    @property
    def solar_illumination(self) -> float | None:
        """Get or sets the solar illumination of the band,
            as measured at half the maximum transmission, in W/m2/micrometers.

        Returns:
            [float]
        """
        return self.properties.get("solar_illumination")

    @solar_illumination.setter
    def solar_illumination(self, v: float | None) -> None:
        if v is not None:
            self.properties["solar_illumination"] = v
        else:
            self.properties.pop("solar_illumination", None)

    def __repr__(self) -> str:
        return f"<Band name={self.properties.get('name')}>"

    def to_dict(self) -> dict[str, Any]:
        """Returns this band as a dictionary.

        Returns:
            dict: The serialization of this Band.
        """
        return self.properties

    @staticmethod
    def band_range(common_name: str) -> tuple[float, float] | None:
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
    def band_description(common_name: str) -> str | None:
        """Returns a description of the band for one with a common name.

        Args:
            common_name : The common band name. Must be one of the :stac-ext:`list of
                accepted common names <eo#common-band-names>`.

        Returns:
            str or None: If a recognized common name, returns a description including
            the band range. Otherwise, returns None.
        """
        r = Band.band_range(common_name)
        if r is not None:
            return f"Common name: {common_name}, Range: {r[0]} to {r[1]}"
        return None


_BANDS_REPLACEMENT = (
    "the bands of the Item, Asset or ItemAssetDefinition with EOExtension.ext(band)"
)
_SUMMARY_REPLACEMENT = "the bands summary with eo: prefixed fields"


def _warn_v1_bands_deprecated(name: str, replacement: str) -> None:
    warnings.warn(
        f"{name} is deprecated and will be removed in a future version. "
        f"Use {replacement} instead.",
        DeprecationWarning,
        stacklevel=3,
    )


def _own_bands(asset: pystac.Asset) -> list[pystac.Band] | None:
    bands = asset.bands
    if asset.owner is not None and bands is asset.owner.bands:
        return None
    return bands


def _to_v1_bands(bands: list[pystac.Band] | None) -> list[Band] | None:
    """Converts common bands to v1.1 :class:`Band` copies, or returns ``None`` if
    none of the bands has a ``name``, ``description`` or ``eo:`` field."""
    if not bands or not any(
        band.name is not None
        or band.description is not None
        or any(k.startswith(PREFIX) for k in band.extra_fields)
        for band in bands
    ):
        return None
    v1_bands = []
    for band in bands:
        properties = {
            k.removeprefix(PREFIX): v
            for k, v in band.extra_fields.items()
            if k.startswith(PREFIX)
        }
        if band.description is not None:
            properties = {"description": band.description, **properties}
        if band.name is not None:
            properties = {"name": band.name, **properties}
        v1_bands.append(Band(properties))
    return v1_bands


def _from_v1_bands(
    bands: list[Band], existing: list[pystac.Band] | None
) -> list[pystac.Band]:
    """Converts v1.1 :class:`Band` objects to common bands with ``eo:`` fields.

    If ``existing`` has as many bands, its fields other than ``name``,
    ``description`` and ``eo:`` fields are kept, by index.
    """
    new = [
        {PREFIX + k if k in V1_BAND_FIELDS else k: v for k, v in band.to_dict().items()}
        for band in bands
    ]
    if existing is not None and len(existing) == len(new):
        new = [
            {
                **{
                    k: v
                    for k, v in old.to_dict().items()
                    if k not in {"name", "description"} and not k.startswith(PREFIX)
                },
                **band,
            }
            for old, band in zip(existing, new)
        ]
    return [pystac.Band.from_dict(band) for band in new]


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
        bands: list[Band] | None = None,
        cloud_cover: float | None = None,
        snow_cover: float | None = None,
    ) -> None:
        """Applies Electro-Optical Extension properties to the extended
        :class:`~pystac.Item` or :class:`~pystac.Asset`.

        Args:
            bands : Deprecated, see :attr:`bands`. A list of available bands where
                each item is a :class:`~Band` object. If given, requires at least one
                band.
            cloud_cover : The estimate of cloud cover as a percentage
                (0-100) of the entire scene. If not available the field should not
                be provided.
            snow_cover : The estimate of snow cover as a percentage
                (0-100) of the entire scene. If not available the field should not
                be provided.
        """
        if bands is not None:
            _warn_v1_bands_deprecated(
                "The bands argument of EOExtension.apply", _BANDS_REPLACEMENT
            )
        self._set_bands(bands)
        self.cloud_cover = validated_percentage(cloud_cover)
        self.snow_cover = validated_percentage(snow_cover)

    @property
    def bands(self) -> list[Band] | None:
        """Gets or sets a list of available bands where each item is a :class:`~Band`
        object (or ``None`` if no bands have been set). If not available the field
        should not be provided.

        .. deprecated:: 2.0.0
            eo v2.0.0 removed ``eo:bands``. Use the ``bands`` of the
            :class:`~pystac.Item`, :class:`~pystac.Asset` or
            :class:`~pystac.ItemAssetDefinition` with ``EOExtension.ext(band)``.

        Reads ``eo:bands`` (eo v1) if it is set. Otherwise, returns copies of the
        object's own common bands (e.g. :attr:`~pystac.Asset.bands`, not inherited
        from its owner) if they have a ``name``, ``description`` or ``eo:`` field
        (eo v2); changes to those copies are not kept.

        Setting this property on an Item, Asset or Item Asset Definition writes the
        common bands, with ``eo:`` prefixed fields, and removes ``eo:bands``. If
        there already are as many common bands, their non-eo fields are kept.
        Setting ``None`` only removes ``eo:bands``.
        """
        _warn_v1_bands_deprecated("EOExtension.bands", _BANDS_REPLACEMENT)
        return self._get_bands()

    @bands.setter
    def bands(self, v: list[Band] | None) -> None:
        _warn_v1_bands_deprecated("EOExtension.bands", _BANDS_REPLACEMENT)
        self._set_bands(v)

    def _set_bands(self, v: list[Band] | None) -> None:
        if v is None or not self._has_common_bands:
            self._set_property(
                BANDS_PROP, map_opt(lambda bands: [b.to_dict() for b in bands], v)
            )
            return
        self._set_property(BANDS_PROP, None)
        self._set_common_bands(_from_v1_bands(v, self._get_common_bands()))

    _has_common_bands: bool = False

    def _get_common_bands(self) -> list[pystac.Band] | None:
        return None

    def _set_common_bands(self, bands: list[pystac.Band]) -> None:
        raise NotImplementedError

    def _get_bands(self) -> list[Band] | None:
        bands = self._get_property(BANDS_PROP, list[dict[str, Any]])
        if bands is not None:
            return [Band(b) for b in bands]
        return _to_v1_bands(self._get_common_bands())

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

    @property
    def common_name(self) -> str | None:
        """Get or sets the name commonly used to refer to the band to make it easier
        to search for bands across instruments. See the :stac-ext:`list of accepted
        common names <eo#common-band-names>`.
        """
        return self._get_property(COMMON_NAME_PROP, str)

    @common_name.setter
    def common_name(self, v: str | None) -> None:
        self._set_property(COMMON_NAME_PROP, v)

    @property
    def center_wavelength(self) -> float | None:
        """Get or sets the center wavelength of the band, in micrometers (μm)."""
        return self._get_property(CENTER_WAVELENGTH_PROP, float)

    @center_wavelength.setter
    def center_wavelength(self, v: float | None) -> None:
        self._set_property(CENTER_WAVELENGTH_PROP, v)

    @property
    def full_width_half_max(self) -> float | None:
        """Get or sets the full width at half maximum (FWHM). The width of the band,
        as measured at half the maximum transmission, in micrometers (μm).
        """
        return self._get_property(FULL_WIDTH_HALF_MAX_PROP, float)

    @full_width_half_max.setter
    def full_width_half_max(self, v: float | None) -> None:
        self._set_property(FULL_WIDTH_HALF_MAX_PROP, v)

    @property
    def solar_illumination(self) -> float | None:
        """Get or sets the solar illumination of the band, as measured at half the
        maximum transmission, in W/m2/micrometers.
        """
        return self._get_property(SOLAR_ILLUMINATION_PROP, float)

    @solar_illumination.setter
    def solar_illumination(self, v: float | None) -> None:
        self._set_property(SOLAR_ILLUMINATION_PROP, v)

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

        This extension can be applied to instances of :class:`~pystac.Item`,
        :class:`~pystac.Asset`, :class:`~pystac.ItemAssetDefinition` or
        :class:`~pystac.Band`. A band has no owner, so ``add_if_missing`` has no
        effect for it.

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
            return cast(EOExtension[T], BandEOExtension(obj))
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

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

    _has_common_bands = True

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def _get_common_bands(self) -> list[pystac.Band] | None:
        return self.item.bands

    def _set_common_bands(self, bands: list[pystac.Band]) -> None:
        self.item.bands = bands

    def _get_bands(self) -> list[Band] | None:
        """Get or sets a list of :class:`~pystac.Band` objects that represent
        the available bands.
        """
        if (bands := super()._get_bands()) is not None:
            return bands

        # get assets with bands even if not in item
        asset_bands: list[Band] = []
        for asset in self.item.assets.values():
            asset_bands.extend(AssetEOExtension(asset)._get_bands() or [])
        return asset_bands or None

    def get_assets(
        self,
        name: str | None = None,
        common_name: str | None = None,
    ) -> dict[str, pystac.Asset]:
        """Get the item's assets where eo:bands are defined.

        Args:
            name: If set, filter the assets such that only those with a
                matching ``eo:band.name`` are returned.
            common_name: If set, filter the assets such that only those with a matching
                ``eo:band.common_name`` are returned.

        Returns:
            Dict[str, Asset]: A dictionary of assets that match ``name``
                and/or ``common_name`` if set or else all of this item's assets were
                eo:bands are defined.
        """
        kwargs = {"name": name, "common_name": common_name}
        assets = {}
        for key, asset in self.item.get_assets().items():
            bands = AssetEOExtension(asset)._get_bands()
            if bands is not None and all(
                v is None or any(v == b.properties.get(k) for b in bands)
                for k, v in kwargs.items()
            ):
                assets[key] = asset
        return assets

    def __repr__(self) -> str:
        return f"<ItemEOExtension Item id={self.item.id}>"


class AssetEOExtension(EOExtension[pystac.Asset]):
    """A concrete implementation of :class:`EOExtension` on an :class:`~pystac.Asset`
    that extends the Asset fields to include properties defined in the
    :stac-ext:`Electro-Optical Extension <eo>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`EOExtension.ext` on an :class:`~pystac.Asset` to extend it.
    """

    asset: pystac.Asset
    """The :class:`~pystac.Asset` being extended."""

    asset_href: str
    """The ``href`` value of the :class:`~pystac.Asset` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Asset` fields, including extension properties."""

    additional_read_properties: Iterable[dict[str, Any]] | None = None
    """If present, this will be a list containing 1 dictionary representing the
    properties of the owning :class:`~pystac.Item`."""

    _has_common_bands = True

    def _get_common_bands(self) -> list[pystac.Band] | None:
        return _own_bands(self.asset)

    def _set_common_bands(self, bands: list[pystac.Band]) -> None:
        self.asset.bands = bands

    def _get_bands(self) -> list[Band] | None:
        if BANDS_PROP not in self.properties:
            return _to_v1_bands(self._get_common_bands())
        return list(
            map(
                lambda band: Band(band),
                cast(list[dict[str, Any]], self.properties.get(BANDS_PROP)),
            )
        )

    def __init__(self, asset: pystac.Asset):
        self.asset = asset
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return f"<AssetEOExtension Asset href={self.asset_href}>"


class ItemAssetsEOExtension(EOExtension[pystac.ItemAssetDefinition]):
    properties: dict[str, Any]
    asset_defn: pystac.ItemAssetDefinition

    _has_common_bands = True

    def _get_common_bands(self) -> list[pystac.Band] | None:
        return self.asset_defn.bands

    def _set_common_bands(self, bands: list[pystac.Band]) -> None:
        self.asset_defn.bands = bands

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        self.asset_defn = item_asset
        self.properties = item_asset.properties


class BandEOExtension(EOExtension[pystac.Band]):
    """A concrete implementation of :class:`EOExtension` on a :class:`~pystac.Band`
    that extends the band's fields to include properties defined in the
    :stac-ext:`Electro-Optical Extension <eo>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`EOExtension.ext` on a :class:`~pystac.Band` to extend it.
    """

    band: pystac.Band
    """The :class:`~pystac.Band` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Band` extra fields, including extension properties."""

    def __init__(self, band: pystac.Band):
        self.band = band
        self.properties = band.extra_fields

    def __repr__(self) -> str:
        return f"<BandEOExtension Band name={self.band.name}>"


class SummariesEOExtension(SummariesExtension):
    """A concrete implementation of :class:`~pystac.extensions.base.SummariesExtension`
    that extends the ``summaries`` field of a :class:`~pystac.Collection` to include
    properties defined in the :stac-ext:`Electro-Optical Extension <eo>`.
    """

    @property
    def bands(self) -> list[Band] | None:
        """Get or sets the summary of :attr:`EOExtension.bands` values
        for this Collection.

        .. deprecated:: 2.0.0
            eo v2.0.0 removed ``eo:bands``. Use the ``bands`` summary with
            ``eo:`` prefixed fields.

        Reads the ``eo:bands`` summary (eo v1) if it is set. Otherwise, returns
        copies of the ``bands`` summary if a band has a ``name``, ``description`` or
        ``eo:`` field (eo v2); changes to those copies are not kept.

        Setting this property writes the ``bands`` summary, with ``eo:`` prefixed
        fields, and removes the ``eo:bands`` summary. If the ``bands`` summary
        already has as many bands, their non-eo fields are kept. Setting ``None``
        only removes the ``eo:bands`` summary.
        """
        _warn_v1_bands_deprecated("SummariesEOExtension.bands", _SUMMARY_REPLACEMENT)
        bands = self.summaries.get_list(BANDS_PROP)
        if bands is not None:
            return [Band(b) for b in bands]
        return _to_v1_bands(self._get_common_bands())

    @bands.setter
    def bands(self, v: list[Band] | None) -> None:
        _warn_v1_bands_deprecated("SummariesEOExtension.bands", _SUMMARY_REPLACEMENT)
        self._set_summary(BANDS_PROP, None)
        if v is not None:
            bands = _from_v1_bands(v, self._get_common_bands())
            self._set_summary("bands", [b.to_dict() for b in bands])

    def _get_common_bands(self) -> list[pystac.Band] | None:
        return map_opt(
            lambda bands: [pystac.Band.from_dict(b) for b in bands],
            self.summaries.get_list("bands"),
        )

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
    stac_object_types = {pystac.STACObjectType.ITEM, pystac.STACObjectType.COLLECTION}

    def migrate(
        self, obj: dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        if version < "0.9" and info.object_type == pystac.STACObjectType.ITEM:
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

            # The way bands were declared in assets changed.
            # In 1.0.0-beta.1 they are inlined into assets as
            # opposed to having indices back into a property-level array.
            if "eo:bands" in obj["properties"]:
                bands = obj["properties"]["eo:bands"]
                for asset in obj["assets"].values():
                    if "eo:bands" in asset:
                        new_bands: list[dict[str, Any]] = []
                        for band_index in asset["eo:bands"]:
                            new_bands.append(bands[band_index])
                        asset["eo:bands"] = new_bands

        if self.prev_extension_ids.intersection(info.extensions):
            if not migrate_extension_bands(obj, BANDS_PROP, PREFIX, V1_BAND_FIELDS):
                self._replace_extension_ids(obj, info, V1_SCHEMA_URI)
                return
            if not has_extension_fields(obj, PREFIX):
                obj["stac_extensions"] = [
                    uri
                    for uri in obj["stac_extensions"]
                    if uri not in self.prev_extension_ids
                ]
                return
        super().migrate(obj, version, info)


EO_EXTENSION_HOOKS: ExtensionHooks = EOExtensionHooks()
