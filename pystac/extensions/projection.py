"""Implements the :stac-ext:`Projection Extension <projection>`."""

from __future__ import annotations

import json
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
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.serialization.identify import STACJSONDescription, STACVersionID

#: Generalized version of :class:`~pystac.Item`, :class:`~pystac.Asset`,
#: or :class:`~pystac.ItemAssetDefinition`
T = TypeVar("T", pystac.Item, pystac.Asset, pystac.ItemAssetDefinition)

SCHEMA_URI: str = "https://stac-extensions.github.io/projection/v2.0.0/schema.json"
SCHEMA_URIS: list[str] = [
    "https://stac-extensions.github.io/projection/v1.0.0/schema.json",
    "https://stac-extensions.github.io/projection/v1.1.0/schema.json",
    SCHEMA_URI,
]
PREFIX: str = "proj:"

# Field names
CODE_PROP: str = PREFIX + "code"
EPSG_PROP: str = PREFIX + "epsg"
WKT2_PROP: str = PREFIX + "wkt2"
PROJJSON_PROP: str = PREFIX + "projjson"
GEOM_PROP: str = PREFIX + "geometry"
BBOX_PROP: str = PREFIX + "bbox"
CENTROID_PROP: str = PREFIX + "centroid"
SHAPE_PROP: str = PREFIX + "shape"
TRANSFORM_PROP: str = PREFIX + "transform"


class ProjectionExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Item` with properties from the :stac-ext:`Projection
    Extension <projection>`. This class is generic over the type of STAC Object to be
    extended (e.g. :class:`~pystac.Item`, :class:`~pystac.Collection`).

    To create a concrete instance of :class:`ProjectionExtension`, use the
    :meth:`ProjectionExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> proj_ext = ProjectionExtension.ext(item)
    """

    name: Literal["proj"] = "proj"

    def apply(
        self,
        *,
        epsg: int | None = None,
        code: str | None = None,
        wkt2: str | None = None,
        projjson: dict[str, Any] | None = None,
        geometry: dict[str, Any] | None = None,
        bbox: list[float] | None = None,
        centroid: dict[str, float] | None = None,
        shape: list[int] | None = None,
        transform: list[float] | None = None,
    ) -> None:
        """Applies Projection extension properties to the extended Item.

        Args:
            epsg : Code of the datasource. Example: 4326.  One of ``code`` and
                ``epsg`` must be provided.
            code : Code of the datasource. Example: "EPSG:4326". One of ``code`` and
                ``epsg`` must be provided.
            wkt2 : WKT2 string representing the Coordinate Reference
                System (CRS) that the ``geometry`` and ``bbox`` fields represent
            projjson : PROJJSON dict representing the
                Coordinate Reference System (CRS) that the ``geometry`` and ``bbox``
                fields represent
            geometry : GeoJSON Polygon dict that defines the footprint of
                this Item.
            bbox : Bounding box of the Item in the asset CRS in
                2 or 3 dimensions.
            centroid : A dict with members 'lat' and 'lon' that defines
                coordinates representing the centroid of the item in the asset data CRS.
                Coordinates are defined in latitude and longitude, even if the data
                coordinate system may not use lat/long.
            shape : Number of pixels in Y and X directions for the
                default grid.
            transform : The affine transformation coefficients for
                the default grid
        """
        if epsg is not None and code is not None:
            raise KeyError(
                "Only one of the options ``code`` and ``epsg`` should be specified."
            )
        elif epsg:
            self.epsg = epsg
        else:
            self.code = code

        self.wkt2 = wkt2
        self.projjson = projjson
        self.geometry = geometry
        self.bbox = bbox
        self.centroid = centroid
        self.shape = shape
        self.transform = transform

    @property
    def epsg(self) -> int | None:
        """Get or sets the EPSG code of the datasource.

        A Coordinate Reference System (CRS) is the data reference system (sometimes
        called a 'projection') used by the asset data, and can usually be referenced
        using an `EPSG code <https://epsg.io/>`_.
        If the asset data does not have a CRS, such as in the case of non-rectified
        imagery with Ground Control Points, ``epsg`` should be set to ``None``.
        It should also be set to ``None`` if a CRS exists, but for which there is no
        valid EPSG code.
        """
        if self.code is not None and self.code.startswith("EPSG:"):
            return int(self.code.replace("EPSG:", ""))
        elif epsg := self._get_property(
            EPSG_PROP, int
        ):  # In case the dictionary was not migrated
            return epsg
        return None

    @epsg.setter
    def epsg(self, v: int | None) -> None:
        if v is None:
            self.code = None
        else:
            self.code = f"EPSG:{v}"

    @property
    def code(self) -> str | None:
        """Get or set the code of the datasource.

        Added in version 2.0.0 of this extension replacing "proj:epsg".

        Projection codes are identified by a string. The `proj <https://proj.org/>`_
        library defines projections using "authority:code", e.g., "EPSG:4326" or
        "IAU_2015:30100". Different projection authorities may define different
        string formats.
        """
        return self._get_property(CODE_PROP, str)

    @code.setter
    def code(self, v: int | None) -> None:
        self._set_property(CODE_PROP, v, pop_if_none=False)

    @property
    def wkt2(self) -> str | None:
        """Get or sets the WKT2 string representing the Coordinate Reference System
        (CRS) that the ``proj:geometry`` and ``proj:bbox`` fields represent

        This value is a
        `WKT2 string <https://docs.opengeospatial.org/is/12-063r5/12-063r5.html>`_.
        If the data does not have a CRS, such as in the case of non-rectified imagery
        with Ground Control Points, ``wkt2`` should be set to ``None``. It should also
        be set to ``None`` if a CRS exists, but for which a WKT2 string does not exist.
        """
        return self._get_property(WKT2_PROP, str)

    @wkt2.setter
    def wkt2(self, v: str | None) -> None:
        self._set_property(WKT2_PROP, v)

    @property
    def projjson(self) -> dict[str, Any] | None:
        """Get or sets the PROJJSON string representing the Coordinate Reference System
        (CRS) that the ``proj:geometry`` and ``proj:bbox`` fields represent

        This value is a
        `PROJJSON object <https://proj.org/specifications/projjson.html>`_.
        If the data does not have a CRS, such as in the case of non-rectified imagery
        with Ground Control Points, ``projjson`` should be set to ``None``. It should
        also be set to ``None`` if a CRS exists, but for which a PROJJSON string does
        not exist.

        The schema for this object can be found
        `here <https://proj.org/schemas/v0.2/projjson.schema.json>`_.
        """
        return self._get_property(PROJJSON_PROP, dict[str, Any])

    @projjson.setter
    def projjson(self, v: dict[str, Any] | None) -> None:
        self._set_property(PROJJSON_PROP, v)

    @property
    def crs_string(self) -> str | None:
        """Returns the coordinate reference system (CRS) string for the extension.

        This string can be used to feed, e.g., ``rasterio.crs.CRS.from_string``.
        The string is determined by the following heuristic:

        1. If a code is set, return the code string, else
        2. If wkt2 is set, return the WKT string, else,
        3. If projjson is set, return the projjson as a string, else,
        4. Return None
        """
        if self.code:
            return self.code
        elif self.epsg:
            return f"EPSG:{self.epsg}"
        elif self.wkt2:
            return self.wkt2
        elif self.projjson:
            return json.dumps(self.projjson)
        else:
            return None

    @property
    def geometry(self) -> dict[str, Any] | None:
        """Get or sets a Polygon GeoJSON dict representing the footprint of this item.

        This dict should be formatted according the Polygon object format specified in
        `RFC 7946, sections 3.1.6 <https://tools.ietf.org/html/rfc7946>`_,
        except not necessarily in EPSG:4326 as required by RFC7946. Specified based on
        the ``code``, ``projjson`` or ``wkt2`` fields (not necessarily EPSG:4326).
        Ideally, this will be represented by a Polygon with five coordinates, as the
        item in the asset data CRS should be a square aligned to the original CRS grid.
        """
        return self._get_property(GEOM_PROP, dict[str, Any])

    @geometry.setter
    def geometry(self, v: dict[str, Any] | None) -> None:
        self._set_property(GEOM_PROP, v)

    @property
    def bbox(self) -> list[float] | None:
        """Get or sets the bounding box of the assets represented by this item in the
        asset data CRS.

        Specified as 4 or 6 coordinates based on the CRS defined in the ``code``,
        ``projjson`` or ``wkt2`` properties. First two numbers are coordinates of the
        lower left corner, followed by coordinates of upper right corner, e.g.,
        ``[west, south, east, north]``, ``[xmin, ymin, xmax, ymax]``,
        ``[left, down, right, up]``, or ``[west, south, lowest, east, north,
        highest]``. The length of the array must be 2*n where n is the number of
        dimensions.
        """
        return self._get_property(BBOX_PROP, list[float])

    @bbox.setter
    def bbox(self, v: list[float] | None) -> None:
        self._set_property(BBOX_PROP, v)

    @property
    def centroid(self) -> dict[str, float] | None:
        """Get or sets coordinates representing the centroid of the item in the asset
        data CRS.

        Coordinates are defined in latitude and longitude, even if the data coordinate
        system does not use lat/long.

        Example::

            item.ext.proj.centroid = { 'lat': 0.0, 'lon': 0.0 }
        """
        return self._get_property(CENTROID_PROP, dict[str, float])

    @centroid.setter
    def centroid(self, v: dict[str, float] | None) -> None:
        self._set_property(CENTROID_PROP, v)

    @property
    def shape(self) -> list[int] | None:
        """Get or sets the number of pixels in Y and X directions for the default grid.

        The shape is an array of integers that represents the number of pixels in the
        most common pixel grid used by the item's assets. The number of pixels should
        be specified in Y, X order. If the shape is defined in an item's properties it
        is used as the default shape for all assets that don't have an overriding shape.
        """
        return self._get_property(SHAPE_PROP, list[int])

    @shape.setter
    def shape(self, v: list[int] | None) -> None:
        self._set_property(SHAPE_PROP, v)

    @property
    def transform(self) -> list[float] | None:
        """Get or sets the the affine transformation coefficients for the default grid.

        The transform is a linear mapping from pixel coordinate space (Pixel, Line) to
        projection coordinate space (Xp, Yp). It is a 3x3 matrix stored as a flat array
        of 9 elements in row major order. Since the last row is always 0,0,1 it can be
        omitted, in which case only 6 elements are recorded. This mapping can be
        obtained from GDAL `GetGeoTransform <https://gdal.org/api/gdaldataset_cpp.html\
#_CPPv4N11GDALDataset15GetGeoTransformEPd>`_
        or the Rasterio `Transform <https://rasterio.readthedocs.io/en/stable/api\
/rasterio.io.html#rasterio.io.BufferedDatasetWriter.transform>`_.
        """
        return self._get_property(TRANSFORM_PROP, list[float])

    @transform.setter
    def transform(self, v: list[float] | None) -> None:
        self._set_property(TRANSFORM_PROP, v)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def get_schema_uris(cls) -> list[str]:
        warnings.warn(
            "get_schema_uris is deprecated and will be removed in v2",
            DeprecationWarning,
        )
        return SCHEMA_URIS

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> ProjectionExtension[T]:
        """Extends the given STAC Object with properties from the :stac-ext:`Projection
        Extension <projection>`.

        This extension can be applied to instances of :class:`~pystac.Item` or
        :class:`~pystac.Asset`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(ProjectionExtension[T], ItemProjectionExtension(obj))
        elif isinstance(obj, pystac.Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(ProjectionExtension[T], AssetProjectionExtension(obj))
        elif isinstance(obj, pystac.ItemAssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(ProjectionExtension[T], ItemAssetsProjectionExtension(obj))
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesProjectionExtension:
        """Returns the extended summaries object for the given collection."""
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesProjectionExtension(obj)


class ItemProjectionExtension(ProjectionExtension[pystac.Item]):
    """A concrete implementation of :class:`ProjectionExtension` on an
    :class:`~pystac.Item` that extends the properties of the Item to include properties
    defined in the :stac-ext:`Projection Extension <projection>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`ProjectionExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: pystac.Item
    """The :class:`~pystac.Item` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Item` properties, including extension properties."""

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemProjectionExtension Item id={self.item.id}>"


class AssetProjectionExtension(ProjectionExtension[pystac.Asset]):
    """A concrete implementation of :class:`ProjectionExtension` on an
    :class:`~pystac.Asset` that extends the Asset fields to include properties defined
    in the :stac-ext:`Projection Extension <projection>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`ProjectionExtension.ext` on an :class:`~pystac.Asset` to extend it.
    """

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
        return f"<AssetProjectionExtension Asset href={self.asset_href}>"


class ItemAssetsProjectionExtension(ProjectionExtension[pystac.ItemAssetDefinition]):
    properties: dict[str, Any]
    asset_defn: pystac.ItemAssetDefinition

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        self.asset_defn = item_asset
        self.properties = item_asset.properties


class SummariesProjectionExtension(SummariesExtension):
    """A concrete implementation of :class:`~pystac.extensions.base.SummariesExtension`
    that extends the ``summaries`` field of a :class:`~pystac.Collection` to include
    properties defined in the :stac-ext:`Projection Extension <projection>`.
    """

    @property
    def code(self) -> list[str] | None:
        """Get or sets the summary of :attr:`ProjectionExtension.code` values
        for this Collection.
        """
        return self.summaries.get_list(CODE_PROP)

    @code.setter
    def code(self, v: list[str] | None) -> None:
        self._set_summary(CODE_PROP, v)

    @property
    def epsg(self) -> list[int] | None:
        """Get the summary of :attr:`ProjectionExtension.epsg` values
        for this Collection.
        """
        if self.code is None:
            return None
        return [int(code.replace("EPSG:", "")) for code in self.code if "EPSG:" in code]

    @epsg.setter
    def epsg(self, v: list[int] | None) -> None:
        if v is None:
            self.code = None
        else:
            self.code = [f"EPSG:{epsg}" for epsg in v]


class ProjectionExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {
        "proj",
        "projection",
        *[uri for uri in SCHEMA_URIS if uri != SCHEMA_URI],
    }
    pre_2 = {
        "proj",
        "projection",
        "https://stac-extensions.github.io/projection/v1.0.0/schema.json",
        "https://stac-extensions.github.io/projection/v1.1.0/schema.json",
    }
    stac_object_types = {pystac.STACObjectType.ITEM}

    def migrate(
        self, obj: dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        if not self.has_extension(obj):
            return

        # proj:epsg moved to proj:code
        if epsg := obj["properties"].pop("proj:epsg", None):
            obj["properties"]["proj:code"] = f"EPSG:{epsg}"

        for key in ["assets", "item_assets"]:
            for asset in obj.get(key, {}).values():
                if epsg := asset.pop("proj:epsg", None):
                    asset["proj:code"] = f"EPSG:{epsg}"

        super().migrate(obj, version, info)


PROJECTION_EXTENSION_HOOKS: ExtensionHooks = ProjectionExtensionHooks()
