"""Implements the Raster extension.

https://github.com/stac-extensions/raster
"""

import enum
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

SCHEMA_URI = "https://stac-extensions.github.io/raster/v1.0.0/schema.json"

BANDS_PROP = "raster:bands"


class Sampling(enum.Enum):
    AREA = "area"
    POINT = "point"


class FileDataType(str, enum.Enum):
    def __str__(self) -> str:
        return str(self.value)

    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"
    INT64 = "int64"
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"
    UINT64 = "uint64"
    FLOAT16 = "float16"
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    CINT16 = "cint16"
    CINT32 = "cint32"
    CFLOAT32 = "cfloat32"
    CFLOAT64 = "cfloat64"
    OTHER = "other"


class Statistics:
    """Represents statistics information attached to a band in the raster extension.

    Use Band.create to create a new Band.
    """

    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    def apply(
        self,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        mean: Optional[float] = None,
        stddev: Optional[float] = None,
        valid_percent: Optional[float] = None,
    ) -> None:
        """
        Sets the properties for this raster Band.

        Args:
            minimum : Minimum value of all the pixels in the band.
            maximum : Maximum value of all the pixels in the band.
            mean : Mean value of all the pixels in the band.
            stddev : Standard Deviation value of all the pixels in the band.
            valid_percent : Percentage of valid (not nodata) pixel.
        """  # noqa
        self.minimum = minimum
        self.maximum = maximum
        self.mean = mean
        self.stddev = stddev
        self.valid_percent = valid_percent

    @classmethod
    def create(
        cls,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        mean: Optional[float] = None,
        stddev: Optional[float] = None,
        valid_percent: Optional[float] = None,
    ) -> "RasterBand":
        """
        Creates a new band.

        Args:
            minimum : Minimum value of all the pixels in the band.
            maximum : Maximum value of all the pixels in the band.
            mean : Mean value of all the pixels in the band.
            stddev : Standard Deviation value of all the pixels in the band.
            valid_percent : Percentage of valid (not nodata) pixel.
        """  # noqa
        b = cls({})
        b.apply(
            minimum=minimum,
            maximum=maximum,
            mean=mean,
            stddev=stddev,
            valid_percent=valid_percent,
        )
        return b

    @property
    def minimum(self) -> Optional[float]:
        """Get or sets the minmum pixel value

        Returns:
            Optional[float]
        """
        return self.properties.get("minimum")

    @minimum.setter
    def minimum(self, v: float) -> None:
        if v is not None:
            self.properties["minimum"] = v
        else:
            self.properties.pop("minimum", None)

    @property
    def maximum(self) -> Optional[float]:
        """Get or sets the maximum pixel value

        Returns:
            Optional[float]
        """
        return self.properties.get("maximum")

    @maximum.setter
    def maximum(self, v: float) -> None:
        if v is not None:
            self.properties["maximum"] = v
        else:
            self.properties.pop("maximum", None)

    @property
    def mean(self) -> Optional[float]:
        """Get or sets the mean pixel value

        Returns:
            Optional[float]
        """
        return self.properties.get("mean")

    @mean.setter
    def mean(self, v: float) -> None:
        if v is not None:
            self.properties["mean"] = v
        else:
            self.properties.pop("mean", None)

    @property
    def stdev(self) -> Optional[float]:
        """Get or sets the stdev pixel value

        Returns:
            Optional[float]
        """
        return self.properties.get("stdev")

    @stdev.setter
    def stdev(self, v: float) -> None:
        if v is not None:
            self.properties["stdev"] = v
        else:
            self.properties.pop("stdev", None)

    @property
    def valid_percent(self) -> Optional[float]:
        """Get or sets the Percentage of valid (not nodata) pixel

        Returns:
            Optional[float]
        """
        return self.properties.get("valid_percent")

    @valid_percent.setter
    def valid_percent(self, v: float) -> None:
        if v is not None:
            self.properties["valid_percent"] = v
        else:
            self.properties.pop("valid_percent", None)

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of those Statistics.

        Returns:
            dict: The wrapped dict of the Statistics that can be written out as JSON.
        """
        return self.properties


class Histogram:
    """Represents pixel distribution information attached to a band in the raster extension.

    Use Band.create to create a new Band.
    """

    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    def apply(
        self,
        count: int = None,
        min: float = None,
        max: float = None,
        buckets: List[int] = None,
    ) -> None:
        """
        Sets the properties for this raster Band.

        Args:
            count : number of buckets of the distribution.
            min : minimum value of the distribution.
                Also the mean value of the first bucket.
            max : maximum value of the distribution.
                Also the mean value of the last bucket.
            buckets : Array of integer indicating the number
                of pixels included in the bucket.
        """  # noqa
        self.count = count
        self.min = min
        self.max = max
        self.buckets = buckets

    @classmethod
    def create(
        cls,
        count: int = None,
        min: float = None,
        max: float = None,
        buckets: List[int] = None,
    ) -> "RasterBand":
        """
        Creates a new band.

        Args:
            count : number of buckets of the distribution.
            min : minimum value of the distribution.
                Also the mean value of the first bucket.
            max : maximum value of the distribution.
                Also the mean value of the last bucket.
            buckets : Array of integer indicating the number
                of pixels included in the bucket.
        """  # noqa
        b = cls({})
        b.apply(
            count=count,
            min=min,
            max=max,
            buckets=buckets,
        )
        return b

    @property
    def count(self) -> Optional[float]:
        """Get or sets the number of buckets of the distribution.

        Returns:
            Optional[float]
        """
        return self.properties.get("count")

    @count.setter
    def count(self, v: float) -> None:
        if v is not None:
            self.properties["count"] = v
        else:
            self.properties.pop("count", None)

    @property
    def min(self) -> Optional[float]:
        """Get or sets the minimum value of the distribution.

        Returns:
            Optional[float]
        """
        return self.properties.get("min")

    @min.setter
    def min(self, v: float) -> None:
        if v is not None:
            self.properties["min"] = v
        else:
            self.properties.pop("min", None)

    @property
    def max(self) -> Optional[float]:
        """Get or sets the maximum value of the distribution.

        Returns:
            float
        """
        return self.properties.get("max")

    @max.setter
    def max(self, v: float) -> None:
        if v is not None:
            self.properties["max"] = v
        else:
            self.properties.pop("max", None)

    @property
    def buckets(self) -> List[int]:
        """Get or sets the Array of integer indicating
        the number of pixels included in the bucket.

        Returns:
            List[int]
        """
        return self.properties.get("buckets")

    @buckets.setter
    def buckets(self, v: List[int]) -> None:
        if v is not None:
            self.properties["buckets"] = v
        else:
            self.properties.pop("buckets", None)

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of this histogram.

        Returns:
            dict: The wrapped dict of the Histogram that can be written out as JSON.
        """
        return self.properties


class RasterBand:
    """Represents a Raster Band information attached to an Item that implements the raster extension.

    Use Band.create to create a new Band.
    """

    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    def apply(
        self,
        nodata: Optional[float] = None,
        sampling: Optional[Sampling] = None,
        data_type: Optional[FileDataType] = None,
        bits_per_sample: Optional[float] = None,
        spatial_resolution: Optional[float] = None,
        statistics: Optional[Statistics] = None,
        unit: Optional[str] = None,
        scale: Optional[float] = None,
        offset: Optional[float] = None,
        histogram: Optional[Histogram] = None,
    ) -> None:
        """
        Sets the properties for this raster Band.

        Args:
            nodata : Pixel values used to identify pixels that are nodata in the assets.
            sampling : One of area or point. Indicates whether a pixel value should be assumed
                to represent a sampling over the region of the pixel or a point sample at the center of the pixel.
            data_type :The data type of the band.
                One of the data types as described in <https://github.com/stac-extensions/raster/#data-types>.
            bits_per_sample : The actual number of bits used for this band.
                Normally only present when the number of bits is non-standard for the datatype,
                such as when a 1 bit TIFF is represented as byte
            spatial_resolution : Average spatial resolution (in meters) of the pixels in the band.
            statistics: Statistics of all the pixels in the band
            unit: unit denomination of the pixel value
            scale: multiplicator factor of the pixel value to transform into the value
                (i.e. translate digital number to reflectance).
            offset: number to be added to the pixel value (after scaling) to transform into the value
                (i.e. translate digital number to reflectance).
            histogram: Histogram distribution information of the pixels values in the band
        """  # noqa
        self.nodata = nodata
        self.sampling = sampling
        self.data_type = data_type
        self.bits_per_sample = bits_per_sample
        self.spatial_resolution = spatial_resolution
        self.statistics = statistics
        self.unit = unit
        self.scale = scale
        self.offset = offset
        self.histogram = histogram

    @classmethod
    def create(
        cls,
        self,
        nodata: Optional[float] = None,
        sampling: Optional[Sampling] = None,
        data_type: Optional[FileDataType] = None,
        bits_per_sample: Optional[float] = None,
        spatial_resolution: Optional[float] = None,
        statistics: Optional[Statistics] = None,
        unit: Optional[str] = None,
        scale: Optional[float] = None,
        offset: Optional[float] = None,
        histogram: Optional[Histogram] = None,
    ) -> "RasterBand":
        """
        Creates a new band.

        Args:
            nodata : Pixel values used to identify pixels that are nodata in the assets.
            sampling : One of area or point. Indicates whether a pixel value should be assumed
                to represent a sampling over the region of the pixel or a point sample at the center of the pixel.
            data_type :The data type of the band.
                One of the data types as described in <https://github.com/stac-extensions/raster/#data-types>.
            bits_per_sample : The actual number of bits used for this band.
                Normally only present when the number of bits is non-standard for the datatype,
                such as when a 1 bit TIFF is represented as byte
            spatial_resolution : Average spatial resolution (in meters) of the pixels in the band.
            statistics: Statistics of all the pixels in the band
            unit: unit denomination of the pixel value
            scale: multiplicator factor of the pixel value to transform into the value
                (i.e. translate digital number to reflectance).
            offset: number to be added to the pixel value (after scaling) to transform into the value
                (i.e. translate digital number to reflectance).
            histogram: Histogram distribution information of the pixels values in the band
        """  # noqa
        b = cls({})
        b.apply(
            nodata=nodata,
            sampling=sampling,
            data_type=data_type,
            bits_per_sample=bits_per_sample,
            spatial_resolution=spatial_resolution,
            statistics=statistics,
            unit=unit,
            scale=scale,
            offset=offset,
            histogram=histogram,
        )
        return b

    @property
    def nodata(self) -> Optional[float]:
        """Get or sets the nodata pixel value

        Returns:
            Optional[float]
        """
        return self.properties.get("nodata")

    @nodata.setter
    def nodata(self, v: float) -> None:
        if v is not None:
            self.properties["nodata"] = v
        else:
            self.properties.pop("nodata", None)

    @property
    def sampling(self) -> Optional[Sampling]:
        """Get or sets the Indicates whether a pixel value should be assumed
        to represent a sampling over the region of the pixel or a point sample
        at the center of the pixel.

        Returns:
            Optional[Sampling]
        """  # noqa
        return self.properties.get("sampling")

    @sampling.setter
    def sampling(self, v: Optional[Sampling]) -> None:
        if v is not None:
            self.properties["sampling"] = v
        else:
            self.properties.pop("sampling", None)

    @property
    def data_type(self) -> Optional[FileDataType]:
        """Get or sets the The data type of the band.

        Returns:
            Optional[FileDataType]
        """
        return self.properties.get("data_type")

    @data_type.setter
    def data_type(self, v: Optional[FileDataType]) -> None:
        if v is not None:
            self.properties["data_type"] = v
        else:
            self.properties.pop("data_type", None)

    @property
    def bits_per_sample(self) -> Optional[float]:
        """Get or sets the actual number of bits used for this band.

        Returns:
            float
        """
        return self.properties.get("bits_per_sample")

    @bits_per_sample.setter
    def bits_per_sample(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties["bits_per_sample"] = v
        else:
            self.properties.pop("bits_per_sample", None)

    @property
    def spatial_resolution(self) -> Optional[float]:
        """Get or sets Average spatial resolution (in meters) of the pixels in the band.

        Returns:
            [float]
        """
        return self.properties.get("spatial_resolution")

    @spatial_resolution.setter
    def spatial_resolution(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties["spatial_resolution"] = v
        else:
            self.properties.pop("spatial_resolution", None)

    @property
    def statistics(self) -> Optional[Statistics]:
        """Get or sets Average spatial resolution (in meters) of the pixels in the band.

        Returns:
            [Statistics]
        """
        return self.properties.get("statistics")

    @statistics.setter
    def statistics(self, v: Optional[Statistics]) -> None:
        if v is not None:
            self.properties["statistics"] = v
        else:
            self.properties.pop("statistics", None)

    @property
    def unit(self) -> Optional[str]:
        """Get or sets the unit denomination of the pixel value

        Returns:
            [str]
        """
        return self.properties.get("unit")

    @unit.setter
    def unit(self, v: Optional[str]) -> None:
        if v is not None:
            self.properties["unit"] = v
        else:
            self.properties.pop("unit", None)

    @property
    def scale(self) -> Optional[float]:
        """Get or sets the multiplicator factor of the pixel value to transform
        into the value (i.e. translate digital number to reflectance).

        Returns:
            [float]
        """
        return self.properties.get("scale")

    @scale.setter
    def scale(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties["scale"] = v
        else:
            self.properties.pop("scale", None)

    @property
    def offset(self) -> Optional[float]:
        """Get or sets the number to be added to the pixel value (after scaling)
        to transform into the value (i.e. translate digital number to reflectance).

        Returns:
            [float]
        """
        return self.properties.get("offset")

    @offset.setter
    def offset(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties["offset"] = v
        else:
            self.properties.pop("offset", None)

    @property
    def histogram(self) -> Optional[Histogram]:
        """Get or sets the Histogram distribution information of the pixels values in the band

        Returns:
            [Histogram]
        """
        return self.properties.get("histogram")

    @histogram.setter
    def histogram(self, v: Optional[Histogram]) -> None:
        if v is not None:
            self.properties["histogram"] = v
        else:
            self.properties.pop("histogram", None)

    def __repr__(self) -> str:
        return "<Raster Band name={}>".format(self.name)

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of this Band.

        Returns:
            dict: The wrapped dict of the Band that can be written out as JSON.
        """
        return self.properties


class RasterExtension(
    Generic[T], PropertiesExtension, ExtensionManagementMixin[pystac.Item]
):
    """RasterItemExt is the extension of the Item in the raster extension

    Args:
        item : The item to be extended.

    Attributes:
        item : The Item that is being extended.

    Note:
        Using RasterItemExt to directly wrap an item will add the 'raster' extension ID to
        the item's stac_extensions.
    """

    def apply(self, bands: List[RasterBand]) -> None:
        """Applies label extension properties to the extended Item.

        Args:
            bands : a list of :class:`~pystac.RasterBand` objects that represent
                the available raster bands.
        """
        self.bands = bands

    @property
    def bands(self) -> Optional[List[RasterBand]]:
        """Get or sets a list of :class:`~pystac.RasterBand` objects that represent
        the available bands.
        """
        return self._get_bands()

    def _get_bands(self) -> Optional[List[RasterBand]]:
        return map_opt(
            lambda bands: [RasterBand(b) for b in bands],
            self._get_property(BANDS_PROP, List[Dict[str, Any]]),
        )

    @bands.setter
    def bands(self, v: Optional[List[RasterBand]]) -> None:
        self._set_property(
            BANDS_PROP, map_opt(lambda bands: [b.to_dict() for b in bands], v)
        )

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @staticmethod
    def ext(obj: T) -> "RasterExtension[T]":
        if isinstance(obj, pystac.Asset):
            return cast(RasterExtension[T], AssetRasterExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"Raster extension does not apply to type {type(obj)}"
            )

    @staticmethod
    def summaries(obj: pystac.Collection) -> "SummariesRasterExtension":
        return SummariesRasterExtension(obj)


class AssetRasterExtension(RasterExtension[pystac.Asset]):
    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.properties
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return "<AssetRasterExtension Item id={}>".format(self.asset_href)


class SummariesRasterExtension(SummariesExtension):
    @property
    def bands(self) -> Optional[List[RasterBand]]:
        """Get or sets a list of :class:`~pystac.Band` objects that represent
        the available bands.
        """
        return map_opt(
            lambda bands: [RasterBand(b) for b in bands],
            self.summaries.get_list(BANDS_PROP, Dict[str, Any]),
        )

    @bands.setter
    def bands(self, v: Optional[List[RasterBand]]) -> None:
        self._set_summary(BANDS_PROP, map_opt(lambda x: [b.to_dict() for b in x], v))
