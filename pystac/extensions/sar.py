"""Implement the STAC Synthetic-Aperture Radar (SAR) Extension.

https://github.com/radiantearth/stac-spec/tree/dev/extensions/sar
"""

import enum
from typing import List, Optional, TypeVar

import pystac
from pystac import Extensions
from pystac.extensions import base

# Required
INSTRUMENT_MODE: str = 'sar:instrument_mode'
FREQUENCY_BAND: str = 'sar:frequency_band'
POLARIZATIONS: str = 'sar:polarizations'
PRODUCT_TYPE: str = 'sar:product_type'

# Not required
CENTER_FREQUENCY: str = 'sar:center_frequency'
RESOLUTION_RANGE: str = 'sar:resolution_range'
RESOLUTION_AZIMUTH: str = 'sar:resolution_azimuth'
PIXEL_SPACING_RANGE: str = 'sar:pixel_spacing_range'
PIXEL_SPACING_AZIMUTH: str = 'sar:pixel_spacing_azimuth'
LOOKS_RANGE: str = 'sar:looks_range'
LOOKS_AZIMUTH: str = 'sar:looks_azimuth'
LOOKS_EQUIVALENT_NUMBER: str = 'sar:looks_equivalent_number'
OBSERVATION_DIRECTION: str = 'sar:observation_direction'

SarItemExtType = TypeVar('SarItemExtType')


class FrequencyBand(enum.Enum):
    P: str = 'P'
    L: str = 'L'
    S: str = 'S'
    C: str = 'C'
    X: str = 'X'
    KU: str = 'Ku'
    K: str = 'K'
    KA: str = 'Ka'


class Polarization(enum.Enum):
    HH: str = 'HH'
    VV: str = 'VV'
    HV: str = 'HV'
    VH: str = 'VH'


class ObservationDirection(enum.Enum):
    LEFT: str = 'left'
    RIGHT: str = 'right'


class SarItemExt(base.ItemExtension):
    """SarItemExt extends Item to add sar properties to a STAC Item.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The item that is being extended.

    Note:
        Using SarItemExt to directly wrap an item will add the 'sar'
        extension ID to the item's stac_extensions.
    """
    item: pystac.Item

    def __init__(self, an_item: pystac.Item) -> None:
        self.item = an_item

    def apply(self,
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
              observation_direction: Optional[ObservationDirection] = None):
        """Applies sar extension properties to the extended Item.

        Args:
            instrument_mode (str): The name of the sensor acquisition mode that is commonly used.
                This should be the short name, if available. For example, WV for "Wave mode."
            frequency_band (FrequencyBand): The common name for the frequency band to make it easier
                to search for bands across instruments. See section "Common Frequency Band Names"
                for a list of accepted names.
            polarizations (List[Polarization]): Any combination of polarizations.
            product_type (str): The product type, for example SSC, MGD, or SGC.
            center_frequency (float): Optional center frequency of the instrument in
                gigahertz (GHz).
            resolution_range (float): Optional range resolution, which is the maximum ability to
                distinguish two adjacent targets perpendicular to the flight path, in meters (m).
            resolution_azimuth (float): Optional azimuth resolution, which is the maximum ability
                to distinguish two adjacent targets parallel to the flight path, in meters (m).
            pixel_spacing_range (float): Optional range pixel spacing, which is the distance
                between adjacent pixels perpendicular to the flight path, in meters (m). Strongly
                RECOMMENDED to be specified for products of type GRD.
            pixel_spacing_azimuth (float): Optional azimuth pixel spacing, which is the distance
                between adjacent pixels parallel to the flight path, in meters (m). Strongly
                RECOMMENDED to be specified for products of type GRD.
            looks_range (int): Optional number of groups of signal samples (looks) perpendicular
                to the flight path.
            looks_azimuth (int): Optional number of groups of signal samples (looks) parallel
                to the flight path.
            looks_equivalent_number (float): Optional equivalent number of looks (ENL).
            observation_direction (ObservationDirection): Optional Antenna pointing direction
                relative to the flight trajectory of the satellite.
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

    @classmethod
    def from_item(cls: SarItemExtType, an_item: pystac.Item) -> SarItemExtType:
        return cls(an_item)

    @classmethod
    def _object_links(cls) -> List:
        return []

    @property
    def instrument_mode(self) -> str:
        """Get or sets an instrument mode string for the item.

        Returns:
            str
        """
        return self.item.properties.get(INSTRUMENT_MODE)

    @instrument_mode.setter
    def instrument_mode(self, v: str) -> None:
        self.item.properties[INSTRUMENT_MODE] = v

    @property
    def frequency_band(self) -> FrequencyBand:
        """Get or sets a FrequencyBand for the item.

        Returns:
            FrequencyBand
        """
        return FrequencyBand(self.item.properties.get(FREQUENCY_BAND))

    @frequency_band.setter
    def frequency_band(self, v: FrequencyBand) -> None:
        self.item.properties[FREQUENCY_BAND] = v.value

    @property
    def polarizations(self) -> List[Polarization]:
        """Get or sets a list of polarizations for the item.

        Returns:
            List[Polarization]
        """
        return [Polarization(v) for v in self.item.properties.get(POLARIZATIONS)]

    @polarizations.setter
    def polarizations(self, values: List[Polarization]) -> None:
        if not isinstance(values, list):
            raise pystac.STACError(f'polarizations must be a list. Invalid "{values}"')
        self.item.properties[POLARIZATIONS] = [v.value for v in values]

    @property
    def product_type(self) -> str:
        """Get or sets a product type string for the item.

        Returns:
            str
        """
        return self.item.properties.get(PRODUCT_TYPE)

    @product_type.setter
    def product_type(self, v: str) -> None:
        self.item.properties[PRODUCT_TYPE] = v

    @property
    def center_frequency(self) -> float:
        """Get or sets a center frequency for the item.

        Returns:
            float
        """
        return self.item.properties.get(CENTER_FREQUENCY)

    @center_frequency.setter
    def center_frequency(self, v: float) -> None:
        self.item.properties[CENTER_FREQUENCY] = v

    @property
    def resolution_range(self) -> float:
        """Get or sets a resolution range for the item.

        Returns:
            float
        """
        return self.item.properties.get(RESOLUTION_RANGE)

    @resolution_range.setter
    def resolution_range(self, v: float) -> None:
        self.item.properties[RESOLUTION_RANGE] = v

    @property
    def resolution_azimuth(self) -> float:
        """Get or sets a resolution azimuth for the item.

        Returns:
            float
        """
        return self.item.properties.get(RESOLUTION_AZIMUTH)

    @resolution_azimuth.setter
    def resolution_azimuth(self, v: float) -> None:
        self.item.properties[RESOLUTION_AZIMUTH] = v

    @property
    def pixel_spacing_range(self) -> float:
        """Get or sets a pixel spacing range for the item.

        Returns:
            float
        """
        return self.item.properties.get(PIXEL_SPACING_RANGE)

    @pixel_spacing_range.setter
    def pixel_spacing_range(self, v: float) -> None:
        self.item.properties[PIXEL_SPACING_RANGE] = v

    @property
    def pixel_spacing_azimuth(self) -> float:
        """Get or sets a pixel spacing azimuth for the item.

        Returns:
            float
        """
        return self.item.properties.get(PIXEL_SPACING_AZIMUTH)

    @pixel_spacing_azimuth.setter
    def pixel_spacing_azimuth(self, v: float) -> None:
        self.item.properties[PIXEL_SPACING_AZIMUTH] = v

    @property
    def looks_range(self) -> int:
        """Get or sets a looks range for the item.

        Returns:
            int
        """
        return self.item.properties.get(LOOKS_RANGE)

    @looks_range.setter
    def looks_range(self, v: int) -> None:
        self.item.properties[LOOKS_RANGE] = v

    @property
    def looks_azimuth(self) -> int:
        """Get or sets a looks azimuth for the item.

        Returns:
            int
        """
        return self.item.properties.get(LOOKS_AZIMUTH)

    @looks_azimuth.setter
    def looks_azimuth(self, v: int) -> None:
        self.item.properties[LOOKS_AZIMUTH] = v

    @property
    def looks_equivalent_number(self) -> float:
        """Get or sets a looks equivalent number for the item.

        Returns:
            float
        """
        return self.item.properties.get(LOOKS_EQUIVALENT_NUMBER)

    @looks_equivalent_number.setter
    def looks_equivalent_number(self, v: float) -> None:
        self.item.properties[LOOKS_EQUIVALENT_NUMBER] = v

    @property
    def observation_direction(self) -> ObservationDirection:
        """Get or sets an observation direction for the item.

        Returns:
            ObservationDirection
        """
        return ObservationDirection(self.item.properties.get(OBSERVATION_DIRECTION))

    @observation_direction.setter
    def observation_direction(self, v: ObservationDirection) -> None:
        self.item.properties[OBSERVATION_DIRECTION] = v.value


SAR_EXTENSION_DEFINITION = base.ExtensionDefinition(Extensions.SAR, [
    base.ExtendedObject(pystac.Item, SarItemExt),
])
