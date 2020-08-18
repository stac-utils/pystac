from pystac import Extensions
from pystac.item import Item
from pystac.extensions.base import (ItemExtension, ExtensionDefinition, ExtendedObject)


class PointcloudItemExt(ItemExtension):
    """PointcloudItemExt is the extension of an Item in the PointCloud Extension.
    The Pointclout extension adds pointcloud information to STAC Items.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The Item that is being extended.

    """
    def __init__(self, item):
        if item.stac_extensions is None:
            item.stac_extensions = [Extensions.POINTCLOUD]
        elif Extensions.POINTCLOUD not in item.stac_extensions:
            item.stac_extensions.append(Extensions.POINTCLOUD)

        self.item = item

    def apply(self,
              count,
              type,
              encoding,
              schemas,
              density=None,
              statistics=None):
        """Applies Pointcloud extension properties to the extended Item.

        Args:
            count (int): REQUIRED. The number of points in the cloud.
            type (str): REQUIRED. Phenomenology type for the point cloud. Possible valid
                values might include lidar, eopc, radar, sonar, or otherThe type of file
                or data format of the cloud.
            encoding (str): REQUIRED. Content encoding or format of the data.
            schemas (List[dict]): REQUIRED. A sequential array of items that define the
                dimensions and their types.
            density (dict or None): Number of points per square unit area.
            statistics (List[int] or None): A sequential array of items mapping to pc:schemas defines per-channel statistics.
        """
        self.count = count
        self.type = type
        self.encoding = encoding
        self.schemas = schemas
        self.density = density
        self.statistics = statistics

    @property
    def count(self):
        """Get or sets the count property of the datasource.

        Returns:
            int
        """
        return self.get_count()

    @count.setter
    def count(self, v):
        self.set_count(v)

    def get_count(self, asset=None):
        """Gets an Item or an Asset epsg.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            int
        """
        if asset is None or 'pc:count' not in asset.properties:
            return self.item.properties.get('pc:count')
        else:
            return asset.properties.get('pc:count')

    def set_count(self, count, asset=None):
        """Set an Item or an Asset count.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.item.properties['proj:count'] = count
        else:
            asset.properties['proj:count'] = count

    @property
    def type(self):
        """Get or sets the WKT2 string representing the Coordinate Reference System (CRS)
        that the proj:geometry and proj:bbox fields represent

        This value is a `WKT2 string <http://docs.opengeospatial.org/is/12-063r5/12-063r5.html>`_.
        If the data does not have a CRS, such as in the case of non-rectified imagery with Ground
        Control Points, wkt2 should be set to null. It should also be set to null if a CRS exists,
        but for which a WKT2 string does not exist.

        Returns:
            str
        """
        return self.get_type()

    @type.setter
    def type(self, v):
        self.set_type(v)

    def get_type(self, asset=None):
        """Gets an Item or an Asset type.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or 'proj:type' not in asset.properties:
            return self.item.properties.get('proj:type')
        else:
            return asset.properties.get('proj:type')

    def set_type(self, type, asset=None):
        """Set an Item or an Asset type.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.item.properties['proj:type'] = type
        else:
            asset.properties['proj:type'] = type

    @property
    def encoding(self):
        """Get or sets the encoding

        Returns:
            dict
        """
        return self.get_projjson()

    @encoding.setter
    def encoding(self, v):
        self.set_encoding(v)

    def get_encoding(self, asset=None):
        """Gets an Item or an Asset encoding.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            dict
        """
        if asset is None or 'proj:encoding' not in asset.properties:
            return self.item.properties.get('proj:encoding')
        else:
            return asset.properties.get('proj:encoding')

    def set_encoding(self, encoding, asset=None):
        """Set an Item or an Asset encoding.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.item.properties['proj:encoding'] = encoding
        else:
            asset.properties['proj:encoding'] = encoding

    @property
    def schema(self):
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
        return self.get_schemas()

    @schemas.setter
    def schemas(self, v):
        self.set_schemas(v)

    def get_schemas(self, asset=None):
        """Gets an Item or an Asset projection geometry.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            dict
        """
        if asset is None or 'proj:schema' not in asset.properties:
            return self.item.properties.get('proj:schema')
        else:
            return asset.properties.get('proj:schemas')

    def set_schemas(self, schemas, asset=None):
        """Set an Item or an Asset projection geometry.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.item.properties['proj:schemas'] = schemas
        else:
            asset.properties['proj:schemas'] = schemas

    @property
    def density(self):
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
        return self.get_density()

    @density.setter
    def density(self, v):
        self.set_density(v)

    def get_density(self, asset=None):
        """Gets an Item or an Asset projection bbox.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            List[float]
        """
        if asset is None or 'proj:density' not in asset.properties:
            return self.item.properties.get('proj:density')
        else:
            return asset.properties.get('proj:density')

    def set_density(self, density, asset=None):
        """Set an Item or an Asset density property.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.item.properties['proj:density'] = density
        else:
            asset.properties['proj:density'] = density

    @property
    def statistics(self):
        """Get or sets coordinates representing the centroid of the item in the asset data CRS.

        Exmample::

            item.ext.proj.centroid = { 'lat': 0.0, 'lon': 0.0 }

        Returns:
            dict
        """
        return self.get_statistics()

    @centroid.setter
    def statistics(self, v):
        self.set_statistics(v)

    def get_statistics(self, asset=None):
        """Gets an Item or an Asset centroid.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            dict
        """
        if asset is None or 'proj:statistics' not in asset.properties:
            return self.item.properties.get('proj:statistics')
        else:
            return asset.properties.get('proj:statistics')

    def set_statistics(self, statistics, asset=None):
        """Set an Item or an Asset centroid.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.item.properties['proj:statistics'] = statistics
        else:
            asset.properties['proj:statistics'] = statistics


    @classmethod
    def _object_links(cls):
        return []

    @classmethod
    def from_item(cls, item):
        return cls(item)


POINTCLOUD_EXTENSION_DEFINITION = ExtensionDefinition(Extensions.POINTCLOUD,
                                                      [ExtendedObject(Item, PointcloudItemExt)])
