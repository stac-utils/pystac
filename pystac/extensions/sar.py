"""Implements the Synthetic-Aperture Radar (SAR) extension.

https://github.com/stac-extensions/sar
"""

import enum
from typing import Any, Dict, Generic, Iterable, List, Optional, TypeVar, cast

import pystac
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.extensions.base import ExtensionManagementMixin, PropertiesExtension
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import get_required, map_opt

T = TypeVar("T", pystac.Item, pystac.Asset)

SCHEMA_URI: str = "https://stac-extensions.github.io/sar/v1.0.0/schema.json"
PREFIX: str = "sar:"

# Required
INSTRUMENT_MODE: str = PREFIX + "instrument_mode"
FREQUENCY_BAND: str = PREFIX + "frequency_band"
POLARIZATIONS: str = PREFIX + "polarizations"
PRODUCT_TYPE: str = PREFIX + "product_type"

# Not required
CENTER_FREQUENCY: str = PREFIX + "center_frequency"
RESOLUTION_RANGE: str = PREFIX + "resolution_range"
RESOLUTION_AZIMUTH: str = PREFIX + "resolution_azimuth"
PIXEL_SPACING_RANGE: str = PREFIX + "pixel_spacing_range"
PIXEL_SPACING_AZIMUTH: str = PREFIX + "pixel_spacing_azimuth"
LOOKS_RANGE: str = PREFIX + "looks_range"
LOOKS_AZIMUTH: str = PREFIX + "looks_azimuth"
LOOKS_EQUIVALENT_NUMBER: str = PREFIX + "looks_equivalent_number"
OBSERVATION_DIRECTION: str = PREFIX + "observation_direction"


class FrequencyBand(str, enum.Enum):
    P = "P"
    L = "L"
    S = "S"
    C = "C"
    X = "X"
    KU = "Ku"
    K = "K"
    KA = "Ka"


class Polarization(enum.Enum):
    HH = "HH"
    VV = "VV"
    HV = "HV"
    VH = "VH"


class ObservationDirection(enum.Enum):
    LEFT = "left"
    RIGHT = "right"


class SarExtension(
    Generic[T], PropertiesExtension, ExtensionManagementMixin[pystac.Item]
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Item` or :class:`~pystac.Asset` with properties from the
    :stac-ext:`SAR Extension <sar>`. This class is generic over the type of
    STAC Object to be extended (e.g. :class:`~pystac.Item`,
    :class:`~pystac.Asset`).

    To create a concrete instance of :class:`SARExtension`, use the
    :meth:`SARExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> sar_ext = SARExtension.ext(item)
    """

    def apply(
        self,
        instrument_mode: str,
        frequency_band: FrequencyBand,
        polarizations: List[Polarization],
        product_type: str,
        center_frequency: Optional[float] = None,
        resolution_range: Optional[float] = None,
        resolution_azimuth: Optional[float] = None,
        pixel_spacing_range: Optional[float] = None,
        pixel_spacing_azimuth: Optional[float] = None,
        looks_range: Optional[int] = None,
        looks_azimuth: Optional[int] = None,
        looks_equivalent_number: Optional[float] = None,
        observation_direction: Optional[ObservationDirection] = None,
    ) -> None:
        """Applies sar extension properties to the extended Item.

        Args:
            instrument_mode : The name of the sensor acquisition mode that is
                commonly used. This should be the short name, if available. For example,
                WV for "Wave mode."
            frequency_band : The common name for the frequency band to
                make it easier to search for bands across instruments. See section
                "Common Frequency Band Names" for a list of accepted names.
            polarizations : Any combination of polarizations.
            product_type : The product type, for example SSC, MGD, or SGC.
            center_frequency : Optional center frequency of the instrument in
                gigahertz (GHz).
            resolution_range : Optional range resolution, which is the maximum
                ability to distinguish two adjacent targets perpendicular to the flight
                path, in meters (m).
            resolution_azimuth : Optional azimuth resolution, which is the
                maximum ability to distinguish two adjacent targets parallel to the
                flight path, in meters (m).
            pixel_spacing_range : Optional range pixel spacing, which is the
                distance between adjacent pixels perpendicular to the flight path,
                in meters (m). Strongly RECOMMENDED to be specified for
                products of type GRD.
            pixel_spacing_azimuth : Optional azimuth pixel spacing, which is the
                distance between adjacent pixels parallel to the flight path, in
                meters (m). Strongly RECOMMENDED to be specified for products of
                type GRD.
            looks_range : Optional number of groups of signal samples (looks)
                perpendicular to the flight path.
            looks_azimuth : Optional number of groups of signal samples (looks)
                parallel to the flight path.
            looks_equivalent_number : Optional equivalent number of looks (ENL).
            observation_direction : Optional Antenna pointing
                direction relative to the flight trajectory of the satellite.
        """
        self.instrument_mode = instrument_mode
        self.frequency_band = frequency_band
        self.polarizations = polarizations
        self.product_type = product_type
        if center_frequency:
            self.center_frequency = center_frequency
        if resolution_range:
            self.resolution_range = resolution_range
        if resolution_azimuth:
            self.resolution_azimuth = resolution_azimuth
        if pixel_spacing_range:
            self.pixel_spacing_range = pixel_spacing_range
        if pixel_spacing_azimuth:
            self.pixel_spacing_azimuth = pixel_spacing_azimuth
        if looks_range:
            self.looks_range = looks_range
        if looks_azimuth:
            self.looks_azimuth = looks_azimuth
        if looks_equivalent_number:
            self.looks_equivalent_number = looks_equivalent_number
        if observation_direction:
            self.observation_direction = observation_direction

    @property
    def instrument_mode(self) -> str:
        """Gets or sets an instrument mode string for the item."""
        return get_required(
            self._get_property(INSTRUMENT_MODE, str), self, INSTRUMENT_MODE
        )

    @instrument_mode.setter
    def instrument_mode(self, v: str) -> None:
        self._set_property(INSTRUMENT_MODE, v, pop_if_none=False)

    @property
    def frequency_band(self) -> FrequencyBand:
        """Gets or sets a FrequencyBand for the item."""
        return get_required(
            map_opt(
                lambda x: FrequencyBand(x), self._get_property(FREQUENCY_BAND, str)
            ),
            self,
            FREQUENCY_BAND,
        )

    @frequency_band.setter
    def frequency_band(self, v: FrequencyBand) -> None:
        self._set_property(FREQUENCY_BAND, v.value, pop_if_none=False)

    @property
    def polarizations(self) -> List[Polarization]:
        """Gets or sets a list of polarizations for the item."""
        return get_required(
            map_opt(
                lambda values: [Polarization(v) for v in values],
                self._get_property(POLARIZATIONS, List[str]),
            ),
            self,
            POLARIZATIONS,
        )

    @polarizations.setter
    def polarizations(self, values: List[Polarization]) -> None:
        if not isinstance(values, list):
            raise pystac.STACError(f'polarizations must be a list. Invalid "{values}"')
        self._set_property(POLARIZATIONS, [v.value for v in values], pop_if_none=False)

    @property
    def product_type(self) -> str:
        """Gets or sets a product type string for the item."""
        return get_required(self._get_property(PRODUCT_TYPE, str), self, PRODUCT_TYPE)

    @product_type.setter
    def product_type(self, v: str) -> None:
        self._set_property(PRODUCT_TYPE, v, pop_if_none=False)

    @property
    def center_frequency(self) -> Optional[float]:
        """Gets or sets a center frequency for the item."""
        return self._get_property(CENTER_FREQUENCY, float)

    @center_frequency.setter
    def center_frequency(self, v: Optional[float]) -> None:
        self._set_property(CENTER_FREQUENCY, v)

    @property
    def resolution_range(self) -> Optional[float]:
        """Gets or sets a resolution range for the item."""
        return self._get_property(RESOLUTION_RANGE, float)

    @resolution_range.setter
    def resolution_range(self, v: Optional[float]) -> None:
        self._set_property(RESOLUTION_RANGE, v)

    @property
    def resolution_azimuth(self) -> Optional[float]:
        """Gets or sets a resolution azimuth for the item."""
        return self._get_property(RESOLUTION_AZIMUTH, float)

    @resolution_azimuth.setter
    def resolution_azimuth(self, v: Optional[float]) -> None:
        self._set_property(RESOLUTION_AZIMUTH, v)

    @property
    def pixel_spacing_range(self) -> Optional[float]:
        """Gets or sets a pixel spacing range for the item."""
        return self._get_property(PIXEL_SPACING_RANGE, float)

    @pixel_spacing_range.setter
    def pixel_spacing_range(self, v: Optional[float]) -> None:
        self._set_property(PIXEL_SPACING_RANGE, v)

    @property
    def pixel_spacing_azimuth(self) -> Optional[float]:
        """Gets or sets a pixel spacing azimuth for the item."""
        return self._get_property(PIXEL_SPACING_AZIMUTH, float)

    @pixel_spacing_azimuth.setter
    def pixel_spacing_azimuth(self, v: Optional[float]) -> None:
        self._set_property(PIXEL_SPACING_AZIMUTH, v)

    @property
    def looks_range(self) -> Optional[int]:
        """Gets or sets a looks range for the item."""
        return self._get_property(LOOKS_RANGE, int)

    @looks_range.setter
    def looks_range(self, v: Optional[int]) -> None:
        self._set_property(LOOKS_RANGE, v)

    @property
    def looks_azimuth(self) -> Optional[int]:
        """Gets or sets a looks azimuth for the item."""
        return self._get_property(LOOKS_AZIMUTH, int)

    @looks_azimuth.setter
    def looks_azimuth(self, v: Optional[int]) -> None:
        self._set_property(LOOKS_AZIMUTH, v)

    @property
    def looks_equivalent_number(self) -> Optional[float]:
        """Gets or sets a looks equivalent number for the item."""
        return self._get_property(LOOKS_EQUIVALENT_NUMBER, float)

    @looks_equivalent_number.setter
    def looks_equivalent_number(self, v: Optional[float]) -> None:
        self._set_property(LOOKS_EQUIVALENT_NUMBER, v)

    @property
    def observation_direction(self) -> Optional[ObservationDirection]:
        """Gets or sets an observation direction for the item."""
        result = self._get_property(OBSERVATION_DIRECTION, str)
        if result is None:
            return None
        return ObservationDirection(result)

    @observation_direction.setter
    def observation_direction(self, v: Optional[ObservationDirection]) -> None:
        self._set_property(OBSERVATION_DIRECTION, map_opt(lambda x: x.value, v))

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> "SarExtension[T]":
        """Extends the given STAC Object with properties from the :stac-ext:`SAR
        Extension <sar>`.

        This extension can be applied to instances of :class:`~pystac.Item` or
        :class:`~pystac.Asset`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Item):
            if add_if_missing:
                cls.add_to(obj)
            cls.validate_has_extension(obj)
            return cast(SarExtension[T], ItemSarExtension(obj))
        elif isinstance(obj, pystac.Asset):
            if add_if_missing and isinstance(obj.owner, pystac.Item):
                cls.add_to(obj.owner)
            cls.validate_has_extension(obj)
            return cast(SarExtension[T], AssetSarExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"SAR extension does not apply to type '{type(obj).__name__}'"
            )


class ItemSarExtension(SarExtension[pystac.Item]):
    """A concrete implementation of :class:`SARExtension` on an :class:`~pystac.Item`
    that extends the properties of the Item to include properties defined in the
    :stac-ext:`SAR Extension <sar>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`SARExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: pystac.Item
    """The :class:`~pystac.Item` being extended."""

    properties: Dict[str, Any]
    """The :class:`~pystac.Item` properties, including extension properties."""

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return "<ItemSarExtension Item id={}>".format(self.item.id)


class AssetSarExtension(SarExtension[pystac.Asset]):
    """A concrete implementation of :class:`SARExtension` on an :class:`~pystac.Asset`
    that extends the Asset fields to include properties defined in the
    :stac-ext:`SAR Extension <sar>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`SARExtension.ext` on an :class:`~pystac.Asset` to extend it.
    """

    asset_href: str
    """The ``href`` value of the :class:`~pystac.Asset` being extended."""

    properties: Dict[str, Any]
    """The :class:`~pystac.Asset` fields, including extension properties."""

    additional_read_properties: Optional[Iterable[Dict[str, Any]]] = None
    """If present, this will be a list containing 1 dictionary representing the
    properties of the owning :class:`~pystac.Item`."""

    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return "<AssetSarExtension Asset href={}>".format(self.asset_href)


class SarExtensionHooks(ExtensionHooks):
    schema_uri = SCHEMA_URI
    prev_extension_ids = {"sar"}
    stac_object_types = {pystac.STACObjectType.ITEM}

    def migrate(
        self, obj: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        if version < "0.9":
            # Some sar fields became common_metadata
            if (
                PREFIX + "platform" in obj["properties"]
                and "platform" not in obj["properties"]
            ):
                obj["properties"]["platform"] = obj["properties"][PREFIX + "platform"]
                del obj["properties"][PREFIX + "platform"]

            if (
                PREFIX + "instrument" in obj["properties"]
                and "instruments" not in obj["properties"]
            ):
                obj["properties"]["instruments"] = [
                    obj["properties"][PREFIX + "instrument"]
                ]
                del obj["properties"][PREFIX + "instrument"]

            if (
                PREFIX + "constellation" in obj["properties"]
                and "constellation" not in obj["properties"]
            ):
                obj["properties"]["constellation"] = obj["properties"][
                    PREFIX + "constellation"
                ]
                del obj["properties"][PREFIX + "constellation"]

        super().migrate(obj, version, info)


SAR_EXTENSION_HOOKS: ExtensionHooks = SarExtensionHooks()
