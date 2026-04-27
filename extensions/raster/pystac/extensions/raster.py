"""Implements the :stac-ext:`Raster Extension <raster>`."""

from __future__ import annotations

import json
import warnings
from collections import Counter
from collections.abc import Iterable
from typing import (
    Any,
    Generic,
    Literal,
    Optional,
    TypeVar,
    cast,
)

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.utils import StringEnum, get_required, map_opt


class _RasterBandCompat(pystac.Band):
    """Compatibility class for older versions of RasterBand

    This is **exclusively** for `pystac.Band` compatibility issues.
    Do not use it as a traditional Python import.
    """

    @classmethod
    def create(  # type: ignore[override]
        cls,
        nodata: float | pystac.NoDataStrings | None = None,
        sampling: Sampling | None = None,
        data_type: pystac.DataType | None = None,
        bits_per_sample: float | None = None,
        spatial_resolution: float | None = None,
        statistics: pystac.Statistics | None = None,
        unit: str | None = None,
        scale: float | None = None,
        offset: float | None = None,
        histogram: Histogram | None = None,
    ) -> pystac.Band:
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
        warnings.warn(
            "RasterBand is deprecated  since v2.0.0 and will be "
            "replaced by pystac.Band for raster attributes instead. Please consult "
            "the release notes (https://github.com/stac-extensions/raster/releases/tag/v2.0.0)"
            " for more details."
            "Use pystac.Band with band.ext.raster for raster fields instead:\n"
            "  band = pystac.Band.create('B01')\n"
            "  band.ext.raster.bits_per_sample = 15\n"
            "  band.ext.raster.sampling = 'area'\n"
            "  band.ext.raster.histogram = Histogram(min=0, max=255)",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().create(
            name=None,
            description=None,
            extra_fields={
                "nodata": nodata,
                "data_type": data_type,
                "statistics": statistics,
                "unit": unit,
                "raster:sampling": sampling,
                "raster:bits_per_sample": bits_per_sample,
                "raster:spatial_resolution": spatial_resolution,
                "raster:scale": scale,
                "raster:offset": offset,
                "raster:histogram": histogram,
            },
        )

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> _RasterBandCompat:
        # Reuse base validation and field parsing, but construct as _EOBandCompat
        # so that common_name and other eo: properties are accessible via get_prop()
        base = pystac.Band.from_dict(
            d
        )  # handles empty-dict validation and extra_fields parsing
        return cls(
            name=base.name,
            description=base.description,
            extra_fields=base.extra_fields,
        )

    # old properties
    @property
    def nodata(self) -> float | pystac.NoDataStrings | None:
        """Get or sets the nodata pixel value

        Returns:
            Optional[float]
        """
        return cast(Optional[pystac.NoDataStrings], self.get_prop("no_data"))

    @nodata.setter
    def nodata(self, v: float | pystac.NoDataStrings | None) -> None:
        self.set_prop("no_data", v)

    @property
    def sampling(self) -> Sampling | None:
        """Get or sets the property indicating whether a pixel value should be assumed
        to represent a sampling over the region of the pixel or a point sample
        at the center of the pixel.

        Returns:
            Optional[Sampling]
        """
        return cast(Optional[Sampling], self.get_prop("raster:sampling"))

    @sampling.setter
    def sampling(self, v: Sampling | None) -> None:
        self.set_prop("raster:sampling", v)

    @property
    def data_type(self) -> pystac.DataType | None:
        """Get or sets the data type of the band.

        Returns:
            Optional[DataType]
        """
        return cast(Optional[pystac.DataType], self.get_prop("data_type"))

    @data_type.setter
    def data_type(self, v: pystac.DataType | None) -> None:
        self.set_prop("data_type", v)

    @property
    def bits_per_sample(self) -> float | None:
        """Get or sets the actual number of bits used for this band.

        Returns:
            float
        """
        return cast(Optional[float], self.get_prop("raster:bits_per_sample"))

    @bits_per_sample.setter
    def bits_per_sample(self, v: float | None) -> None:
        self.set_prop("raster:bits_per_sample", v)

    @property
    def spatial_resolution(self) -> float | None:
        """Get or sets the average spatial resolution (in meters) of the pixels in the
        band.

        Returns:
            [float]
        """
        return cast(Optional[float], self.get_prop("raster:spatial_resolution"))

    @spatial_resolution.setter
    def spatial_resolution(self, v: float | None) -> None:
        self.set_prop("raster:spatial_resolution", v)

    @property
    def statistics(self) -> pystac.Statistics | None:
        """Get or sets the average spatial resolution (in meters) of the pixels in the
        band.

        Returns:
            [Statistics]
        """
        return cast(Optional[pystac.Statistics], self.get_prop("statistics"))

    @statistics.setter
    def statistics(self, v: pystac.Statistics | None) -> None:
        self.set_prop("statistics", v)

    @property
    def unit(self) -> str | None:
        """Get or sets the unit denomination of the pixel value

        Returns:
            [str]
        """
        return cast(Optional[str], self.get_prop("unit"))

    @unit.setter
    def unit(self, v: str | None) -> None:
        self.set_prop("unit", v)

    @property
    def scale(self) -> float | None:
        """Get or sets the multiplicator factor of the pixel value to transform
        into the value (i.e. translate digital number to reflectance).

        Returns:
            [float]
        """
        return cast(Optional[float], self.get_prop("raster:scale"))

    @scale.setter
    def scale(self, v: float | None) -> None:
        self.set_prop("raster:scale", v)

    @property
    def offset(self) -> float | None:
        """Get or sets the number to be added to the pixel value (after scaling)
        to transform into the value (i.e. translate digital number to reflectance).

        Returns:
            [float]
        """
        return cast(Optional[float], self.get_prop("raster:float"))

    @offset.setter
    def offset(self, v: float | None) -> None:
        self.set_prop("raster:offset", v)

    @property
    def histogram(self) -> Histogram | None:
        """Get or sets the histogram distribution information of the pixels values in
        the band.

        Returns:
            [Histogram]
        """
        return cast(Optional[Histogram], self.get_prop("raster:histogram"))

    @histogram.setter
    def histogram(self, v: Histogram | None) -> None:
        self.set_prop("raster:histogram", v)

    def __repr__(self) -> str:
        return "<Raster Band>"


def __getattr__(name: str) -> object:
    if name == "RasterBand":
        import warnings

        warnings.warn(
            "RasterBand is deprecated  since v2.0.0 and will be "
            "replaced by pystac.Band for raster attributes instead. Please consult "
            "the release notes (https://github.com/stac-extensions/raster/releases/tag/v2.0.0)"
            " for more details."
            "Use pystac.Band with band.ext.raster for raster fields instead:\n"
            "  band = pystac.Band.create('B01')\n"
            "  band.ext.raster.bits_per_sample = 15\n"
            "  band.ext.raster.sampling = 'area'\n"
            "  band.ext.raster.histogram = Histogram(min=0, max=255)",
            DeprecationWarning,
            stacklevel=2,
        )

        return _RasterBandCompat
    raise AttributeError(f"module 'pystac.extensions.raster' has no attribute {name!r}")


#: Generalized version of :class:`~pystac.Asset` or
#: :class:`~pystac.ItemAssetDefinition`
T = TypeVar("T", pystac.Asset, pystac.ItemAssetDefinition, pystac.Band)

SCHEMA_URI = "https://stac-extensions.github.io/raster/v2.0.0/schema.json"
SCHEMA_URIS = [
    "https://stac-extensions.github.io/raster/v1.1.0/schema.json",
    "https://stac-extensions.github.io/raster/v1.0.0/schema.json",
    SCHEMA_URI,
]
SCHEMA_STARTWITH = "https://stac-extensions.github.io/raster/"

PREFIX: str = "raster:"

BANDS_PROP: str = PREFIX + "bands"  # Deprecated
# Field names
# Can be used in Assets and Item properties
SAMPLING_PROP = PREFIX + "sampling"
BITS_PER_SAMPLE_PROP = PREFIX + "bits_per_sample"
SPATIAL_RESOLUTION_PROP = PREFIX + "spatial_resolution"
SCALE_PROP = PREFIX + "scale"
OFFSET_PROP = PREFIX + "offset"
HISTOGRAM_PROP = PREFIX + "histogram"


class Sampling(StringEnum):
    AREA = "area"
    POINT = "point"


# Renamed to raster:histogram
class Histogram:
    """Represents pixel distribution information attached to a band in the raster
    extension.

    Use Band.create to create a new Band.
    """

    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]) -> None:
        self.properties = properties

    def apply(
        self,
        count: int,
        min: float,
        max: float,
        buckets: list[int],
    ) -> None:
        """
        Sets the properties for this raster Band.

        Args:
            count : number of buckets of the distribution.
            min : minimum value of the distribution.
                Also, the mean value of the first bucket.
            max : maximum value of the distribution.
                Also, the mean value of the last bucket.
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
        buckets: list[int],
    ) -> Histogram:
        """
        Creates a new band.

        Args:
            count : number of buckets of the distribution.
            min : minimum value of the distribution.
                Also, the mean value of the first bucket.
            max : maximum value of the distribution.
                Also, the mean value of the last bucket.
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
        return cast(int, get_required(self.properties.get("count"), self, "count"))

    @count.setter
    def count(self, v: int) -> None:
        self.properties["count"] = v

    @property
    def min(self) -> float:
        """Get or sets the minimum value of the distribution.

        Returns:
            float
        """
        return cast(float, get_required(self.properties.get("min"), self, "min"))

    @min.setter
    def min(self, v: float) -> None:
        self.properties["min"] = v

    @property
    def max(self) -> float:
        """Get or sets the maximum value of the distribution.

        Returns:
            float
        """
        return cast(float, get_required(self.properties.get("max"), self, "max"))

    @max.setter
    def max(self, v: float) -> None:
        self.properties["max"] = v

    @property
    def buckets(self) -> list[int]:
        """Get or sets the Array of integer indicating
        the number of pixels included in the bucket.

        Returns:
            List[int]
        """
        return get_required(self.properties.get("buckets"), self, "buckets")

    @buckets.setter
    def buckets(self, v: list[int]) -> None:
        self.properties["buckets"] = v

    def to_dict(self) -> dict[str, Any]:
        """Returns this histogram as a dictionary.

        Returns:
            dict: The serialization of the Histogram.
        """
        return self.properties

    @staticmethod
    def from_dict(d: dict[str, Any]) -> Histogram:
        """Constructs a Histogram from a dict.

        Returns:
            Histogram: The Histogram deserialized from the JSON dict.
        """
        return Histogram(properties=d)


class RasterExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Asset`, or
    :class:`~pystac.ItemAssetDefinition` with properties from
    the :stac-ext:`Raster Extension <raster>`. This class is generic over
    the type of STAC Object to be extended (e.g. :class:`~pystac.Item`,
    :class:`~pystac.Asset`).

    This class will generally not be used directly. Instead, use the concrete
    implementation associated with the STAC Object you want to extend (e.g.
    :class:`~AssetRasterExtension` to extend an :class:`~pystac.Item`).  You may
    prefer to use the `ext` class method of this class to construct the correct
    instance type for you.
    """

    name: Literal["raster"] = "raster"

    properties: dict[str, Any]
    """The :class:`~pystac.Asset` fields, including extension properties."""

    def apply(
        self,
        sampling: Sampling | None = None,
        bits_per_sample: float | None = None,
        spatial_resolution: float | None = None,
        scale: float | None = None,
        offset: float | None = None,
        histogram: Histogram | None = None,
    ) -> None:
        """Applies raster extension properties to the extended :class:`pystac.Item` or
        :class:`pystac.Asset`.

        Args:
            sampling: One of area or point. Indicates whether a pixel value
                should be assumed to represent a sampling over the region of the
                pixel or a point sample at the center of the pixel.
            bits_per_sample: The actual number of bits used for this band. Normally
                only present when the number of bits is non-standard for the
                datatype, such as when a 1 bit TIFF is represented as byte.
            spatial_resolution: Average spatial resolution (in meters) of the
                pixels in the band.
            scale: Multiplicator factor of the pixel value to transform into the
                value (i.e. translate digital number to reflectance).
            offset: Number to be added to the pixel value (after scaling) to
                transform into the value (i.e. translate digital number to reflectance).
            histogram: Histogram distribution information of the pixels values in the
                band.
        """
        self.sampling = sampling
        self.bits_per_sample = bits_per_sample
        self.spatial_resolution = spatial_resolution
        self.scale = scale
        self.offset = offset
        self.histogram = histogram

    # sampling
    @property
    def sampling(self) -> Sampling | None:
        return self._get_property(SAMPLING_PROP, Sampling)

    @sampling.setter
    def sampling(self, v: Sampling | None) -> None:
        self._set_property(SAMPLING_PROP, v, pop_if_none=True)

    # bits_per_sample
    @property
    def bits_per_sample(self) -> float | None:
        return self._get_property(BITS_PER_SAMPLE_PROP, float)

    @bits_per_sample.setter
    def bits_per_sample(self, v: float | None) -> None:
        self._set_property(BITS_PER_SAMPLE_PROP, v, pop_if_none=True)

    # spatial_resolution
    @property
    def spatial_resolution(self) -> float | None:
        return self._get_property(SPATIAL_RESOLUTION_PROP, float)

    @spatial_resolution.setter
    def spatial_resolution(self, v: float | None) -> None:
        self._set_property(SPATIAL_RESOLUTION_PROP, v, pop_if_none=True)

    # scale
    @property
    def scale(self) -> float | None:
        return self._get_property(SCALE_PROP, float)

    @scale.setter
    def scale(self, v: float | None) -> None:
        self._set_property(SCALE_PROP, v, pop_if_none=True)

    # offset
    @property
    def offset(self) -> float | None:
        return self._get_property(OFFSET_PROP, float)

    @offset.setter
    def offset(self, v: float | None) -> None:
        self._set_property(OFFSET_PROP, v, pop_if_none=True)

    @property
    def histogram(self) -> Histogram | None:
        """Get or sets the histogram distribution information of the pixels values in
        the STAC object.

        Returns:
            [Histogram]
        """
        return map_opt(
            Histogram.from_dict,
            self._get_property(HISTOGRAM_PROP, dict[str, Any]),
        )

    @histogram.setter
    def histogram(self, v: Histogram | None) -> None:
        self._set_property(HISTOGRAM_PROP, map_opt(lambda h: h.to_dict(), v))

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
    def ext(cls, obj: T, add_if_missing: bool = False) -> RasterExtension[T]:
        """Extends the given STAC Object with properties from the :stac-ext:`Raster
        Extension <raster>`.

        This extension can be applied to instances of :class:`~pystac.Asset`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(RasterExtension[T], AssetRasterExtension(obj))
        elif isinstance(obj, pystac.ItemAssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(RasterExtension[T], ItemAssetsRasterExtension(obj))
        elif isinstance(obj, pystac.Band):
            # No need to check for owner for now
            return cast(RasterExtension[T], BandRasterExtension(obj))
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesRasterExtension:
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesRasterExtension(obj)

    # Utils for bands
    def get_bands(self) -> list[RasterExtension[pystac.Band]] | None:
        """Returns bands with the Raster Extension loaded"""
        pass

    def get_statistics(self) -> pystac.Statistics | None:
        pass

    # Deprecated
    @property
    def bands(self) -> list[_RasterBandCompat] | None:
        """Gets or sets a list of available bands where each item is a
        :class:`~RasterBand` object (or ``None`` if no bands have been set). If not
        available the field should not be provided.
        """
        warnings.warn(
            "RasterBand is deprecated  since v2.0.0 and will be "
            "replaced by pystac.Band for raster attributes instead. Please consult "
            "the release notes (https://github.com/stac-extensions/raster/releases/tag/v2.0.0)"
            " for more details."
            "Use pystac.Band with band.ext.raster for raster fields instead:\n"
            "  band = pystac.Band.create('B01')\n"
            "  band.ext.raster.bits_per_sample = 15\n"
            "  band.ext.raster.sampling = 'area'\n"
            "  band.ext.raster.histogram = Histogram(min=0, max=255)",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._get_bands()

    @bands.setter
    def bands(self, v: list[pystac.Band] | None) -> None:
        warnings.warn(
            "RasterBand is deprecated  since v2.0.0 and will be "
            "replaced by pystac.Band for raster attributes instead. Please consult "
            "the release notes (https://github.com/stac-extensions/raster/releases/tag/v2.0.0)"
            " for more details."
            "Use pystac.Band with band.ext.raster for raster fields instead:\n"
            "  band = pystac.Band.create('B01')\n"
            "  band.ext.raster.bits_per_sample = 15\n"
            "  band.ext.raster.sampling = 'area'\n"
            "  band.ext.raster.histogram = Histogram(min=0, max=255)",
            DeprecationWarning,
            stacklevel=2,
        )
        self._set_bands(v)

    def _get_bands(self) -> list[_RasterBandCompat] | None:
        pass

    def _set_bands(self, v: list[pystac.Band] | None) -> None:
        pass


class AssetRasterExtension(RasterExtension[pystac.Asset]):
    asset_href: str
    """The ``href`` value of the :class:`~pystac.Asset` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Asset` fields, including extension properties."""

    additional_read_properties: Iterable[dict[str, Any]] | None = None
    """If present, this will be a list containing 1 dictionary representing the
    properties of the owning :class:`~pystac.Item`."""

    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return f"<AssetRasterExtension Asset href={self.asset_href}>"

    def get_bands(self) -> list[RasterExtension[pystac.Band]] | None:
        if "bands" not in self.properties:
            return None
        return list(
            map(
                lambda band: RasterExtension.ext(pystac.Band.from_dict(band)),
                cast(list[dict[str, Any]], self.properties.get("bands")),
            )
        )

    # Deprecated
    def _get_bands(self) -> list[_RasterBandCompat] | None:
        if "bands" not in self.properties:
            return None
        return list(
            map(
                lambda band: _RasterBandCompat.from_dict(band),
                cast(list[dict[str, Any]], self.properties.get("bands")),
            )
        )

    def _set_bands(self, v: list[pystac.Band] | None) -> None:
        if v is not None:
            self.properties["bands"] = [b.to_dict() for b in v]


class ItemAssetsRasterExtension(RasterExtension[pystac.ItemAssetDefinition]):
    asset_definition: pystac.ItemAssetDefinition
    """A reference to the :class:`~pystac.ItemAssetDefinition`
    being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.ItemAssetDefinition` fields, including
    extension properties."""

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        self.properties = item_asset.properties
        self.asset_definition = item_asset

    def __repr__(self) -> str:
        return "<ItemAssetsRasterExtension AssetDefinition={}>".format(
            self.asset_definition
        )


class BandRasterExtension(RasterExtension[pystac.Band]):
    def __init__(self, band: pystac.Band) -> None:
        self.band_name = band.name
        self.description = band.description
        self.properties = band.extra_fields

    def __repr__(self) -> str:
        return f"<BandRasterExtension Band name={self.band_name}>"

    def get_statistics(self) -> pystac.Statistics | None:
        statistics = self.properties.get("statistics")

        if statistics is not None:
            return pystac.Statistics.from_dict(statistics)

        return None


class SummariesRasterExtension(SummariesExtension):
    """A concrete implementation of :class:`~pystac.extensions.base.SummariesExtension`
    that extends the ``summaries`` field of a :class:`~pystac.Collection` to include
    properties defined in the :stac-ext:`Raster Extension <raster>`.
    """

    def get_bands(self) -> list[RasterExtension[pystac.Band]] | None:
        bands = self.summaries.get_list("bands")

        if bands is not None:
            return [RasterExtension.ext(pystac.Band.from_dict(b)) for b in bands]

        return None


class RasterExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: set[str] = {
        "raster",
        *[uri for uri in SCHEMA_URIS if uri != SCHEMA_URI],
    }
    stac_object_types = {pystac.STACObjectType.ITEM, pystac.STACObjectType.COLLECTION}

    def _migrate_obj_with_bands(self, obj: dict[str, Any]) -> None:
        """Migrates objects from raster:band to band and moves common metadata
        to item, collection summary or asset

        - If object is a STAC Item, pass obj["properties"]
        - If object is an item asset, pass the asset
        """
        if "raster:bands" not in obj:
            return None

        # Fields present in the new band asset
        common_band_fields = frozenset(["name", "description"])
        # Fields promoted to item/asset metadata
        common_metadata_fields = frozenset(
            ["nodata", "data_type", "statistics", "unit"]
        )
        # Fields remaining in the band or the asset, but prefixed to
        # raster instead
        to_be_renamed = frozenset(
            [
                "sampling",
                "bits_per_sample",
                "spatial_resolution",
                "scale",
                "offset",
                "histogram",
            ]
        )

        raster_fields = common_band_fields | common_metadata_fields | to_be_renamed

        old_bands = obj.pop("raster:bands")

        if old_bands and isinstance(old_bands[0], int):
            return None

        def transform_band(band_obj: dict[str, Any]) -> dict[str, Any]:
            return {
                (PREFIX + k if k in to_be_renamed else k): v
                for k, v in band_obj.items()
                if k in raster_fields
            }

        # Create the bands ; they won't have any names however
        if "bands" not in obj:
            obj["bands"] = [transform_band(band) for band in old_bands]

        # Bands from EO already exist and have a name
        elif "bands" in obj and len(obj["bands"]) == len(old_bands):
            for band, old_band in zip(obj["bands"], old_bands):
                band.update(transform_band(old_band))

        # Once "bands" is created, identify and remove duplicates
        # Dominant element must be set on the property
        # Minor elements can stay in the bands
        bands = obj["bands"]
        n_elements = len(bands)
        # One band, most metadata goes back up into the asset/item

        promotable = (
            frozenset([PREFIX + k for k in to_be_renamed]) | common_metadata_fields
        )

        counters: dict[str, Counter[str]] = {
            key: Counter(
                json.dumps(band[key], sort_keys=True) for band in bands if key in band
            )
            for key in promotable
        }

        for k, counter in counters.items():
            if counter.total() != n_elements:  # field missing from at least one band
                continue
            dom_element, dom_count = counter.most_common(1)[0]

            if dom_count == 1 and len(bands) > 1:
                continue

            obj[k] = json.loads(dom_element)
            for band in bands:
                if json.dumps(band.get(k), sort_keys=True) == dom_element:
                    del band[k]

        # Next make sure "bands" is empty
        if all([len(b) == 0 for b in bands]):
            del obj["bands"]

    def migrate(
        self, obj: dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:

        # Bands moved to common metadata
        #
        # Content proper to bands has been renamed as raster:<field>
        # Fields affected: sampling, bits_per_sample, spatial_resolution, scale
        # offset and histogram
        #
        # nodata, data_type, statistics and unit were not renamed, but have been moved
        # to STAC common metadata

        if version < "2.0.0":
            # if "eo:bands" in obj.get("properties", {}):
            if "properties" in obj:
                self._migrate_obj_with_bands(obj["properties"])
                if "assets" in obj.keys():
                    for asset in obj["assets"].values():
                        self._migrate_obj_with_bands(asset)

        super().migrate(obj, version, info)


RASTER_EXTENSION_HOOKS: ExtensionHooks = RasterExtensionHooks()
