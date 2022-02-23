"""Implements the :stac-ext:`Projection Extension <projection>`."""

import json
from typing import Any, Dict, Generic, Iterable, List, Optional, TypeVar, Union, cast

import pystac
from pystac.extensions.hooks import ExtensionHooks
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)

T = TypeVar("T", pystac.Item, pystac.Asset)

SCHEMA_URI: str = "https://stac-extensions.github.io/projection/v1.0.0/schema.json"
PREFIX: str = "proj:"

# Field names
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
    ExtensionManagementMixin[Union[pystac.Item, pystac.Collection]],
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

    def apply(
        self,
        epsg: Optional[int],
        wkt2: Optional[str] = None,
        projjson: Optional[Dict[str, Any]] = None,
        geometry: Optional[Dict[str, Any]] = None,
        bbox: Optional[List[float]] = None,
        centroid: Optional[Dict[str, float]] = None,
        shape: Optional[List[int]] = None,
        transform: Optional[List[float]] = None,
    ) -> None:
        """Applies Projection extension properties to the extended Item.

        Args:
            epsg : REQUIRED. EPSG code of the datasource.
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
        self.epsg = epsg
        self.wkt2 = wkt2
        self.projjson = projjson
        self.geometry = geometry
        self.bbox = bbox
        self.centroid = centroid
        self.shape = shape
        self.transform = transform

    @property
    def epsg(self) -> Optional[int]:
        """Get or sets the EPSG code of the datasource.

        A Coordinate Reference System (CRS) is the data reference system (sometimes
        called a 'projection') used by the asset data, and can usually be referenced
        using an `EPSG code <https://epsg.io/>`_.
        If the asset data does not have a CRS, such as in the case of non-rectified
        imagery with Ground Control Points, ``epsg`` should be set to ``None``.
        It should also be set to ``None`` if a CRS exists, but for which there is no
        valid EPSG code.
        """
        return self._get_property(EPSG_PROP, int)

    @epsg.setter
    def epsg(self, v: Optional[int]) -> None:
        self._set_property(EPSG_PROP, v, pop_if_none=False)

    @property
    def wkt2(self) -> Optional[str]:
        """Get or sets the WKT2 string representing the Coordinate Reference System (CRS)
        that the ``proj:geometry`` and ``proj:bbox`` fields represent

        This value is a
        `WKT2 string <https://docs.opengeospatial.org/is/12-063r5/12-063r5.html>`_.
        If the data does not have a CRS, such as in the case of non-rectified imagery
        with Ground Control Points, ``wkt2`` should be set to ``None``. It should also
        be set to ``None`` if a CRS exists, but for which a WKT2 string does not exist.
        """
        return self._get_property(WKT2_PROP, str)

    @wkt2.setter
    def wkt2(self, v: Optional[str]) -> None:
        self._set_property(WKT2_PROP, v)

    @property
    def projjson(self) -> Optional[Dict[str, Any]]:
        """Get or sets the PROJJSON string representing the Coordinate Reference System (CRS)
        that the ``proj:geometry`` and ``proj:bbox`` fields represent

        This value is a
        `PROJJSON object <https://proj.org/specifications/projjson.html>`_.
        If the data does not have a CRS, such as in the case of non-rectified imagery
        with Ground Control Points, ``projjson`` should be set to ``None``. It should
        also be set to ``None`` if a CRS exists, but for which a PROJJSON string does
        not exist.

        The schema for this object can be found
        `here <https://proj.org/schemas/v0.2/projjson.schema.json>`_.
        """
        return self._get_property(PROJJSON_PROP, Dict[str, Any])

    @projjson.setter
    def projjson(self, v: Optional[Dict[str, Any]]) -> None:
        self._set_property(PROJJSON_PROP, v)

    @property
    def crs_string(self) -> Optional[str]:
        """Returns the coordinate reference system (CRS) string for the extension.

        This string can be used to feed, e.g., ``rasterio.crs.CRS.from_string``.
        The string is determined by the following heuristic:

        1. If an EPSG code is set, return "EPSG:{code}", else
        2. If wkt2 is set, return the WKT string, else,
        3. If projjson is set, return the projjson as a string, else,
        4. Return None
        """
        if self.epsg:
            return f"EPSG:{self.epsg}"
        elif self.wkt2:
            return self.wkt2
        elif self.projjson:
            return json.dumps(self.projjson)
        else:
            return None

    @property
    def geometry(self) -> Optional[Dict[str, Any]]:
        """Get or sets a Polygon GeoJSON dict representing the footprint of this item.

        This dict should be formatted according the Polygon object format specified in
        `RFC 7946, sections 3.1.6 <https://tools.ietf.org/html/rfc7946>`_,
        except not necessarily in EPSG:4326 as required by RFC7946. Specified based on
        the ``epsg``, ``projjson`` or ``wkt2`` fields (not necessarily EPSG:4326).
        Ideally, this will be represented by a Polygon with five coordinates, as the
        item in the asset data CRS should be a square aligned to the original CRS grid.
        """
        return self._get_property(GEOM_PROP, Dict[str, Any])

    @geometry.setter
    def geometry(self, v: Optional[Dict[str, Any]]) -> None:
        self._set_property(GEOM_PROP, v)

    @property
    def bbox(self) -> Optional[List[float]]:
        """Get or sets the bounding box of the assets represented by this item in the asset
        data CRS.

        Specified as 4 or 6 coordinates based on the CRS defined in the ``epsg``,
        ``projjson`` or ``wkt2`` properties. First two numbers are coordinates of the
        lower left corner, followed by coordinates of upper right corner, e.g.,
        ``[west, south, east, north]``, ``[xmin, ymin, xmax, ymax]``,
        ``[left, down, right, up]``, or ``[west, south, lowest, east, north,
        highest]``. The length of the array must be 2*n where n is the number of
        dimensions.
        """
        return self._get_property(BBOX_PROP, List[float])

    @bbox.setter
    def bbox(self, v: Optional[List[float]]) -> None:
        self._set_property(BBOX_PROP, v)

    @property
    def centroid(self) -> Optional[Dict[str, float]]:
        """Get or sets coordinates representing the centroid of the item in the asset data CRS.

        Coordinates are defined in latitude and longitude, even if the data coordinate
        system does not use lat/long.

        Example::

            item.ext.proj.centroid = { 'lat': 0.0, 'lon': 0.0 }
        """
        return self._get_property(CENTROID_PROP, Dict[str, float])

    @centroid.setter
    def centroid(self, v: Optional[Dict[str, float]]) -> None:
        self._set_property(CENTROID_PROP, v)

    @property
    def shape(self) -> Optional[List[int]]:
        """Get or sets the number of pixels in Y and X directions for the default grid.

        The shape is an array of integers that represents the number of pixels in the
        most common pixel grid used by the item's assets. The number of pixels should
        be specified in Y, X order. If the shape is defined in an item's properties it
        is used as the default shape for all assets that don't have an overriding shape.
        """
        return self._get_property(SHAPE_PROP, List[int])

    @shape.setter
    def shape(self, v: Optional[List[int]]) -> None:
        self._set_property(SHAPE_PROP, v)

    @property
    def transform(self) -> Optional[List[float]]:
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
        return self._get_property(TRANSFORM_PROP, List[float])

    @transform.setter
    def transform(self, v: Optional[List[float]]) -> None:
        self._set_property(TRANSFORM_PROP, v)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> "ProjectionExtension[T]":
        """Extends the given STAC Object with properties from the :stac-ext:`Projection
        Extension <projection>`.

        This extension can be applied to instances of :class:`~pystac.Item` or
        :class:`~pystac.Asset`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Item):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(ProjectionExtension[T], ItemProjectionExtension(obj))
        elif isinstance(obj, pystac.Asset):
            cls.validate_owner_has_extension(obj, add_if_missing)
            return cast(ProjectionExtension[T], AssetProjectionExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"Projection extension does not apply to type '{type(obj).__name__}'"
            )

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> "SummariesProjectionExtension":
        """Returns the extended summaries object for the given collection."""
        cls.validate_has_extension(obj, add_if_missing)
        return SummariesProjectionExtension(obj)


class ItemProjectionExtension(ProjectionExtension[pystac.Item]):
    """A concrete implementation of :class:`ProjectionExtension` on an :class:`~pystac.Item`
    that extends the properties of the Item to include properties defined in the
    :stac-ext:`Projection Extension <projection>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`ProjectionExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: pystac.Item
    """The :class:`~pystac.Item` being extended."""

    properties: Dict[str, Any]
    """The :class:`~pystac.Item` properties, including extension properties."""

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return "<ItemProjectionExtension Item id={}>".format(self.item.id)


class AssetProjectionExtension(ProjectionExtension[pystac.Asset]):
    """A concrete implementation of :class:`ProjectionExtension` on an
    :class:`~pystac.Asset` that extends the Asset fields to include properties defined
    in the :stac-ext:`Projection Extension <projection>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`ProjectionExtension.ext` on an :class:`~pystac.Asset` to extend it.
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
        return "<AssetProjectionExtension Asset href={}>".format(self.asset_href)


class SummariesProjectionExtension(SummariesExtension):
    """A concrete implementation of :class:`~SummariesExtension` that extends
    the ``summaries`` field of a :class:`~pystac.Collection` to include properties
    defined in the :stac-ext:`Projection Extension <projection>`.
    """

    @property
    def epsg(self) -> Optional[List[int]]:
        """Get or sets the summary of :attr:`ProjectionExtension.epsg` values
        for this Collection.
        """
        return self.summaries.get_list(EPSG_PROP)

    @epsg.setter
    def epsg(self, v: Optional[List[int]]) -> None:
        self._set_summary(EPSG_PROP, v)


class ProjectionExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"proj", "projection"}
    stac_object_types = {pystac.STACObjectType.ITEM}


PROJECTION_EXTENSION_HOOKS: ExtensionHooks = ProjectionExtensionHooks()
