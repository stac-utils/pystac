"""Implements the Projection extension.

https://github.com/stac-extensions/projection
"""

from typing import Any, Dict, Generic, List, Optional, Set, TypeVar, cast

import pystac
from pystac.extensions.hooks import ExtensionHooks
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
)

T = TypeVar("T", pystac.Item, pystac.Asset)

SCHEMA_URI = "https://stac-extensions.github.io/projection/v1.0.0/schema.json"

EPSG_PROP = "proj:epsg"
WKT2_PROP = "proj:wkt2"
PROJJSON_PROP = "proj:projjson"
GEOM_PROP = "proj:geometry"
BBOX_PROP = "proj:bbox"
CENTROID_PROP = "proj:centroid"
SHAPE_PROP = "proj:shape"
TRANSFORM_PROP = "proj:transform"


class ProjectionExtension(
    Generic[T], PropertiesExtension, ExtensionManagementMixin[pystac.Item]
):
    """ProjectionItemExt is the extension of an Item in the Projection Extension.
    The Projection extension adds projection information to STAC Items.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The Item that is being extended.

    Note:
        Using ProjectionItemExt to directly wrap an item will add the 'proj' extension
        ID to the item's stac_extensions.
    """

    def __init__(self, item: pystac.Item) -> None:
        self.item = item

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
            epsg (int or None): REQUIRED. EPSG code of the datasource.
            wkt2 (str or None): WKT2 string representing the Coordinate Reference
                System (CRS) that the ``geometry`` and ``bbox`` fields represent
            projjson (dict or None): PROJJSON dict representing the
                Coordinate Reference System (CRS) that the ``geometry`` and ``bbox``
                fields represent
            geometry (dict or None): GeoJSON Polygon dict that defines the footprint of
                this Item.
            bbox (List[float] or None): Bounding box of the Item in the asset CRS in
                2 or 3 dimensions.
            centroid (dict or None): A dict with members 'lat' and 'lon' that defines
                coordinates representing the centroid of the item in the asset data CRS.
                Coordinates are defined in latitude and longitude, even if the data
                coordinate system may not use lat/long.
            shape (List[int] or None): Number of pixels in Y and X directions for the
                default grid.
            transform (List[float] or None): The affine transformation coefficients for
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
        using an `EPSG code <http://epsg.io/>`_.
        If the asset data does not have a CRS, such as in the case of non-rectified
        imagery with Ground Control Points, epsg should be set to None.
        It should also be set to null if a CRS exists, but for which there is no valid
        EPSG code.

        Returns:
            int
        """
        return self._get_property(EPSG_PROP, int)

    @epsg.setter
    def epsg(self, v: Optional[int]) -> None:
        self._set_property(EPSG_PROP, v, pop_if_none=False)

    @property
    def wkt2(self) -> Optional[str]:
        """Get or sets the WKT2 string representing the Coordinate Reference System (CRS)
        that the proj:geometry and proj:bbox fields represent

        This value is a
        `WKT2 string <http://docs.opengeospatial.org/is/12-063r5/12-063r5.html>`_.
        If the data does not have a CRS, such as in the case of non-rectified imagery
        with Ground Control Points, wkt2 should be set to null. It should also be set
        to null if a CRS exists, but for which a WKT2 string does not exist.

        Returns:
            str
        """
        return self._get_property(WKT2_PROP, str)

    @wkt2.setter
    def wkt2(self, v: Optional[str]) -> None:
        self._set_property(WKT2_PROP, v)

    @property
    def projjson(self) -> Optional[Dict[str, Any]]:
        """Get or sets the PROJJSON string representing the Coordinate Reference System (CRS)
        that the proj:geometry and proj:bbox fields represent

        This value is a
        `PROJJSON object <https://proj.org/specifications/projjson.html>`_.
        If the data does not have a CRS, such as in the case of non-rectified imagery
        with Ground Control Points, projjson should be set to null. It should also be
        set to null if a CRS exists, but for which a PROJJSON string does not exist.

        The schema for this object can be found
        `here <https://proj.org/schemas/v0.2/projjson.schema.json>`_.

        Returns:
            dict
        """
        return self._get_property(PROJJSON_PROP, Dict[str, Any])

    @projjson.setter
    def projjson(self, v: Optional[Dict[str, Any]]) -> None:
        self._set_property(PROJJSON_PROP, v)

    @property
    def geometry(self) -> Optional[Dict[str, Any]]:
        """Get or sets a Polygon GeoJSON dict representing the footprint of this item.

        This dict should be formatted according the Polygon object format specified in
        `RFC 7946, sections 3.1.6 <https://tools.ietf.org/html/rfc7946>`_,
        except not necessarily in EPSG:4326 as required by RFC7946. Specified based on
        the ``epsg``, ``projjson`` or ``wkt2`` fields (not necessarily EPSG:4326).
        Ideally, this will be represented by a Polygon with five coordinates, as the
        item in the asset data CRS should be a square aligned to the original CRS grid.

        Returns:
            dict
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
        [west, south, east, north], [xmin, ymin, xmax, ymax], [left, down, right, up],
        or [west, south, lowest, east, north, highest]. The length of the array
        must be 2*n where n is the number of dimensions.

        Returns:
            List[float]
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

        Returns:
            dict
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

        Returns:
            List[int]
        """
        return self._get_property(SHAPE_PROP, List[int])

    @shape.setter
    def shape(self, v: Optional[List[int]]) -> None:
        self._set_property(SHAPE_PROP, v)

    @property
    def transform(self) -> Optional[List[float]]:
        """Get or sets the the affine transformation coefficients for the default grid.

        The transform is a linear mapping from pixel coordinate space (Pixel, Line) to
        projection coordinate space (Xp, Yp). It is a 3x3 matrix stored as a flat array of 9
        elements in row major order. Since the last row is always 0,0,1 it can be omitted, in
        which case only 6 elements are recorded. This mapping can be obtained from
        GDAL `GetGeoTransform <https://gdal.org/api/gdaldataset_cpp.html#_CPPv4N11GDALDataset15GetGeoTransformEPd>`_
        or the
        Rasterio `Transform <https://rasterio.readthedocs.io/en/stable/api/rasterio.io.html#rasterio.io.BufferedDatasetWriter.transform>`_.

        Returns:
            List[float]
        """  # noqa: E501
        return self._get_property(TRANSFORM_PROP, List[float])

    @transform.setter
    def transform(self, v: Optional[List[float]]) -> None:
        self._set_property(TRANSFORM_PROP, v)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @staticmethod
    def ext(obj: T) -> "ProjectionExtension[T]":
        if isinstance(obj, pystac.Item):
            return cast(ProjectionExtension[T], ItemProjectionExtension(obj))
        elif isinstance(obj, pystac.Asset):
            return cast(ProjectionExtension[T], AssetProjectionExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"File extension does not apply to type {type(obj)}"
            )


class ItemProjectionExtension(ProjectionExtension[pystac.Item]):
    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return "<ItemProjectionExtension Item id={}>".format(self.item.id)


class AssetProjectionExtension(ProjectionExtension[pystac.Asset]):
    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.properties
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return "<AssetProjectionExtension Asset href={}>".format(self.asset_href)


class ProjectionExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: Set[str] = set(["proj", "projection"])
    stac_object_types: Set[pystac.STACObjectType] = set([pystac.STACObjectType.ITEM])


PROJECTION_EXTENSION_HOOKS = ProjectionExtensionHooks()
