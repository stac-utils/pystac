from pystac import Extensions
from pystac.item import Item
from pystac.extensions.base import (ItemExtension, ExtensionDefinition, ExtendedObject)


class ProjectionItemExt(ItemExtension):
    """ProjectionItemExt is the extension of an Item in the Projection Extension.
    The Projection extension adds projection information to STAC Items.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The Item that is being extended.

    Note:
        Using ProjectionItemExt to directly wrap an item will add the 'proj' extension ID to
        the item's stac_extensions.
    """
    def __init__(self, item):
        if item.stac_extensions is None:
            item.stac_extensions = [Extensions.PROJECTION]
        elif Extensions.PROJECTION not in item.stac_extensions:
            item.stac_extensions.append(Extensions.PROJECTION)

        self.item = item

    def apply(self,
              epsg,
              wkt2=None,
              projjson=None,
              geometry=None,
              bbox=None,
              centroid=None,
              shape=None,
              transform=None):
        """Applies Projection extension properties to the extended Item.

        Args:
            epsg (int or None): REQUIRED. EPSG code of the datasource.
            wkt2 (str or None): WKT2 string representing the Coordinate Reference System (CRS) that
                the ``geometry`` and ``bbox`` fields represent
            projjson (dict or None): PROJJSON dict representing the
                Coordinate Reference System (CRS) that the ``geometry`` and ``bbox``
                fields represent
            geometry (dict or None): GeoJSON Polygon dict that defines the footprint of this Item.
            bbox (List[float] or None): Bounding box of the Item in the asset CRS in
                2 or 3 dimensions.
            centroid (dict or None): A dict with members 'lat' and 'lon' that defines
                coordinates representing the centroid of the item in the asset data CRS.
                Coordinates are defined in latitude and longitude, even if the data coordinate
                system may not use lat/long.
            shape (List[int] or None): Number of pixels in Y and X directions for the default grid.
            transform (List[float] or None): The affine transformation coefficients for the
                default grid
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
    def epsg(self):
        """Get or sets the EPSG code of the datasource.

        A Coordinate Reference System (CRS) is the data reference system (sometimes called a
        'projection') used by the asset data, and can usually be referenced using an
        `EPSG code <http://epsg.io/>`_.
        If the asset data does not have a CRS, such as in the case of non-rectified imagery with
        Ground Control Points, epsg should be set to None.
        It should also be set to null if a CRS exists, but for which there is no valid EPSG code.

        Returns:
            int
        """
        return self.item.properties.get('proj:epsg')

    @epsg.setter
    def epsg(self, v):
        self.item.properties['proj:epsg'] = v

    @property
    def wkt2(self):
        """Get or sets the WKT2 string representing the Coordinate Reference System (CRS)
        that the proj:geometry and proj:bbox fields represent

        This value is a `WKT2 string <http://docs.opengeospatial.org/is/12-063r5/12-063r5.html>`_.
        If the data does not have a CRS, such as in the case of non-rectified imagery with Ground
        Control Points, wkt2 should be set to null. It should also be set to null if a CRS exists,
        but for which a WKT2 string does not exist.

        Returns:
            str
        """
        return self.item.properties.get('proj:wkt2')

    @wkt2.setter
    def wkt2(self, v):
        self.item.properties['proj:wkt2'] = v

    @property
    def projjson(self):
        """Get or sets the PROJJSON string representing the Coordinate Reference System (CRS)
        that the proj:geometry and proj:bbox fields represent

        This value is a `PROJJSON object <https://proj.org/specifications/projjson.html>`_.
        If the data does not have a CRS, such as in the case of non-rectified imagery with Ground
        Control Points, projjson should be set to null. It should also be set to null if a
        CRS exists, but for which a PROJJSON string does not exist.

        The schema for this object can be found
        `here <https://proj.org/schemas/v0.2/projjson.schema.json>`_.

        Returns:
            dict
        """
        return self.item.properties.get('proj:projjson')

    @projjson.setter
    def projjson(self, v):
        self.item.properties['proj:projjson'] = v

    @property
    def geometry(self):
        """Get or sets a Polygon GeoJSON dict representing the footprint of this item.

        This dict should be formatted according the Polygon object format specified in
        `RFC 7946, sections 3.1.6 <https://tools.ietf.org/html/rfc7946>`_,
        except not necessarily in EPSG:4326 as required by RFC7946. Specified based on the
        ``epsg``, ``projjson`` or ``wkt2`` fields (not necessarily EPSG:4326).
        Ideally, this will be represented by a Polygon with five coordinates, as the item in
        the asset data CRS should be a square aligned to the original CRS grid.

        Returns:
            dict
        """
        return self.item.properties.get('proj:geometry')

    @geometry.setter
    def geometry(self, v):
        self.item.properties['proj:geometry'] = v

    @property
    def bbox(self):
        """Get or sets the bounding box of the assets represented by this item in the asset
        data CRS.

        Specified as 4 or 6 coordinates based on the CRS defined in the ``epsg``, ``projjson``
        or ``wkt2`` properties. First two numbers are coordinates of the lower left corner,
        followed by coordinates of upper right corner, e.g.,
        [west, south, east, north], [xmin, ymin, xmax, ymax], [left, down, right, up],
        or [west, south, lowest, east, north, highest]. The length of the array must be 2*n
        where n is the number of dimensions.

        Returns:
            List[float]
        """
        return self.item.properties.get('proj:bbox')

    @bbox.setter
    def bbox(self, v):
        self.item.properties['proj:bbox'] = v

    @property
    def centroid(self):
        """Get or sets coordinates representing the centroid of the item in the asset data CRS.

        Coordinates are defined in latitude and longitude, even if the data coordinate system
        does not use lat/long.

        Exmample::

            item.ext.proj.centroid = { 'lat': 0.0, 'lon': 0.0 }

        Returns:
            dict
        """
        return self.item.properties.get('proj:centroid')

    @centroid.setter
    def centroid(self, v):
        self.item.properties['proj:centroid'] = v

    @property
    def shape(self):
        """Get or sets the number of pixels in Y and X directions for the default grid.

        The shape is an array of integers that represents the number of pixels in the most
        common pixel grid used by the item's assets. The number of pixels should be specified
        in Y, X order. If the shape is defined in an item's properties it is used as the default
        shape for all assets that don't have an overriding shape.

        Returns:
            List[int]
        """
        return self.item.properties.get('proj:shape')

    @shape.setter
    def shape(self, v):
        self.item.properties['proj:shape'] = v

    @property
    def transform(self):
        """Get or sets the the affine transformation coefficients for the default grid.

        The transform is a linear mapping from pixel coordinate space (Pixel, Line) to
        projection coordinate space (Xp, Yp). It is a 3x3 matrix stored as a flat array of 9
        elements in row major order. Since the last row is always 0,0,1 it can be omitted, in
        which case only 6 elements are recorded. This mapping can be obtained from
        GDAL `GetGeoTransform <https://gdal.org/api/gdaldataset_cpp.html#_CPPv4N11GDALDataset15GetGeoTransformEPd>`_
        or the
        Rasterio `Transform <https://rasterio.readthedocs.io/en/stable/api/rasterio.io.html#rasterio.io.BufferedDatasetWriter.transform>`_.

        Returns:
            float
        """  # noqa: E501
        return self.item.properties.get('proj:transform')

    @transform.setter
    def transform(self, v):
        self.item.properties['proj:transform'] = v

    @classmethod
    def _object_links(cls):
        return []

    @classmethod
    def from_item(cls, item):
        return cls(item)


PROJECTION_EXTENSION_DEFINITION = ExtensionDefinition(Extensions.PROJECTION,
                                                      [ExtendedObject(Item, ProjectionItemExt)])
