from typing import Any, Dict, List, Optional
from pystac import Extensions, STACError
from pystac.item import Asset, Item
from pystac.extensions.base import (ItemExtension, ExtensionDefinition, ExtendedObject)


class PointcloudSchema:
    """Defines a schema for dimension of a pointcloud (e.g., name, size, type)

    Use PointCloudSchema.create to create a new instance of PointCloudSchema from properties.
    """
    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    def apply(self, name: str, size: int, type: str) -> None:
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
    def create(cls, name: str, size: int, type: str) -> "PointcloudSchema":
        """Creates a new PointCloudSchema.

        Args:
           name (str): The name of dimension.
           size (int): The size of the dimension in bytes. Whole bytes are supported.
           type (str): Dimension type. Valid values are `floating`, `unsigned`, and `signed`

        Returns:
              PointCloudSchema
        """
        c = cls({})
        c.apply(name=name, size=size, type=type)
        return c

    @property
    def size(self) -> int:
        """Get or sets the size value.

        Returns:
            int
        """
        result = self.properties.get('size')
        if result is None:
            raise STACError(f"Pointcloud schema does not have size property: {self.properties}")
        return result

    @size.setter
    def size(self, v: int) -> None:
        if not isinstance(v, int):
            raise STACError("size must be an int! Invalid input: {}".format(v))

        self.properties['size'] = v

    @property
    def name(self) -> str:
        """Get or sets the name property for this PointCloudSchema.

        Returns:
            str
        """
        result = self.properties.get('name')
        if result is None:
            raise STACError(f"Pointcloud schema does not have name property: {self.properties}")
        return result

    @name.setter
    def name(self, v: str) -> None:
        self.properties['name'] = v

    @property
    def type(self) -> str:
        """Get or sets the type property. Valid values are `floating`, `unsigned`, and `signed`

        Returns:
            str
        """
        result = self.properties.get('type')
        if result is None:
            raise STACError(f"Pointcloud schema has no type property: {self.properties}")
        return result

    @type.setter
    def type(self, v: str) -> None:
        self.properties['type'] = v

    def __repr__(self) -> str:
        return '<PointCloudSchema name={} size={} type={}>'.format(self.name, self.size, self.type)

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of this PointCloudSchema.

        Returns:
            dict: The wrapped dict of the PointCloudSchema that can be written out as JSON.
        """
        return self.properties


class PointcloudStatistic:
    """Defines a single statistic for Pointcloud channel or dimension

    Use PointcloudStatistic.create to create a new instance of LabelClasses from property values.
    """
    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    def apply(self,
              name: str,
              position: Optional[int] = None,
              average: Optional[float] = None,
              count: Optional[int] = None,
              maximum: Optional[float] = None,
              minimum: Optional[float] = None,
              stddev: Optional[float] = None,
              variance: Optional[float] = None) -> None:
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
               name: str,
               position: Optional[int] = None,
               average: Optional[float] = None,
               count: Optional[int] = None,
               maximum: Optional[float] = None,
               minimum: Optional[float] = None,
               stddev: Optional[float] = None,
               variance: Optional[float] = None) -> "PointcloudStatistic":
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
        c.apply(name=name,
                position=position,
                average=average,
                count=count,
                maximum=maximum,
                minimum=minimum,
                stddev=stddev,
                variance=variance)
        return c

    @property
    def name(self) -> str:
        """Get or sets the name property

        Returns:
            str
        """
        result = self.properties.get('name')
        if result is None:
            raise STACError(f"Pointcloud statistics does not have name property: {self.properties}")
        return result

    @name.setter
    def name(self, v: str) -> None:
        if v is not None:
            self.properties['name'] = v
        else:
            self.properties.pop('name', None)

    @property
    def position(self) -> Optional[int]:
        """Get or sets the position property

        Returns:
            int
        """
        return self.properties.get('position')

    @position.setter
    def position(self, v: Optional[int]) -> None:
        if v is not None:
            self.properties['position'] = v
        else:
            self.properties.pop('position', None)

    @property
    def average(self) -> Optional[float]:
        """Get or sets the average property

        Returns:
            float
        """
        return self.properties.get('average')

    @average.setter
    def average(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties['average'] = v
        else:
            self.properties.pop('average', None)

    @property
    def count(self) -> Optional[int]:
        """Get or sets the count property

        Returns:
            int
        """
        return self.properties.get('count')

    @count.setter
    def count(self, v: Optional[int]) -> None:
        if v is not None:
            self.properties['count'] = v
        else:
            self.properties.pop('count', None)

    @property
    def maximum(self) -> Optional[float]:
        """Get or sets the maximum property

        Returns:
            float
        """
        return self.properties.get('maximum')

    @maximum.setter
    def maximum(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties['maximum'] = v
        else:
            self.properties.pop('maximum', None)

    @property
    def minimum(self) -> Optional[float]:
        """Get or sets the minimum property

        Returns:
            float
        """
        return self.properties.get('minimum')

    @minimum.setter
    def minimum(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties['minimum'] = v
        else:
            self.properties.pop('minimum', None)

    @property
    def stddev(self) -> Optional[float]:
        """Get or sets the stddev property

        Returns:
            float
        """
        return self.properties.get('stddev')

    @stddev.setter
    def stddev(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties['stddev'] = v
        else:
            self.properties.pop('stddev', None)

    @property
    def variance(self) -> Optional[float]:
        """Get or sets the variance property

        Returns:
            float
        """
        return self.properties.get('variance')

    @variance.setter
    def variance(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties['variance'] = v
        else:
            self.properties.pop('variance', None)

    def __repr__(self) -> str:
        return '<PointcloudStatistic statistics={}>'.format(str(self.properties))

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of this PointcloudStatistic.

        Returns:
            dict: The wrapped dict of the PointcloudStatistic that can be written out as JSON.
        """
        return self.properties


class PointcloudItemExt(ItemExtension):
    """PointcloudItemExt is the extension of an Item in the PointCloud Extension.
    The Pointclout extension adds pointcloud information to STAC Items.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The Item that is being extended.

    """
    def __init__(self, item: Item) -> None:
        if item.stac_extensions is None:
            item.stac_extensions = [str(Extensions.POINTCLOUD)]
        elif str(Extensions.POINTCLOUD) not in item.stac_extensions:
            item.stac_extensions.append(str(Extensions.POINTCLOUD))

        self.item = item

    def apply(self,
              count: int,
              type: str,
              encoding: str,
              schemas: List[PointcloudSchema],
              density: Optional[float] = None,
              statistics: Optional[List[PointcloudStatistic]] = None,
              epsg: Optional[int] = None) -> None:  # TODO: Remove epsg per spec
        """Applies Pointcloud extension properties to the extended Item.

        Args:
            count (int): REQUIRED. The number of points in the cloud.
            type (str): REQUIRED. Phenomenology type for the point cloud. Possible valid
                values might include lidar, eopc, radar, sonar, or otherThe type of file
                or data format of the cloud.
            encoding (str): REQUIRED. Content encoding or format of the data.
            schemas (List[PointcloudSchema]): REQUIRED. A sequential array of items that define the
                dimensions and their types.
            density (float or None): Number of points per square unit area.
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
    def count(self) -> int:
        """Get or sets the count property of the datasource.

        Returns:
            int
        """
        return self.get_count()

    @count.setter
    def count(self, v: int) -> None:
        self.set_count(v)

    def get_count(self, asset: Optional[Asset] = None) -> int:
        """Gets an Item or an Asset count.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            int
        """
        if asset is None or 'pc:count' not in asset.properties:
            result = self.item.properties.get('pc:count')
        else:
            result = asset.properties.get('pc:count')

        if result is None:
            raise STACError(f"pc:count not found on point cloud item with ID {self.item.id}")

        return result

    def set_count(self, count: int, asset: Optional[Asset] = None) -> None:
        """Set an Item or an Asset count.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        self._set_property('pc:count', count, asset)

    @property
    def type(self) -> str:
        """Get or sets the pc:type prop on the Item

        Returns:
            str
        """
        return self.get_type()

    @type.setter
    def type(self, v: str) -> None:
        self.set_type(v)

    def get_type(self, asset: Optional[Asset] = None) -> str:
        """Gets an Item or an Asset type.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or 'pc:type' not in asset.properties:
            result = self.item.properties.get('pc:type')
        else:
            result = asset.properties.get('pc:type')

        if result is None:
            raise STACError(f"pc:type not found on point cloud item with ID {self.item.id}")

        return result

    def set_type(self, type: str, asset: Optional[Asset] = None) -> None:
        """Set an Item or an Asset type.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        self._set_property('pc:type', type, asset)

    @property
    def encoding(self) -> str:
        """Get or sets the content-encoding for the item.

        The content-encoding is the underlying encoding format for the point cloud.
        Examples may include: laszip, ascii, binary, etc.

        Returns:
            str
        """
        return self.get_encoding()

    @encoding.setter
    def encoding(self, v: str) -> None:
        self.set_encoding(v)

    def get_encoding(self, asset: Optional[Asset] = None) -> str:
        """Gets an Item or an Asset encoding.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or 'pc:encoding' not in asset.properties:
            result = self.item.properties.get('pc:encoding')
        else:
            result = asset.properties.get('pc:encoding')

        if result is None:
            raise STACError(f"pc:encoding not found on point cloud item with ID {self.item.id}")

        return result

    def set_encoding(self, encoding: str, asset: Optional[Asset] = None) -> None:
        """Set an Item or an Asset encoding.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        self._set_property('pc:encoding', encoding, asset)

    @property
    def schemas(self) -> List[PointcloudSchema]:
        """Get or sets a

        The schemas represent the structure of the data attributes in the pointcloud,
        and is represented as a sequential array of items that define the dimensions
        and their types,

        Returns:
            List[PointcloudSchema]
        """
        return self.get_schemas()

    @schemas.setter
    def schemas(self, v: List[PointcloudSchema]) -> None:
        self.set_schemas(v)

    def get_schemas(self, asset: Optional[Asset] = None) -> List[PointcloudSchema]:
        """Gets an Item or an Asset projection geometry.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            List[PointcloudSchema]
        """
        if asset is None or 'pc:schemas' not in asset.properties:
            schemas = self.item.properties.get('pc:schemas')
        else:
            schemas = asset.properties.get('pc:schemas')

        if schemas is None:
            return []
        else:
            return [PointcloudSchema(s) for s in schemas]

    def set_schemas(self, schemas: List[PointcloudSchema], asset: Optional[Asset] = None) -> None:
        """Set an Item or an Asset schema

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        dicts = [s.to_dict() for s in schemas]
        self._set_property('pc:schemas', dicts, asset)

    @property
    def density(self) -> Optional[float]:
        """Get or sets the density for the item.

        Density is defined as the number of points per square unit area.

        Returns:
            int
        """
        return self.get_density()

    @density.setter
    def density(self, v: Optional[float]) -> None:
        self.set_density(v)

    def get_density(self, asset: Optional[Asset] = None) -> Optional[float]:
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

    def set_density(self, density: Optional[float], asset: Optional[Asset] = None) -> None:
        """Set an Item or an Asset density property.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        self._set_property('pc:density', density, asset)

    @property
    def statistics(self) -> Optional[List[PointcloudStatistic]]:
        """Get or sets the statistics for each property of the dataset.

        A sequential array of items mapping to pc:schemas defines per-channel statistics.

        Example::

            item.ext.pointcloud.statistics = [{ 'name': 'red', 'min': 0, 'max': 255 }]
        """
        return self.get_statistics()

    @statistics.setter
    def statistics(self, v: Optional[List[PointcloudStatistic]]) -> None:
        self.set_statistics(v)

    def get_statistics(self, asset: Optional[Asset] = None) -> Optional[List[PointcloudStatistic]]:
        """Gets an Item or an Asset centroid.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            List[PointCloudStatistics] or None
        """
        if asset is None or 'pc:statistics' not in asset.properties:
            stats = self.item.properties.get('pc:statistics')
            if stats:
                return [PointcloudStatistic(s) for s in stats]
            else:
                return None
        else:
            return [PointcloudStatistic.create(s) for s in asset.properties['pc:statistics']]

    def set_statistics(self,
                       statistics: Optional[List[PointcloudStatistic]],
                       asset: Optional[Asset] = None) -> None:
        """Set an Item or an Asset centroid.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if statistics is not None:
            self._set_property('pc:statistics', [s.to_dict() for s in statistics], asset)
        else:
            self._set_property('pc:statistics', None, asset)

    @classmethod
    def _object_links(cls) -> List[str]:
        return []

    @classmethod
    def from_item(cls, item: Item) -> "PointcloudItemExt":
        return cls(item)


POINTCLOUD_EXTENSION_DEFINITION: ExtensionDefinition = ExtensionDefinition(
    Extensions.POINTCLOUD, [ExtendedObject(Item, PointcloudItemExt)])
