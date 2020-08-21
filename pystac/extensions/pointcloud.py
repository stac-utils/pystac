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
              statistics=None,
              epsg=None):
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
            epsg (str): An EPSG code for the projected coordinates of the pointcloud.
        """
        self.count = count
        self.type = type
        self.encoding = encoding
        self.schemas = schemas
        self.density = density
        self.statistics = statistics
        self.epsg = epsg

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
        """Gets an Item or an Asset count.

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
            self.item.properties['pc:count'] = count
        else:
            asset.properties['pc:count'] = count

    @property
    def type(self):
        """Get or sets the pc:type prop on the Item

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
        if asset is None or 'pc:type' not in asset.properties:
            return self.item.properties.get('pc:type')
        else:
            return asset.properties.get('pc:type')

    def set_type(self, type, asset=None):
        """Set an Item or an Asset type.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.item.properties['pc:type'] = type
        else:
            asset.properties['pc:type'] = type

    @property
    def encoding(self):
        """Get or sets the content-encoding for the item.

        The content-encoding is the underlying encoding format for the point cloud. 
        Examples may include: laszip, ascii, binary, etc.

        Returns:
            str
        """
        return self.get_encoding()

    @encoding.setter
    def encoding(self, v):
        self.set_encoding(v)

    def get_encoding(self, asset=None):
        """Gets an Item or an Asset encoding.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or 'pc:encoding' not in asset.properties:
            return self.item.properties.get('pc:encoding')
        else:
            return asset.properties.get('pc:encoding')

    def set_encoding(self, encoding, asset=None):
        """Set an Item or an Asset encoding.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.item.properties['pc:encoding'] = encoding
        else:
            asset.properties['pc:encoding'] = encoding

    @property
    def schemas(self):
        """Get or sets a 

        The schemas represent the structure of the data attributes in the pointcloud, 
        and is represented as a sequential array of items that define the dimensions and their types.

        Returns:
            List[dict]
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
        if asset is None or 'pc:schema' not in asset.properties:
            return self.item.properties.get('pc:schema')
        else:
            return asset.properties.get('pc:schemas')

    def set_schemas(self, schemas, asset=None):
        """Set an Item or an Asset schema

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.item.properties['pc:schemas'] = schemas
        else:
            asset.properties['pc:schemas'] = schemas

    @property
    def density(self):
        """Get or sets the density for the item. 

        Density is defined as the number of points per square unit area.

        Returns:
            int
        """
        return self.get_density()

    @density.setter
    def density(self, v):
        self.set_density(v)

    def get_density(self, asset=None):
        """Gets an Item or an Asset density.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            int
        """
        if asset is None or 'pc:density' not in asset.properties:
            return self.item.properties.get('pc:density')
        else:
            return asset.properties.get('pc:density')

    def set_density(self, density, asset=None):
        """Set an Item or an Asset density property.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.item.properties['pc:density'] = density
        else:
            asset.properties['pc:density'] = density

    @property
    def statistics(self):
        """Get or sets the statistics for each property of the dataset.

        A sequential array of items mapping to pc:schemas defines per-channel statistics.

        Exmample::

            item.ext.pointcloud.statistics = [{ 'name': 'red', 'min': 0, 'max': 255 }]

        Returns:
            List[dict]
        """
        return self.get_statistics()

    @statistics.setter
    def statistics(self, v):
        self.set_statistics(v)

    def get_statistics(self, asset=None):
        """Gets an Item or an Asset centroid.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            dict
        """
        if asset is None or 'pc:statistics' not in asset.properties:
            return self.item.properties.get('pc:statistics')
        else:
            return asset.properties.get('pc:statistics')

    def set_statistics(self, statistics, asset=None):
        """Set an Item or an Asset centroid.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.item.properties['pc:statistics'] = statistics
        else:
            asset.properties['pc:statistics'] = statistics

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
            str
        """
        return self.get_epsg()

    @epsg.setter
    def epsg(self, v):
        self.set_epsg(v)

    def get_epsg(self, asset=None):
        """Gets an Item or an Asset epsg.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or 'pc:epsg' not in asset.properties:
            return self.item.properties.get('pc:epsg')
        else:
            return asset.properties.get('pc:epsg')

    def set_epsg(self, epsg, asset=None):
        """Set an Item or an Asset epsg.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.item.properties['pc:epsg'] = epsg
        else:
            asset.properties['pc:epsg'] = epsg



    @classmethod
    def _object_links(cls):
        return []

    @classmethod
    def from_item(cls, item):
        return cls(item)


POINTCLOUD_EXTENSION_DEFINITION = ExtensionDefinition(Extensions.POINTCLOUD,
                                                      [ExtendedObject(Item, PointcloudItemExt)])
