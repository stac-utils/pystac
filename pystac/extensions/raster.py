"""Implements the :stac-ext:`Raster Extension <raster>`."""

from typing import Any, Dict, Iterable, List, Optional, Union

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.utils import StringEnum, get_opt, get_required, map_opt

SCHEMA_URI = "https://stac-extensions.github.io/raster/v1.1.0/schema.json"

BANDS_PROP = "raster:bands"


class Sampling(StringEnum):
    AREA = "area"
    POINT = "point"


class DataType(StringEnum):
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


class NoDataStrings(StringEnum):
    INF = "inf"
    NINF = "-inf"
    NAN = "nan"


class Statistics:
    """Represents statistics information attached to a band in the raster extension.

    Use Statistics.create to create a new Statistics instance.
    """

    properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Optional[float]]) -> None:
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
        """
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
    ) -> "Statistics":
        """
        Creates a new band.

        Args:
            minimum : Minimum value of all the pixels in the band.
            maximum : Maximum value of all the pixels in the band.
            mean : Mean value of all the pixels in the band.
            stddev : Standard Deviation value of all the pixels in the band.
            valid_percent : Percentage of valid (not nodata) pixel.
        """
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
        """Get or sets the minimum pixel value

        Returns:
            Optional[float]
        """
        return self.properties.get("minimum")

    @minimum.setter
    def minimum(self, v: Optional[float]) -> None:
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
    def maximum(self, v: Optional[float]) -> None:
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
    def mean(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties["mean"] = v
        else:
            self.properties.pop("mean", None)

    @property
    def stddev(self) -> Optional[float]:
        """Get or sets the standard deviation pixel value

        Returns:
            Optional[float]
        """
        return self.properties.get("stddev")

    @stddev.setter
    def stddev(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties["stddev"] = v
        else:
            self.properties.pop("stddev", None)

    @property
    def valid_percent(self) -> Optional[float]:
        """Get or sets the Percentage of valid (not nodata) pixel

        Returns:
            Optional[float]
        """
        return self.properties.get("valid_percent")

    @valid_percent.setter
    def valid_percent(self, v: Optional[float]) -> None:
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

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Statistics":
        """Constructs an Statistics from a dict.

        Returns:
            Statistics: The Statistics deserialized from the JSON dict.
        """
        return Statistics(properties=d)


class Histogram:
    """Represents pixel distribution information attached to a band in the raster extension.

    Use Band.create to create a new Band.
    """

    properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    def apply(
        self,
        count: int,
        min: float,
        max: float,
        buckets: List[int],
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
        """
        self.count = count
        self.min = min
        self.max = max
        self.buckets = buckets

    @classmethod
    def create(
        cls,
        count: int,
        min: float,
        max: float,
        buckets: List[int],
    ) -> "Histogram":
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
        """
        b = cls({})
        b.apply(
            count=count,
            min=min,
            max=max,
            buckets=buckets,
        )
        return b

    @property
    def count(self) -> int:
        """Get or sets the number of buckets of the distribution.

        Returns:
            int
        """
        return get_required(self.properties.get("count"), self, "count")

    @count.setter
    def count(self, v: int) -> None:
        self.properties["count"] = v

    @property
    def min(self) -> float:
        """Get or sets the minimum value of the distribution.

        Returns:
            float
        """
        return get_required(self.properties.get("min"), self, "min")

    @min.setter
    def min(self, v: float) -> None:
        self.properties["min"] = v

    @property
    def max(self) -> float:
        """Get or sets the maximum value of the distribution.

        Returns:
            float
        """
        return get_required(self.properties.get("max"), self, "max")

    @max.setter
    def max(self, v: float) -> None:
        self.properties["max"] = v

    @property
    def buckets(self) -> List[int]:
        """Get or sets the Array of integer indicating
        the number of pixels included in the bucket.

        Returns:
            List[int]
        """
        return get_required(self.properties.get("buckets"), self, "buckets")

    @buckets.setter
    def buckets(self, v: List[int]) -> None:
        self.properties["buckets"] = v

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of this histogram.

        Returns:
            dict: The wrapped dict of the Histogram that can be written out as JSON.
        """
        return self.properties

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Histogram":
        """Constructs an Histogram from a dict.

        Returns:
            Histogram: The Histogram deserialized from the JSON dict.
        """
        return Histogram(properties=d)


class RasterBand:
    """Represents a Raster Band information attached to an Item
    that implements the raster extension.

    Use Band.create to create a new Band.
    """

    properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    def apply(
        self,
        nodata: Optional[Union[float, NoDataStrings]] = None,
        sampling: Optional[Sampling] = None,
        data_type: Optional[DataType] = None,
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
            sampling : One of area or point. Indicates whether a pixel value should be
                assumed to represent a sampling over the region of the pixel or a point
                sample at the center of the pixel.
            data_type :The data type of the band.
                One of the data types as described in the
                :stac-ext:`Raster Data Types <raster/#data-types> docs`.
            bits_per_sample : The actual number of bits used for this band.
                Normally only present when the number of bits is non-standard for the
                datatype, such as when a 1 bit TIFF is represented as byte
            spatial_resolution : Average spatial resolution (in meters) of the pixels in
                the band.
            statistics: Statistics of all the pixels in the band
            unit: unit denomination of the pixel value
            scale: multiplicator factor of the pixel value to transform into the value
                (i.e. translate digital number to reflectance).
            offset: number to be added to the pixel value (after scaling) to transform
                into the value (i.e. translate digital number to reflectance).
            histogram: Histogram distribution information of the pixels values in the
                band
        """
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
        nodata: Optional[Union[float, NoDataStrings]] = None,
        sampling: Optional[Sampling] = None,
        data_type: Optional[DataType] = None,
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
            sampling : One of area or point. Indicates whether a pixel value should be
                assumed to represent a sampling over the region of the pixel or a point
                sample at the center of the pixel.
            data_type :The data type of the band.
                One of the data types as described in the
                :stac-ext:`Raster Data Types <raster/#data-types> docs`.
            bits_per_sample : The actual number of bits used for this band.
                Normally only present when the number of bits is non-standard for the
                datatype, such as when a 1 bit TIFF is represented as byte
            spatial_resolution : Average spatial resolution (in meters) of the pixels in
                the band.
            statistics: Statistics of all the pixels in the band
            unit: unit denomination of the pixel value
            scale: multiplicator factor of the pixel value to transform into the value
                (i.e. translate digital number to reflectance).
            offset: number to be added to the pixel value (after scaling) to transform
                into the value (i.e. translate digital number to reflectance).
            histogram: Histogram distribution information of the pixels values in the
                band
        """
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
    def nodata(self) -> Optional[Union[float, NoDataStrings]]:
        """Get or sets the nodata pixel value

        Returns:
            Optional[float]
        """
        return self.properties.get("nodata")

    @nodata.setter
    def nodata(self, v: Optional[Union[float, NoDataStrings]]) -> None:
        if v is not None:
            self.properties["nodata"] = v
        else:
            self.properties.pop("nodata", None)

    @property
    def sampling(self) -> Optional[Sampling]:
        """Get or sets the property indicating whether a pixel value should be assumed
        to represent a sampling over the region of the pixel or a point sample
        at the center of the pixel.

        Returns:
            Optional[Sampling]
        """
        return self.properties.get("sampling")

    @sampling.setter
    def sampling(self, v: Optional[Sampling]) -> None:
        if v is not None:
            self.properties["sampling"] = v
        else:
            self.properties.pop("sampling", None)

    @property
    def data_type(self) -> Optional[DataType]:
        """Get or sets the data type of the band.

        Returns:
            Optional[DataType]
        """
        return self.properties.get("data_type")

    @data_type.setter
    def data_type(self, v: Optional[DataType]) -> None:
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
        """Get or sets the average spatial resolution (in meters) of the pixels in the band.

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
        """Get or sets the average spatial resolution (in meters) of the pixels in the band.

        Returns:
            [Statistics]
        """
        return Statistics.from_dict(get_opt(self.properties.get("statistics")))

    @statistics.setter
    def statistics(self, v: Optional[Statistics]) -> None:
        if v is not None:
            self.properties["statistics"] = v.to_dict()
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
        """Get or sets the histogram distribution information of the pixels values in the band

        Returns:
            [Histogram]
        """
        return Histogram.from_dict(get_opt(self.properties.get("histogram")))

    @histogram.setter
    def histogram(self, v: Optional[Histogram]) -> None:
        if v is not None:
            self.properties["histogram"] = v.to_dict()
        else:
            self.properties.pop("histogram", None)

    def __repr__(self) -> str:
        return "<Raster Band>"

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of this Band.

        Returns:
            dict: The wrapped dict of the Band that can be written out as JSON.
        """
        return self.properties


class RasterExtension(
    PropertiesExtension, ExtensionManagementMixin[Union[pystac.Item, pystac.Collection]]
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Item` or :class:`~pystac.Asset` with properties from
    the :stac-ext:`Raster Extension <raster>`. This class is generic over
    the type of STAC Object to be extended (e.g. :class:`~pystac.Item`,
    :class:`~pystac.Asset`).

    This class will generally not be used directly. Instead, use the concrete
    implementation associated with the STAC Object you want to extend (e.g.
    :class:`~ItemRasterExtension` to extend an :class:`~pystac.Item`).
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
        return "<AssetRasterExtension Asset href={}>".format(self.asset_href)

    def apply(self, bands: List[RasterBand]) -> None:
        """Applies raster extension properties to the extended :class:`pystac.Item` or
        :class:`pystac.Asset`.

        Args:
            bands : a list of :class:`~pystac.RasterBand` objects that represent
                the available raster bands.
        """
        self.bands = bands

    @property
    def bands(self) -> Optional[List[RasterBand]]:
        """Gets or sets a list of available bands where each item is a :class:`~RasterBand`
        object (or ``None`` if no bands have been set). If not available the field
        should not be provided.
        """
        return self._get_bands()

    @bands.setter
    def bands(self, v: Optional[List[RasterBand]]) -> None:
        self._set_property(
            BANDS_PROP, map_opt(lambda bands: [b.to_dict() for b in bands], v)
        )

    def _get_bands(self) -> Optional[List[RasterBand]]:
        return map_opt(
            lambda bands: [RasterBand(b) for b in bands],
            self._get_property(BANDS_PROP, List[Dict[str, Any]]),
        )

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: pystac.Asset, add_if_missing: bool = False) -> "RasterExtension":
        """Extends the given STAC Object with properties from the :stac-ext:`Raster
        Extension <raster>`.

        This extension can be applied to instances of :class:`~pystac.Asset`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Asset):
            cls.validate_owner_has_extension(obj, add_if_missing)
            return cls(obj)
        else:
            raise pystac.ExtensionTypeError(
                f"Raster extension does not apply to type '{type(obj).__name__}'"
            )

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> "SummariesRasterExtension":
        cls.validate_has_extension(obj, add_if_missing)
        return SummariesRasterExtension(obj)


class SummariesRasterExtension(SummariesExtension):
    """A concrete implementation of :class:`~SummariesExtension` that extends
    the ``summaries`` field of a :class:`~pystac.Collection` to include properties
    defined in the :stac-ext:`Raster Extension <raster>`.
    """

    @property
    def bands(self) -> Optional[List[RasterBand]]:
        """Get or sets a list of :class:`~pystac.Band` objects that represent
        the available bands.
        """
        return map_opt(
            lambda bands: [RasterBand(b) for b in bands],
            self.summaries.get_list(BANDS_PROP),
        )

    @bands.setter
    def bands(self, v: Optional[List[RasterBand]]) -> None:
        self._set_summary(BANDS_PROP, map_opt(lambda x: [b.to_dict() for b in x], v))
