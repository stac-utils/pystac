"""Implements the :stac-ext:`Point Cloud Extension <pointcloud>`."""

from __future__ import annotations

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
from pystac.summaries import RangeSummary
from pystac.utils import StringEnum, get_required, map_opt

#: Generalized version of :class:`~pystac.Item`, :class:`~pystac.Asset`,
#: or :class:`~pystac.ItemAssetDefinition`
T = TypeVar("T", pystac.Item, pystac.Asset, pystac.ItemAssetDefinition)

SCHEMA_URI: str = "https://stac-extensions.github.io/pointcloud/v1.0.0/schema.json"
PREFIX: str = "pc:"

COUNT_PROP = PREFIX + "count"
TYPE_PROP = PREFIX + "type"
ENCODING_PROP = PREFIX + "encoding"
SCHEMAS_PROP = PREFIX + "schemas"
DENSITY_PROP = PREFIX + "density"
STATISTICS_PROP = PREFIX + "statistics"


class PhenomenologyType(StringEnum):
    """Valid values for the ``pc:type`` field in the :stac-ext:`Pointcloud Item
    Properties <pointcloud#item-properties>`."""

    LIDAR = "lidar"
    EOPC = "eopc"
    RADAR = "radar"
    SONAR = "sonar"
    OTHER = "other"


class SchemaType(StringEnum):
    """Valid values for the ``type`` field in a :stac-ext:`Schema Object
    <pointcloud#schema-object>`."""

    FLOATING = "floating"
    UNSIGNED = "unsigned"
    SIGNED = "signed"


class Schema:
    """Defines a schema for dimension of a pointcloud (e.g., name, size, type)

    Use :meth:`Schema.create` to create a new instance of ``Schema`` from
    properties.
    """

    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]) -> None:
        self.properties = properties

    def apply(self, name: str, size: int, type: SchemaType) -> None:
        """Sets the properties for this Schema.

        Args:
           name : The name of dimension.
           size : The size of the dimension in bytes. Whole bytes are supported.
           type : Dimension type. Valid values are ``floating``, ``unsigned``, and
           ``signed``
        """
        self.properties["name"] = name
        self.properties["size"] = size
        self.properties["type"] = type

    @classmethod
    def create(cls, name: str, size: int, type: SchemaType) -> Schema:
        """Creates a new Schema.

        Args:
           name : The name of dimension.
           size : The size of the dimension in bytes. Whole bytes are supported.
           type : Dimension type. Valid values are ``floating``, ``unsigned``, and
           ``signed``
        """
        c = cls({})
        c.apply(name=name, size=size, type=type)
        return c

    @property
    def size(self) -> int:
        """Gets or sets the size value."""
        return get_required(self.properties.get("size"), self, "size")

    @size.setter
    def size(self, v: int) -> None:
        if not isinstance(v, int):
            raise pystac.STACError(f"size must be an int! Invalid input: {v}")

        self.properties["size"] = v

    @property
    def name(self) -> str:
        """Gets or sets the name property for this Schema."""
        return get_required(self.properties.get("name"), self, "name")

    @name.setter
    def name(self, v: str) -> None:
        self.properties["name"] = v

    @property
    def type(self) -> SchemaType:
        """Gets or sets the type property. Valid values are ``floating``, ``unsigned``,
        and ``signed``."""
        return get_required(self.properties.get("type"), self, "type")

    @type.setter
    def type(self, v: SchemaType) -> None:
        self.properties["type"] = v

    def __repr__(self) -> str:
        return "<Schema name={} size={} type={}>".format(
            self.properties.get("name"),
            self.properties.get("size"),
            self.properties.get("type"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Returns this schema as a dictionary."""
        return self.properties


class Statistic:
    """Defines a single statistic for Pointcloud channel or dimension

    Use :meth:`Statistic.create` to create a new instance of
    ``Statistic`` from property values."""

    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]) -> None:
        self.properties = properties

    def apply(
        self,
        name: str,
        position: int | None = None,
        average: float | None = None,
        count: int | None = None,
        maximum: float | None = None,
        minimum: float | None = None,
        stddev: float | None = None,
        variance: float | None = None,
    ) -> None:
        """Sets the properties for this Statistic.

        Args:
            name : REQUIRED. The name of the channel.
            position : Optional position of the channel in the schema.
            average : Optional average of the channel.
            count : Optional number of elements in the channel.
            maximum : Optional maximum value of the channel.
            minimum : Optional minimum value of the channel.
            stddev : Optional standard deviation of the channel.
            variance : Optional variance of the channel.
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
        position: int | None = None,
        average: float | None = None,
        count: int | None = None,
        maximum: float | None = None,
        minimum: float | None = None,
        stddev: float | None = None,
        variance: float | None = None,
    ) -> Statistic:
        """Creates a new Statistic class.

        Args:
            name : REQUIRED. The name of the channel.
            position : Optional position of the channel in the schema.
            average : Optional average of the channel.
            count : Optional number of elements in the channel.
            maximum : Optional maximum value of the channel.
            minimum : Optional minimum value of the channel.
            stddev : Optional standard deviation of the channel.
            variance : Optional variance of the channel.
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
        """Gets or sets the name property."""
        return get_required(self.properties.get("name"), self, "name")

    @name.setter
    def name(self, v: str) -> None:
        if v is not None:
            self.properties["name"] = v
        else:
            self.properties.pop("name", None)

    @property
    def position(self) -> int | None:
        """Gets or sets the position property."""
        return self.properties.get("position")

    @position.setter
    def position(self, v: int | None) -> None:
        if v is not None:
            self.properties["position"] = v
        else:
            self.properties.pop("position", None)

    @property
    def average(self) -> float | None:
        """Gets or sets the average property."""
        return self.properties.get("average")

    @average.setter
    def average(self, v: float | None) -> None:
        if v is not None:
            self.properties["average"] = v
        else:
            self.properties.pop("average", None)

    @property
    def count(self) -> int | None:
        """Gets or sets the count property."""
        return self.properties.get("count")

    @count.setter
    def count(self, v: int | None) -> None:
        if v is not None:
            self.properties["count"] = v
        else:
            self.properties.pop("count", None)

    @property
    def maximum(self) -> float | None:
        """Gets or sets the maximum property."""
        return self.properties.get("maximum")

    @maximum.setter
    def maximum(self, v: float | None) -> None:
        if v is not None:
            self.properties["maximum"] = v
        else:
            self.properties.pop("maximum", None)

    @property
    def minimum(self) -> float | None:
        """Gets or sets the minimum property."""
        return self.properties.get("minimum")

    @minimum.setter
    def minimum(self, v: float | None) -> None:
        if v is not None:
            self.properties["minimum"] = v
        else:
            self.properties.pop("minimum", None)

    @property
    def stddev(self) -> float | None:
        """Gets or sets the stddev property."""
        return self.properties.get("stddev")

    @stddev.setter
    def stddev(self, v: float | None) -> None:
        if v is not None:
            self.properties["stddev"] = v
        else:
            self.properties.pop("stddev", None)

    @property
    def variance(self) -> float | None:
        """Gets or sets the variance property."""
        return self.properties.get("variance")

    @variance.setter
    def variance(self, v: float | None) -> None:
        if v is not None:
            self.properties["variance"] = v
        else:
            self.properties.pop("variance", None)

    def __repr__(self) -> str:
        return f"<Statistic statistics={str(self.properties)}>"

    def to_dict(self) -> dict[str, Any]:
        """Returns this statistic as a dictionary."""
        return self.properties

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Statistic):
            return NotImplemented
        return self.to_dict() == o.to_dict()


class PointcloudExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Item` or :class:`~pystac.Asset` with properties from the
    :stac-ext:`Point Cloud Extension <pointcloud>`. This class is generic over the type
    of STAC Object to be extended (e.g. :class:`~pystac.Item`,
    :class:`~pystac.Asset`).

    To create a concrete instance of :class:`PointcloudExtension`, use the
    :meth:`PointcloudExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> pc_ext = PointcloudExtension.ext(item)
    """

    name: Literal["pc"] = "pc"

    def apply(
        self,
        count: int,
        type: PhenomenologyType | str,
        encoding: str,
        schemas: list[Schema],
        density: float | None = None,
        statistics: list[Statistic] | None = None,
    ) -> None:
        """Applies Pointcloud extension properties to the extended Item.

        Args:
            count : REQUIRED. The number of points in the cloud.
            type : REQUIRED. Phenomenology type for the point cloud. Possible valid
                values might include lidar, eopc, radar, sonar, or otherThe type of file
                or data format of the cloud.
            encoding : REQUIRED. Content encoding or format of the data.
            schemas : REQUIRED. A sequential array of items
                that define the dimensions and their types.
            density : Number of points per square unit area.
            statistics : A sequential array of items mapping to
                pc:schemas defines per-channel statistics.
        """
        self.count = count
        self.type = type
        self.encoding = encoding
        self.schemas = schemas
        self.density = density
        self.statistics = statistics

    @property
    def count(self) -> int:
        """Gets or sets the number of points in the Item."""
        return get_required(self._get_property(COUNT_PROP, int), self, COUNT_PROP)

    @count.setter
    def count(self, v: int) -> None:
        self._set_property(COUNT_PROP, v, pop_if_none=False)

    @property
    def type(self) -> PhenomenologyType | str:
        """Gets or sets the phenomenology type for the point cloud."""
        return get_required(self._get_property(TYPE_PROP, str), self, TYPE_PROP)

    @type.setter
    def type(self, v: PhenomenologyType | str) -> None:
        self._set_property(TYPE_PROP, v, pop_if_none=False)

    @property
    def encoding(self) -> str:
        """Gets or sets the content encoding or format of the data."""
        return get_required(self._get_property(ENCODING_PROP, str), self, ENCODING_PROP)

    @encoding.setter
    def encoding(self, v: str) -> None:
        self._set_property(ENCODING_PROP, v, pop_if_none=False)

    @property
    def schemas(self) -> list[Schema]:
        """Gets or sets the list of :class:`Schema` instances defining
        dimensions and types for the data.
        """
        result = get_required(
            self._get_property(SCHEMAS_PROP, list[dict[str, Any]]), self, SCHEMAS_PROP
        )
        return [Schema(s) for s in result]

    @schemas.setter
    def schemas(self, v: list[Schema]) -> None:
        self._set_property(SCHEMAS_PROP, [x.to_dict() for x in v], pop_if_none=False)

    @property
    def density(self) -> float | None:
        """Gets or sets the number of points per square unit area."""
        return self._get_property(DENSITY_PROP, float)

    @density.setter
    def density(self, v: float | None) -> None:
        self._set_property(DENSITY_PROP, v)

    @property
    def statistics(self) -> list[Statistic] | None:
        """Gets or sets the list of :class:`Statistic` instances describing
        the pre-channel statistics. Elements in this list map to elements in the
        :attr:`PointcloudExtension.schemas` list."""
        result = self._get_property(STATISTICS_PROP, list[dict[str, Any]])
        return map_opt(lambda stats: [Statistic(s) for s in stats], result)

    @statistics.setter
    def statistics(self, v: list[Statistic] | None) -> None:
        set_value = map_opt(lambda stats: [s.to_dict() for s in stats], v)
        self._set_property(STATISTICS_PROP, set_value)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> PointcloudExtension[T]:
        """Extends the given STAC Object with properties from the :stac-ext:`Point Cloud
        Extension <pointcloud>`.

        This extension can be applied to instances of :class:`~pystac.Item` or
        :class:`~pystac.Asset`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(PointcloudExtension[T], ItemPointcloudExtension(obj))
        elif isinstance(obj, pystac.Asset):
            if obj.owner is not None and not isinstance(obj.owner, pystac.Item):
                raise pystac.ExtensionTypeError(
                    "Pointcloud extension does not apply to Collection Assets."
                )
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(PointcloudExtension[T], AssetPointcloudExtension(obj))
        elif isinstance(obj, pystac.ItemAssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(PointcloudExtension[T], ItemAssetsPointcloudExtension(obj))
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesPointcloudExtension:
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesPointcloudExtension(obj)


class ItemPointcloudExtension(PointcloudExtension[pystac.Item]):
    """A concrete implementation of :class:`PointcloudExtension` on an
    :class:`~pystac.Item` that extends the properties of the Item to include
    properties defined in the :stac-ext:`Point Cloud Extension <pointcloud>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`PointcloudExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: pystac.Item
    properties: dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemPointcloudExtension Item id={self.item.id}>"


class AssetPointcloudExtension(PointcloudExtension[pystac.Asset]):
    """A concrete implementation of :class:`PointcloudExtension` on an
    :class:`~pystac.Asset` that extends the Asset fields to include properties defined
    in the :stac-ext:`Point Cloud Extension <pointcloud>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`PointcloudExtension.ext` on an :class:`~pystac.Asset` to extend it.
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
            self.repr_id = f"href={asset.href} item.id={asset.owner.id}"
        else:
            self.repr_id = f"href={asset.href}"

    def __repr__(self) -> str:
        return f"<AssetPointcloudExtension Asset {self.repr_id}>"


class ItemAssetsPointcloudExtension(PointcloudExtension[pystac.ItemAssetDefinition]):
    properties: dict[str, Any]
    asset_defn: pystac.ItemAssetDefinition

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        self.asset_defn = item_asset
        self.properties = item_asset.properties


class SummariesPointcloudExtension(SummariesExtension):
    """A concrete implementation of :class:`~pystac.extensions.base.SummariesExtension`
    that extends the ``summaries`` field of a :class:`~pystac.Collection` to include
    properties defined in the :stac-ext:`Point Cloud Extension <pointcloud>`.
    """

    @property
    def count(self) -> RangeSummary[int] | None:
        return self.summaries.get_range(COUNT_PROP)

    @count.setter
    def count(self, v: RangeSummary[int] | None) -> None:
        self._set_summary(COUNT_PROP, v)

    @property
    def type(self) -> list[PhenomenologyType | str] | None:
        return self.summaries.get_list(TYPE_PROP)

    @type.setter
    def type(self, v: list[PhenomenologyType | str] | None) -> None:
        self._set_summary(TYPE_PROP, v)

    @property
    def encoding(self) -> list[str] | None:
        return self.summaries.get_list(ENCODING_PROP)

    @encoding.setter
    def encoding(self, v: list[str] | None) -> None:
        self._set_summary(ENCODING_PROP, v)

    @property
    def density(self) -> RangeSummary[float] | None:
        return self.summaries.get_range(DENSITY_PROP)

    @density.setter
    def density(self, v: RangeSummary[float] | None) -> None:
        self._set_summary(DENSITY_PROP, v)

    @property
    def statistics(self) -> list[Statistic] | None:
        return map_opt(
            lambda stats: [Statistic(d) for d in stats],
            self.summaries.get_list(STATISTICS_PROP),
        )

    @statistics.setter
    def statistics(self, v: list[Statistic] | None) -> None:
        self._set_summary(
            STATISTICS_PROP,
            map_opt(lambda stats: [s.to_dict() for s in stats], v),
        )


class PointcloudExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"pointcloud"}
    stac_object_types = {pystac.STACObjectType.ITEM}


POINTCLOUD_EXTENSION_HOOKS: ExtensionHooks = PointcloudExtensionHooks()
