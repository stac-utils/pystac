"""Implements the Point Cloud extension.

https://github.com/stac-extensions/pointcloud
"""

from typing import Any, Dict, Generic, List, Optional, Set, TypeVar, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import map_opt

T = TypeVar("T", pystac.Item, pystac.Asset)

SCHEMA_URI = "https://stac-extensions.github.io/pointcloud/v1.0.0/schema.json"

COUNT_PROP = "pc:count"
TYPE_PROP = "pc:type"
ENCODING_PROP = "pc:encoding"
SCHEMAS_PROP = "pc:schemas"
DENSITY_PROP = "pc:density"
STATISTICS_PROP = "pc:statistics"


class PointcloudSchema:
    """Defines a schema for dimension of a pointcloud (e.g., name, size, type)

    Use PointCloudSchema.create to create a new instance of PointCloudSchema from
    properties.
    """

    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    def apply(self, name: str, size: int, type: str) -> None:
        """Sets the properties for this PointCloudSchema.

        Args:
           name (str): The name of dimension.
           size (int): The size of the dimension in bytes. Whole bytes are supported.
           type (str): Dimension type. Valid values are `floating`, `unsigned`, and
           `signed`
        """
        self.properties["name"] = name
        self.properties["size"] = size
        self.properties["type"] = type

    @classmethod
    def create(cls, name: str, size: int, type: str) -> "PointcloudSchema":
        """Creates a new PointCloudSchema.

        Args:
           name (str): The name of dimension.
           size (int): The size of the dimension in bytes. Whole bytes are supported.
           type (str): Dimension type. Valid values are `floating`, `unsigned`, and
           `signed`

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
        result = self.properties.get("size")
        if result is None:
            raise pystac.STACError(
                f"Pointcloud schema does not have size property: {self.properties}"
            )
        return result

    @size.setter
    def size(self, v: int) -> None:
        if not isinstance(v, int):
            raise pystac.STACError("size must be an int! Invalid input: {}".format(v))

        self.properties["size"] = v

    @property
    def name(self) -> str:
        """Get or sets the name property for this PointCloudSchema.

        Returns:
            str
        """
        result = self.properties.get("name")
        if result is None:
            raise pystac.STACError(
                f"Pointcloud schema does not have name property: {self.properties}"
            )
        return result

    @name.setter
    def name(self, v: str) -> None:
        self.properties["name"] = v

    @property
    def type(self) -> str:
        """Get or sets the type property. Valid values are `floating`, `unsigned`, and `signed`

        Returns:
            str
        """
        result = self.properties.get("type")
        if result is None:
            raise pystac.STACError(
                f"Pointcloud schema has no type property: {self.properties}"
            )
        return result

    @type.setter
    def type(self, v: str) -> None:
        self.properties["type"] = v

    def __repr__(self) -> str:
        return "<PointCloudSchema name={} size={} type={}>".format(
            self.name, self.size, self.type
        )

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of this PointCloudSchema.

        Returns:
            dict: The wrapped dict of the PointCloudSchema that can be written out as
            JSON.
        """
        return self.properties


class PointcloudStatistic:
    """Defines a single statistic for Pointcloud channel or dimension

    Use PointcloudStatistic.create to create a new instance of LabelClasses from
    property values.
    """

    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    def apply(
        self,
        name: str,
        position: Optional[int] = None,
        average: Optional[float] = None,
        count: Optional[int] = None,
        maximum: Optional[float] = None,
        minimum: Optional[float] = None,
        stddev: Optional[float] = None,
        variance: Optional[float] = None,
    ) -> None:
        """Sets the properties for this PointcloudStatistic.

        Args:
            name (str): REQUIRED. The name of the channel.
            position (int): Position of the channel in the schema.
            average (float): The average of the channel.
            count (int): The number of elements in the channel.
            maximum (float): The maximum value of the channel.
            minimum (float): The minimum value of the channel.
            stddev (float): The standard deviation of the channel.
            variance (float): The variance of the channel.
        """
        self.properties["name"] = name
        self.properties["position"] = position
        self.properties["average"] = average
        self.properties["count"] = count
        self.properties["maximum"] = maximum
        self.properties["minimum"] = minimum
        self.properties["stddev"] = stddev
        self.properties["variance"] = variance

    @classmethod
    def create(
        cls,
        name: str,
        position: Optional[int] = None,
        average: Optional[float] = None,
        count: Optional[int] = None,
        maximum: Optional[float] = None,
        minimum: Optional[float] = None,
        stddev: Optional[float] = None,
        variance: Optional[float] = None,
    ) -> "PointcloudStatistic":
        """Creates a new PointcloudStatistic class.

        Args:
            name (str): REQUIRED. The name of the channel.
            position (int): Position of the channel in the schema.
            average (float) The average of the channel.
            count (int): The number of elements in the channel.
            maximum (float): The maximum value of the channel.
            minimum (float): The minimum value of the channel.
            stddev (float): The standard deviation of the channel.
            variance (float): The variance of the channel.

        Returns:
            LabelClasses
        """
        c = cls({})
        c.apply(
            name=name,
            position=position,
            average=average,
            count=count,
            maximum=maximum,
            minimum=minimum,
            stddev=stddev,
            variance=variance,
        )
        return c

    @property
    def name(self) -> str:
        """Get or sets the name property

        Returns:
            str
        """
        result = self.properties.get("name")
        if result is None:
            raise pystac.STACError(
                f"Pointcloud statistics does not have name property: {self.properties}"
            )
        return result

    @name.setter
    def name(self, v: str) -> None:
        if v is not None:
            self.properties["name"] = v
        else:
            self.properties.pop("name", None)

    @property
    def position(self) -> Optional[int]:
        """Get or sets the position property

        Returns:
            int
        """
        return self.properties.get("position")

    @position.setter
    def position(self, v: Optional[int]) -> None:
        if v is not None:
            self.properties["position"] = v
        else:
            self.properties.pop("position", None)

    @property
    def average(self) -> Optional[float]:
        """Get or sets the average property

        Returns:
            float
        """
        return self.properties.get("average")

    @average.setter
    def average(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties["average"] = v
        else:
            self.properties.pop("average", None)

    @property
    def count(self) -> Optional[int]:
        """Get or sets the count property

        Returns:
            int
        """
        return self.properties.get("count")

    @count.setter
    def count(self, v: Optional[int]) -> None:
        if v is not None:
            self.properties["count"] = v
        else:
            self.properties.pop("count", None)

    @property
    def maximum(self) -> Optional[float]:
        """Get or sets the maximum property

        Returns:
            float
        """
        return self.properties.get("maximum")

    @maximum.setter
    def maximum(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties["maximum"] = v
        else:
            self.properties.pop("maximum", None)

    @property
    def minimum(self) -> Optional[float]:
        """Get or sets the minimum property

        Returns:
            float
        """
        return self.properties.get("minimum")

    @minimum.setter
    def minimum(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties["minimum"] = v
        else:
            self.properties.pop("minimum", None)

    @property
    def stddev(self) -> Optional[float]:
        """Get or sets the stddev property

        Returns:
            float
        """
        return self.properties.get("stddev")

    @stddev.setter
    def stddev(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties["stddev"] = v
        else:
            self.properties.pop("stddev", None)

    @property
    def variance(self) -> Optional[float]:
        """Get or sets the variance property

        Returns:
            float
        """
        return self.properties.get("variance")

    @variance.setter
    def variance(self, v: Optional[float]) -> None:
        if v is not None:
            self.properties["variance"] = v
        else:
            self.properties.pop("variance", None)

    def __repr__(self) -> str:
        return "<PointcloudStatistic statistics={}>".format(str(self.properties))

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of this PointcloudStatistic.

        Returns:
            dict: The wrapped dict of the PointcloudStatistic that can be written out
            as JSON.
        """
        return self.properties


class PointcloudExtension(
    Generic[T], PropertiesExtension, ExtensionManagementMixin[pystac.Item]
):
    """PointcloudItemExt is the extension of an Item in the PointCloud Extension.
    The Pointclout extension adds pointcloud information to STAC Items.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The Item that is being extended.

    """

    def apply(
        self,
        count: int,
        type: str,
        encoding: str,
        schemas: List[PointcloudSchema],
        density: Optional[float] = None,
        statistics: Optional[List[PointcloudStatistic]] = None,
        epsg: Optional[int] = None,
    ) -> None:  # TODO: Remove epsg per spec
        """Applies Pointcloud extension properties to the extended Item.

        Args:
            count (int): REQUIRED. The number of points in the cloud.
            type (str): REQUIRED. Phenomenology type for the point cloud. Possible valid
                values might include lidar, eopc, radar, sonar, or otherThe type of file
                or data format of the cloud.
            encoding (str): REQUIRED. Content encoding or format of the data.
            schemas (List[PointcloudSchema]): REQUIRED. A sequential array of items
            that define the
                dimensions and their types.
            density (float or None): Number of points per square unit area.
            statistics (List[int] or None): A sequential array of items mapping to
                pc:schemas defines per-channel statistics.
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
        result = self._get_property(COUNT_PROP, int)
        if result is None:
            raise pystac.RequiredPropertyMissing(self, COUNT_PROP)
        return result

    @count.setter
    def count(self, v: int) -> None:
        self._set_property(COUNT_PROP, v, pop_if_none=False)

    @property
    def type(self) -> str:
        """Get or sets the pc:type prop on the Item

        Returns:
            str
        """
        result = self._get_property(TYPE_PROP, str)
        if result is None:
            raise pystac.RequiredPropertyMissing(self, TYPE_PROP)
        return result

    @type.setter
    def type(self, v: str) -> None:
        self._set_property(TYPE_PROP, v, pop_if_none=False)

    @property
    def encoding(self) -> str:
        """Get or sets the content-encoding for the item.

        The content-encoding is the underlying encoding format for the point cloud.
        Examples may include: laszip, ascii, binary, etc.

        Returns:
            str
        """
        result = self._get_property(ENCODING_PROP, str)
        if result is None:
            raise pystac.RequiredPropertyMissing(self, ENCODING_PROP)
        return result

    @encoding.setter
    def encoding(self, v: str) -> None:
        self._set_property(ENCODING_PROP, v, pop_if_none=False)

    @property
    def schemas(self) -> List[PointcloudSchema]:
        """Get or sets a

        The schemas represent the structure of the data attributes in the pointcloud,
        and is represented as a sequential array of items that define the dimensions
        and their types,

        Returns:
            List[PointcloudSchema]
        """
        result = self._get_property(SCHEMAS_PROP, List[Dict[str, Any]])
        if result is None:
            raise pystac.RequiredPropertyMissing(self, SCHEMAS_PROP)
        return [PointcloudSchema(s) for s in result]

    @schemas.setter
    def schemas(self, v: List[PointcloudSchema]) -> None:
        self._set_property(SCHEMAS_PROP, [x.to_dict() for x in v], pop_if_none=False)

    @property
    def density(self) -> Optional[float]:
        """Get or sets the density for the item.

        Density is defined as the number of points per square unit area.

        Returns:
            int
        """
        return self._get_property(DENSITY_PROP, float)

    @density.setter
    def density(self, v: Optional[float]) -> None:
        self._set_property(DENSITY_PROP, v)

    @property
    def statistics(self) -> Optional[List[PointcloudStatistic]]:
        """Get or sets the statistics for each property of the dataset.

        A sequential array of items mapping to pc:schemas defines per-channel
        statistics.

        Example::

            item.ext.pointcloud.statistics = [{ 'name': 'red', 'min': 0, 'max': 255 }]
        """
        result = self._get_property(STATISTICS_PROP, List[Dict[str, Any]])
        return map_opt(lambda stats: [PointcloudStatistic(s) for s in stats], result)

    @statistics.setter
    def statistics(self, v: Optional[List[PointcloudStatistic]]) -> None:
        set_value = map_opt(lambda stats: [s.to_dict() for s in stats], v)
        self._set_property(STATISTICS_PROP, set_value)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @staticmethod
    def ext(obj: T) -> "PointcloudExtension[T]":
        if isinstance(obj, pystac.Item):
            return cast(PointcloudExtension[T], ItemPointcloudExtension(obj))
        elif isinstance(obj, pystac.Asset):
            return cast(PointcloudExtension[T], AssetPointcloudExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"File extension does not apply to type {type(obj)}"
            )


class ItemPointcloudExtension(PointcloudExtension[pystac.Item]):
    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return "<ItemPointcloudExtension Item id={}>".format(self.item.id)


class AssetPointcloudExtension(PointcloudExtension[pystac.Asset]):
    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.properties
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]
            self.repr_id = f"href={asset.href} item.id={asset.owner.id}"
        else:
            self.repr_id = f"href={asset.href}"

    def __repr__(self) -> str:
        return f"<AssetPointcloudExtension Asset {self.repr_id}>"


class PointcloudExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: Set[str] = set(["pointcloud"])
    stac_object_types: Set[pystac.STACObjectType] = set([pystac.STACObjectType.ITEM])


POINTCLOUD_EXTENSION_HOOKS = PointcloudExtensionHooks()
