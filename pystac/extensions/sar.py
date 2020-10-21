"""Implement the STAC Synthetic-Aperture Radar (SAR) Extension.

https://github.com/radiantearth/stac-spec/tree/dev/extensions/sar
"""

# TODO(schwehr): Document.

import enum
from typing import List, Optional, TypeVar

import pystac
from pystac import Extensions
from pystac import item
from pystac.extensions import base

# Required
INSTRUMENT_MODE = 'sar:instrument_mode'
FREQUENCY_BAND = 'sar:frequency_band'
POLARIZATIONS = 'sar:polarizations'
PRODUCT_TYPE = 'sar:product_type'

# Not required
CENTER_FREQUENCY = 'sar:center_frequency'
RESOLUTION_RANGE = 'sar:resolution_range'
RESOLUTION_AZIMUTH = 'sar:resolution_azimuth'
PIXEL_SPACING_RANGE = 'sar:pixel_spacing_range'
PIXEL_SPACING_AZIMUTH = 'sar:pixel_spacing_azimuth'
LOOKS_RANGE = 'sar:looks_range'
LOOKS_AZIMUTH = 'sar:looks_azimuth'
LOOKS_EQUIVALENT_NUMBER = 'sar:looks_equivalent_number'
OBSERVATION_DIRECTION = 'sar:observation_direction'

SarItemExtType = TypeVar('SarItemExtType')


class FrequencyBand(enum.Enum):
    P = 'P'
    L = 'L'
    S = 'S'
    C = 'C'
    X = 'X'
    KU = 'Ku'
    K = 'K'
    KA = 'Ka'


class Polarization(enum.Enum):
    HH = 'HH'
    VV = 'VV'
    HV = 'HV'
    VH = 'VH'


class ObservationDirection(enum.Enum):
    LEFT = 'left'
    RIGHT = 'right'


class SarItemExt(base.ItemExtension):
    """Add sar properties to a STAC Item."""
    def __init__(self, an_item: item.Item) -> None:
        self.item = an_item

    def apply(self,
              instrument_mode: str,
              frequency_band: str,
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
    def from_item(cls: SarItemExtType, an_item: item.Item) -> SarItemExtType:
        return cls(an_item)

    @classmethod
    def _object_links(cls) -> List:
        return []

    @property
    def instrument_mode(self) -> str:
        return self.item.properties.get(INSTRUMENT_MODE)

    @instrument_mode.setter
    def instrument_mode(self, v: str) -> None:
        self.item.properties[INSTRUMENT_MODE] = v

    @property
    def frequency_band(self) -> FrequencyBand:
        return FrequencyBand(self.item.properties.get(FREQUENCY_BAND))

    @frequency_band.setter
    def frequency_band(self, v: FrequencyBand) -> None:
        self.item.properties[FREQUENCY_BAND] = v.value

    @property
    def polarizations(self) -> List[Polarization]:
        return [Polarization(v) for v in self.item.properties.get(POLARIZATIONS)]

    @polarizations.setter
    def polarizations(self, values: List[Polarization]) -> None:
        if not isinstance(values, list):
            raise pystac.STACError(f'polarizations must be a list. Invalid "{values}"')
        self.item.properties[POLARIZATIONS] = [v.value for v in values]

    @property
    def product_type(self) -> str:
        return self.item.properties.get(PRODUCT_TYPE)

    @product_type.setter
    def product_type(self, v: str) -> None:
        self.item.properties[PRODUCT_TYPE] = v

    @property
    def center_frequency(self) -> float:
        return self.item.properties.get(CENTER_FREQUENCY)

    @center_frequency.setter
    def center_frequency(self, v: float) -> None:
        self.item.properties[CENTER_FREQUENCY] = v

    @property
    def resolution_range(self) -> float:
        return self.item.properties.get(RESOLUTION_RANGE)

    @resolution_range.setter
    def resolution_range(self, v: float) -> None:
        self.item.properties[RESOLUTION_RANGE] = v

    @property
    def resolution_azimuth(self) -> float:
        return self.item.properties.get(RESOLUTION_AZIMUTH)

    @resolution_azimuth.setter
    def resolution_azimuth(self, v: float) -> None:
        self.item.properties[RESOLUTION_AZIMUTH] = v

    @property
    def pixel_spacing_range(self) -> float:
        return self.item.properties.get(PIXEL_SPACING_RANGE)

    @pixel_spacing_range.setter
    def pixel_spacing_range(self, v: float) -> None:
        self.item.properties[PIXEL_SPACING_RANGE] = v

    @property
    def pixel_spacing_azimuth(self) -> float:
        return self.item.properties.get(PIXEL_SPACING_AZIMUTH)

    @pixel_spacing_azimuth.setter
    def pixel_spacing_azimuth(self, v: float) -> None:
        self.item.properties[PIXEL_SPACING_AZIMUTH] = v

    @property
    def looks_range(self) -> int:
        return self.item.properties.get(LOOKS_RANGE)

    @looks_range.setter
    def looks_range(self, v: int) -> None:
        self.item.properties[LOOKS_RANGE] = v

    @property
    def looks_azimuth(self) -> int:
        return self.item.properties.get(LOOKS_AZIMUTH)

    @looks_azimuth.setter
    def looks_azimuth(self, v: int) -> None:
        self.item.properties[LOOKS_AZIMUTH] = v

    @property
    def looks_equivalent_number(self) -> float:
        return self.item.properties.get(LOOKS_EQUIVALENT_NUMBER)

    @looks_equivalent_number.setter
    def looks_equivalent_number(self, v: float) -> None:
        self.item.properties[LOOKS_EQUIVALENT_NUMBER] = v

    @property
    def observation_direction(self) -> ObservationDirection:
        return ObservationDirection(self.item.properties.get(OBSERVATION_DIRECTION))

    @observation_direction.setter
    def observation_direction(self, v: ObservationDirection) -> None:
        self.item.properties[OBSERVATION_DIRECTION] = v.value


SAR_EXTENSION_DEFINITION = base.ExtensionDefinition(Extensions.SAR, [
    base.ExtendedObject(item.Item, SarItemExt),
])
