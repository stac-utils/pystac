from pystac import Extensions, STACError
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

    def apply(self, count, type, encoding, schemas, density=None, statistics=None, epsg=None):
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
            statistics (List[int] or None): A sequential array of items mapping to pc:schemas
                defines per-channel statistics.
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
        and is represented as a sequential array of items that define the dimensions
        and their types,

        Returns:
            List[PointcloudSchema]
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
            List[PointcloudSchema]
        """
        if asset is None or 'pc:schemas' not in asset.properties:
            schemas = self.item.properties.get('pc:schemas')
            return [PointcloudSchema(s) for s in schemas]
        else:
            return [PointcloudSchema.create(s) for s in asset.properties.get('pc:schemas')]

    def set_schemas(self, schemas, asset=None):
        """Set an Item or an Asset schema

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        dicts = [s.to_dict() for s in schemas]
        if asset is None:
            self.item.properties['pc:schemas'] = dicts
        else:
            asset.properties['pc:schemas'] = dicts

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

        Example::

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
            List[PointCloudStatistics] or None
        """
        if asset is None or 'pc:statistics' not in asset.properties:
            stats = self.item.properties.get('pc:statistics')
            return [PointcloudStatistic(s) for s in stats]
        else:
            return [PointcloudStatistic.create(s) for s in asset.properties.get('pc:statistics')]

    def set_statistics(self, statistics, asset=None):
        """Set an Item or an Asset centroid.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if statistics is not None:
            statistics = [s.to_dict() for s in statistics]
        if asset is None:
            self.item.properties['pc:statistics'] = statistics
        else:
            asset.properties['pc:statistics'] = statistics

    @classmethod
    def _object_links(cls):
        return []

    @classmethod
    def from_item(cls, item):
        return cls(item)


class PointcloudSchema:
    """Defines a schema for dimension of a pointcloud (e.g., name, size, type)

    Use PointCloudSchema.create to create a new instance of PointCloudSchema from properties.
    """
    def __init__(self, properties):
        self.properties = properties

    def apply(self, name, size, type):
        """Sets the properties for this PointCloudSchema.

        Args:
           name (str): The name of dimension.
           size (int): The size of the dimension in bytes. Whole bytes are supported.
           type (str): Dimension type. Valid values are `floating`, `unsigned`, and `signed`
        """
        self.properties['name'] = name
        self.properties['size'] = size
        self.properties['type'] = type

    @classmethod
    def create(cls, *args):
        """Creates a new PointCloudSchema.

        Args:
           name (str): The name of dimension.
           size (int): The size of the dimension in bytes. Whole bytes are supported.
           type (str): Dimension type. Valid values are `floating`, `unsigned`, and `signed`

        Returns:
              PointCloudSchema
        """
        c = cls({})
        c.apply(*args)
        return c

    @property
    def size(self):
        """Get or sets the size value.

        Returns:
            int
        """
        return self.properties.get('size')

    @size.setter
    def size(self, v):
        if not type(v) is int:
            raise STACError("size must be an int! Invalid input: {}".format(v))

        self.properties['size'] = v

    @property
    def name(self):
        """Get or sets the name property for this PointCloudSchema.

        Returns:
            str
        """
        return self.properties.get('name')

    @name.setter
    def name(self, v):
        if v is not None:
            self.properties['name'] = v
        else:
            self.properties.pop('name', None)

    @property
    def type(self):
        """Get or sets the type property. Valid values are `floating`, `unsigned`, and `signed`

        Returns:
            str
        """
        return self.properties.get('type')

    @type.setter
    def type(self, v):
        if v is not None:
            self.properties['type'] = v
        else:
            self.properties.pop('type', None)

    def __repr__(self):
        return '<PointCloudSchema name={} size={} type={}>'.format(self.name, self.size, self.type)

    def to_dict(self):
        """Returns the dictionary representing the JSON of this PointCloudSchema.

        Returns:
            dict: The wrapped dict of the PointCloudSchema that can be written out as JSON.
        """
        return self.properties


class PointcloudStatistic:
    """Defines a single statistic for Pointcloud channel or dimension

    Use PointcloudStatistic.create to create a new instance of LabelClasses from property values.
    """
    def __init__(self, properties):
        self.properties = properties

    def apply(self,
              name,
              position=None,
              average=None,
              count=None,
              maximum=None,
              minimum=None,
              stddev=None,
              variance=None):
        """Sets the properties for this PointcloudStatistic.

        Args:
            name (str): REQUIRED. The name of the channel.
            position (int): Position of the channel in the schema.
            average (float)	The average of the channel.
            count (int): The number of elements in the channel.
            maximum	(float): The maximum value of the channel.
            minimum	(float):	The minimum value of the channel.
            stddev (float): The standard deviation of the channel.
            variance (float): The variance of the channel.
        """
        self.properties['name'] = name
        self.properties['position'] = position
        self.properties['average'] = average
        self.properties['count'] = count
        self.properties['maximum'] = maximum
        self.properties['minimum'] = minimum
        self.properties['stddev'] = stddev
        self.properties['variance'] = variance

    @classmethod
    def create(cls,
               name,
               position=None,
               average=None,
               count=None,
               maximum=None,
               minimum=None,
               stddev=None,
               variance=None):
        """Creates a new PointcloudStatistic class.

        Args:
            name (str): REQUIRED. The name of the channel.
            position (int): Position of the channel in the schema.
            average (float)	The average of the channel.
            count (int): The number of elements in the channel.
            maximum	(float): The maximum value of the channel.
            minimum	(float):	The minimum value of the channel.
            stddev (float): The standard deviation of the channel.
            variance (float): The variance of the channel.

        Returns:
            LabelClasses
        """
        c = cls({})
        c.apply(name, )
        return c

    @property
    def name(self):
        """Get or sets the name property

        Returns:
            str
        """
        return self.properties.get('name')

    @name.setter
    def name(self, v):
        if v is not None:
            self.properties['name'] = v
        else:
            self.properties.pop('name', None)

    @property
    def position(self):
        """Get or sets the position property

        Returns:
            int
        """
        return self.properties.get('position')

    @position.setter
    def position(self, v):
        if v is not None:
            self.properties['position'] = v
        else:
            self.properties.pop('position', None)

    @property
    def average(self):
        """Get or sets the average property

        Returns:
            float
        """
        return self.properties.get('average')

    @average.setter
    def average(self, v):
        if v is not None:
            self.properties['average'] = v
        else:
            self.properties.pop('average', None)

    @property
    def count(self):
        """Get or sets the count property

        Returns:
            int
        """
        return self.properties.get('count')

    @count.setter
    def count(self, v):
        if v is not None:
            self.properties['count'] = v
        else:
            self.properties.pop('count', None)

    @property
    def maximum(self):
        """Get or sets the maximum property

        Returns:
            float
        """
        return self.properties.get('maximum')

    @maximum.setter
    def maximum(self, v):
        if v is not None:
            self.properties['maximum'] = v
        else:
            self.properties.pop('maximum', None)

    @property
    def minimum(self):
        """Get or sets the minimum property

        Returns:
            float
        """
        return self.properties.get('minimum')

    @minimum.setter
    def minimum(self, v):
        if v is not None:
            self.properties['minimum'] = v
        else:
            self.properties.pop('minimum', None)

    @property
    def stddev(self):
        """Get or sets the stddev property

        Returns:
            float
        """
        return self.properties.get('stddev')

    @stddev.setter
    def stddev(self, v):
        if v is not None:
            self.properties['stddev'] = v
        else:
            self.properties.pop('stddev', None)

    @property
    def variance(self):
        """Get or sets the variance property

        Returns:
            float
        """
        return self.properties.get('variance')

    @variance.setter
    def variance(self, v):
        if v is not None:
            self.properties['variance'] = v
        else:
            self.properties.pop('variance', None)

    def __repr__(self):
        return '<PointcloudStatistic statistics={}>'.format(str(self.properties))

    def to_dict(self):
        """Returns the dictionary representing the JSON of this PointcloudStatistic.

        Returns:
            dict: The wrapped dict of the PointcloudStatistic that can be written out as JSON.
        """
        return self.properties


POINTCLOUD_EXTENSION_DEFINITION = ExtensionDefinition(Extensions.POINTCLOUD,
                                                      [ExtendedObject(Item, PointcloudItemExt)])
