"""Implements the :stac-ext:`Datacube Extension <datacube>`."""

from __future__ import annotations

from abc import ABC
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union, cast

import pystac
from pystac.extensions.base import ExtensionManagementMixin, PropertiesExtension
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import StringEnum, get_required, map_opt

T = TypeVar("T", pystac.Collection, pystac.Item, pystac.Asset)

SCHEMA_URI = "https://stac-extensions.github.io/datacube/v2.0.0/schema.json"

PREFIX: str = "cube:"
DIMENSIONS_PROP = PREFIX + "dimensions"
VARIABLES_PROP = PREFIX + "variables"

# Dimension properties
DIM_TYPE_PROP = "type"
DIM_DESC_PROP = "description"
DIM_AXIS_PROP = "axis"
DIM_EXTENT_PROP = "extent"
DIM_VALUES_PROP = "values"
DIM_STEP_PROP = "step"
DIM_REF_SYS_PROP = "reference_system"
DIM_UNIT_PROP = "unit"

# Variable properties
VAR_TYPE_PROP = "type"
VAR_DESC_PROP = "description"
VAR_EXTENT_PROP = "extent"
VAR_VALUES_PROP = "values"
VAR_DIMENSIONS_PROP = "dimensions"
VAR_UNIT_PROP = "unit"


class DimensionType(StringEnum):
    """Dimension object types for spatial and temporal Dimension Objects."""

    SPATIAL = "spatial"
    TEMPORAL = "temporal"


class HorizontalSpatialDimensionAxis(StringEnum):
    """Allowed values for ``axis`` field of :class:`HorizontalSpatialDimension`
    object."""

    X = "x"
    Y = "y"


class VerticalSpatialDimensionAxis(StringEnum):
    """Allowed values for ``axis`` field of :class:`VerticalSpatialDimension`
    object."""

    Z = "z"


class Dimension(ABC):
    """Object representing a dimension of the datacube. The fields contained in
    Dimension Object vary by ``type``. See the :stac-ext:`Datacube Dimension Object
    <datacube#dimension-object>` docs for details.
    """

    properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    @property
    def dim_type(self) -> Union[DimensionType, str]:
        """The type of the dimension. Must be ``"spatial"`` for :stac-ext:`Horizontal
        Spatial Dimension Objects <datacube#horizontal-spatial-dimension-object>` or
        :stac-ext:`Vertical Spatial Dimension Objects
        <datacube#vertical-spatial-dimension-object>`, and ``"temporal"`` for
        :stac-ext:`Temporal Dimension Objects <datacube#temporal-dimension-object>`. May
        be an arbitrary string for :stac-ext:`Additional Dimension Objects
        <datacube#additional-dimension-object>`."""
        return get_required(
            self.properties.get(DIM_TYPE_PROP), "cube:dimension", DIM_TYPE_PROP
        )

    @dim_type.setter
    def dim_type(self, v: Union[DimensionType, str]) -> None:
        self.properties[DIM_TYPE_PROP] = v

    @property
    def description(self) -> Optional[str]:
        """Detailed multi-line description to explain the dimension. `CommonMark 0.29
        <http://commonmark.org/>`__ syntax MAY be used for rich text representation."""
        return self.properties.get(DIM_DESC_PROP)

    @description.setter
    def description(self, v: Optional[str]) -> None:
        if v is None:
            self.properties.pop(DIM_DESC_PROP, None)
        else:
            self.properties[DIM_DESC_PROP] = v

    def to_dict(self) -> Dict[str, Any]:
        return self.properties

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> Dimension:
        dim_type: str = get_required(
            d.get(DIM_TYPE_PROP), "cube_dimension", DIM_TYPE_PROP
        )
        if dim_type == DimensionType.SPATIAL:
            axis: str = get_required(
                d.get(DIM_AXIS_PROP), "cube_dimension", DIM_AXIS_PROP
            )
            if axis == "z":
                return VerticalSpatialDimension(d)
            else:
                return HorizontalSpatialDimension(d)
        elif dim_type == DimensionType.TEMPORAL:
            # The v1.0.0 spec says that AdditionalDimensions can have
            # type 'temporal', but it is unclear how to differentiate that
            # from a temporal dimension. Just key off of type for now.
            # See https://github.com/stac-extensions/datacube/issues/5
            return TemporalDimension(d)
        else:
            return AdditionalDimension(d)


class HorizontalSpatialDimension(Dimension):
    @property
    def axis(self) -> HorizontalSpatialDimensionAxis:
        """Axis of the spatial dimension. Must be one of ``"x"`` or ``"y"``."""
        return get_required(
            self.properties.get(DIM_AXIS_PROP), "cube:dimension", DIM_AXIS_PROP
        )

    @axis.setter
    def axis(self, v: HorizontalSpatialDimensionAxis) -> None:
        self.properties[DIM_TYPE_PROP] = v

    @property
    def extent(self) -> List[float]:
        """Extent (lower and upper bounds) of the dimension as two-dimensional array.
        Open intervals with ``None`` are not allowed."""
        return get_required(
            self.properties.get(DIM_EXTENT_PROP), "cube:dimension", DIM_EXTENT_PROP
        )

    @extent.setter
    def extent(self, v: List[float]) -> None:
        self.properties[DIM_EXTENT_PROP] = v

    @property
    def values(self) -> Optional[List[float]]:
        """Optional set of all potential values."""
        return self.properties.get(DIM_VALUES_PROP)

    @values.setter
    def values(self, v: Optional[List[float]]) -> None:
        if v is None:
            self.properties.pop(DIM_VALUES_PROP, None)
        else:
            self.properties[DIM_VALUES_PROP] = v

    @property
    def step(self) -> Optional[float]:
        """The space between the values. Use ``None`` for irregularly spaced steps."""
        return self.properties.get(DIM_STEP_PROP)

    @step.setter
    def step(self, v: Optional[float]) -> None:
        self.properties[DIM_STEP_PROP] = v

    def clear_step(self) -> None:
        """Setting step to None sets it to the null value,
        which means irregularly spaced steps. Use clear_step
        to remove it from the properties."""
        self.properties.pop(DIM_STEP_PROP, None)

    @property
    def reference_system(self) -> Optional[Union[str, float, Dict[str, Any]]]:
        """The spatial reference system for the data, specified as `numerical EPSG code
        <http://www.epsg-registry.org/>`__, `WKT2 (ISO 19162) string
        <http://docs.opengeospatial.org/is/18-010r7/18-010r7.html>`__ or `PROJJSON
        object <https://proj.org/specifications/projjson.html>`__.
        Defaults to EPSG code 4326."""
        return self.properties.get(DIM_REF_SYS_PROP)

    @reference_system.setter
    def reference_system(self, v: Optional[Union[str, float, Dict[str, Any]]]) -> None:
        if v is None:
            self.properties.pop(DIM_REF_SYS_PROP, None)
        else:
            self.properties[DIM_REF_SYS_PROP] = v


class VerticalSpatialDimension(Dimension):
    @property
    def axis(self) -> VerticalSpatialDimensionAxis:
        """Axis of the spatial dimension. Always ``"z"``."""
        return get_required(
            self.properties.get(DIM_AXIS_PROP), "cube:dimension", DIM_AXIS_PROP
        )

    @axis.setter
    def axis(self, v: VerticalSpatialDimensionAxis) -> None:
        self.properties[DIM_TYPE_PROP] = v

    @property
    def extent(self) -> Optional[List[Optional[float]]]:
        """If the dimension consists of `ordinal
        <https://en.wikipedia.org/wiki/Level_of_measurement#Ordinal_scale>`__ values,
        the extent (lower and upper bounds) of the values as two-dimensional array. Use
        null for open intervals."""
        return self.properties.get(DIM_EXTENT_PROP)

    @extent.setter
    def extent(self, v: Optional[List[Optional[float]]]) -> None:
        if v is None:
            self.properties.pop(DIM_EXTENT_PROP, None)
        else:
            self.properties[DIM_EXTENT_PROP] = v

    @property
    def values(self) -> Optional[Union[List[float], List[str]]]:
        """A set of all potential values, especially useful for `nominal
        <https://en.wikipedia.org/wiki/Level_of_measurement#Nominal_level>`__ values."""

        return self.properties.get(DIM_VALUES_PROP)

    @values.setter
    def values(self, v: Optional[Union[List[float], List[str]]]) -> None:
        if v is None:
            self.properties.pop(DIM_VALUES_PROP, None)
        else:
            self.properties[DIM_VALUES_PROP] = v

    @property
    def step(self) -> Optional[float]:
        """If the dimension consists of `interval
        <https://en.wikipedia.org/wiki/Level_of_measurement#Interval_scale>`__ values,
        the space between the values. Use null for irregularly spaced steps."""
        return self.properties.get(DIM_STEP_PROP)

    @step.setter
    def step(self, v: Optional[float]) -> None:
        self.properties[DIM_STEP_PROP] = v

    def clear_step(self) -> None:
        """Setting step to None sets it to the null value,
        which means irregularly spaced steps. Use clear_step
        to remove it from the properties."""
        self.properties.pop(DIM_STEP_PROP, None)

    @property
    def unit(self) -> Optional[str]:
        """The unit of measurement for the data, preferably compliant to `UDUNITS-2
        <https://ncics.org/portfolio/other-resources/udunits2/>`__ units (singular)."""
        return self.properties.get(DIM_UNIT_PROP)

    @unit.setter
    def unit(self, v: Optional[str]) -> None:
        if v is None:
            self.properties.pop(DIM_UNIT_PROP, None)
        else:
            self.properties[DIM_UNIT_PROP] = v

    @property
    def reference_system(self) -> Optional[Union[str, float, Dict[str, Any]]]:
        """The spatial reference system for the data, specified as `numerical EPSG code
        <http://www.epsg-registry.org/>`__, `WKT2 (ISO 19162) string
        <http://docs.opengeospatial.org/is/18-010r7/18-010r7.html>`__ or `PROJJSON
        object <https://proj.org/specifications/projjson.html>`__.
        Defaults to EPSG code 4326."""
        return self.properties.get(DIM_REF_SYS_PROP)

    @reference_system.setter
    def reference_system(self, v: Optional[Union[str, float, Dict[str, Any]]]) -> None:
        if v is None:
            self.properties.pop(DIM_REF_SYS_PROP, None)
        else:
            self.properties[DIM_REF_SYS_PROP] = v


class TemporalDimension(Dimension):
    @property
    def extent(self) -> Optional[List[Optional[str]]]:
        """Extent (lower and upper bounds) of the dimension as two-dimensional array.
        The dates and/or times must be strings compliant to `ISO 8601
        <https://en.wikipedia.org/wiki/ISO_8601>`__. ``None`` is allowed for open date
        ranges."""
        return self.properties.get(DIM_EXTENT_PROP)

    @extent.setter
    def extent(self, v: Optional[List[Optional[str]]]) -> None:
        if v is None:
            self.properties.pop(DIM_EXTENT_PROP, None)
        else:
            self.properties[DIM_EXTENT_PROP] = v

    @property
    def values(self) -> Optional[List[str]]:
        """If the dimension consists of set of specific values they can be listed here.
        The dates and/or times must be strings compliant to `ISO 8601
        <https://en.wikipedia.org/wiki/ISO_8601>`__."""
        return self.properties.get(DIM_VALUES_PROP)

    @values.setter
    def values(self, v: Optional[List[str]]) -> None:
        if v is None:
            self.properties.pop(DIM_VALUES_PROP, None)
        else:
            self.properties[DIM_VALUES_PROP] = v

    @property
    def step(self) -> Optional[str]:
        """The space between the temporal instances as `ISO 8601 duration
        <https://en.wikipedia.org/wiki/ISO_8601#Durations>`__, e.g. P1D. Use null for
        irregularly spaced steps."""
        return self.properties.get(DIM_STEP_PROP)

    @step.setter
    def step(self, v: Optional[str]) -> None:
        self.properties[DIM_STEP_PROP] = v

    def clear_step(self) -> None:
        """Setting step to None sets it to the null value,
        which means irregularly spaced steps. Use clear_step
        to remove it from the properties."""
        self.properties.pop(DIM_STEP_PROP, None)


class AdditionalDimension(Dimension):
    @property
    def extent(self) -> Optional[List[Optional[float]]]:
        """If the dimension consists of `ordinal
        <https://en.wikipedia.org/wiki/Level_of_measurement#Ordinal_scale>`__ values,
        the extent (lower and upper bounds) of the values as two-dimensional array. Use
        null for open intervals."""
        return self.properties.get(DIM_EXTENT_PROP)

    @extent.setter
    def extent(self, v: Optional[List[Optional[float]]]) -> None:
        if v is None:
            self.properties.pop(DIM_EXTENT_PROP, None)
        else:
            self.properties[DIM_EXTENT_PROP] = v

    @property
    def values(self) -> Optional[Union[List[str], List[float]]]:
        """A set of all potential values, especially useful for `nominal
        <https://en.wikipedia.org/wiki/Level_of_measurement#Nominal_level>`__ values."""
        return self.properties.get(DIM_VALUES_PROP)

    @values.setter
    def values(self, v: Optional[Union[List[str], List[float]]]) -> None:
        if v is None:
            self.properties.pop(DIM_VALUES_PROP, None)
        else:
            self.properties[DIM_VALUES_PROP] = v

    @property
    def step(self) -> Optional[float]:
        """If the dimension consists of `interval
        <https://en.wikipedia.org/wiki/Level_of_measurement#Interval_scale>`__ values,
        the space between the values. Use null for irregularly spaced steps."""
        return self.properties.get(DIM_STEP_PROP)

    @step.setter
    def step(self, v: Optional[float]) -> None:
        self.properties[DIM_STEP_PROP] = v

    def clear_step(self) -> None:
        """Setting step to None sets it to the null value,
        which means irregularly spaced steps. Use clear_step
        to remove it from the properties."""
        self.properties.pop(DIM_STEP_PROP, None)

    @property
    def unit(self) -> Optional[str]:
        """The unit of measurement for the data, preferably compliant to `UDUNITS-2
        units <https://ncics.org/portfolio/other-resources/udunits2/>`__ (singular)."""
        return self.properties.get(DIM_UNIT_PROP)

    @unit.setter
    def unit(self, v: Optional[str]) -> None:
        if v is None:
            self.properties.pop(DIM_UNIT_PROP, None)
        else:
            self.properties[DIM_UNIT_PROP] = v

    @property
    def reference_system(self) -> Optional[Union[str, float, Dict[str, Any]]]:
        """The reference system for the data."""
        return self.properties.get(DIM_REF_SYS_PROP)

    @reference_system.setter
    def reference_system(self, v: Optional[Union[str, float, Dict[str, Any]]]) -> None:
        if v is None:
            self.properties.pop(DIM_REF_SYS_PROP, None)
        else:
            self.properties[DIM_REF_SYS_PROP] = v


class VariableType(StringEnum):
    """Variable object types"""

    DATA = "data"
    AUXILIARY = "auxiliary"


class Variable:
    """Object representing a variable in the datacube. The dimensions field lists
    zero or more :stac-ext:`Datacube Dimension Object <datacube#dimension-object>`
    instances. See the :stac-ext:`Datacube Variable Object
    <datacube#variable-object>` docs for details.
    """

    properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    @property
    def dimensions(self) -> List[str]:
        """The dimensions of the variable. Should refer to keys in the
        ``cube:dimensions`` object or be an empty list if the variable has no
        dimensions
        """
        return get_required(
            self.properties.get(VAR_DIMENSIONS_PROP),
            "cube:variable",
            VAR_DIMENSIONS_PROP,
        )

    @dimensions.setter
    def dimensions(self, v: List[str]) -> None:
        self.properties[VAR_DIMENSIONS_PROP] = v

    @property
    def var_type(self) -> Union[VariableType, str]:
        """Type of the variable, either ``data`` or ``auxiliary``"""
        return get_required(
            self.properties.get(VAR_TYPE_PROP), "cube:variable", VAR_TYPE_PROP
        )

    @var_type.setter
    def var_type(self, v: Union[VariableType, str]) -> None:
        self.properties[VAR_TYPE_PROP] = v

    @property
    def description(self) -> Optional[str]:
        """Detailed multi-line description to explain the variable. `CommonMark 0.29
        <http://commonmark.org/>`__ syntax MAY be used for rich text representation."""
        return self.properties.get(VAR_DESC_PROP)

    @description.setter
    def description(self, v: Optional[str]) -> None:
        if v is None:
            self.properties.pop(VAR_DESC_PROP, None)
        else:
            self.properties[VAR_DESC_PROP] = v

    @property
    def extent(self) -> List[Union[float, str, None]]:
        """If the variable consists of `ordinal values
        <https://en.wikipedia.org/wiki/Level_of_measurement#Ordinal_scale>`, the extent
        (lower and upper bounds) of the values as two-dimensional array. Use ``None``
        for open intervals"""
        return get_required(
            self.properties.get(VAR_EXTENT_PROP), "cube:variable", VAR_EXTENT_PROP
        )

    @extent.setter
    def extent(self, v: List[Union[float, str, None]]) -> None:
        self.properties[VAR_EXTENT_PROP] = v

    @property
    def values(self) -> Optional[List[Union[float, str]]]:
        """A set of all potential values, especially useful for `nominal values
        <https://en.wikipedia.org/wiki/Level_of_measurement#Nominal_level>`."""
        return self.properties.get(VAR_VALUES_PROP)

    @values.setter
    def values(self, v: Optional[List[Union[float, str]]]) -> None:
        if v is None:
            self.properties.pop(VAR_VALUES_PROP)
        else:
            self.properties[VAR_VALUES_PROP] = v

    @property
    def unit(self) -> Optional[str]:
        """The unit of measurement for the data, preferably compliant to `UDUNITS-2
        <https://ncics.org/portfolio/other-resources/udunits2/>` units (singular)"""
        return self.properties.get(VAR_UNIT_PROP)

    @unit.setter
    def unit(self, v: Optional[str]) -> None:
        if v is None:
            self.properties.pop(VAR_UNIT_PROP)
        else:
            self.properties[VAR_UNIT_PROP] = v

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> Variable:
        return Variable(d)

    def to_dict(self) -> Dict[str, Any]:
        return self.properties


class DatacubeExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Union[pystac.Collection, pystac.Item]],
):
    """An abstract class that can be used to extend the properties of a
    :class:`~pystac.Collection`, :class:`~pystac.Item`, or :class:`~pystac.Asset` with
    properties from the :stac-ext:`Datacube Extension <datacube>`. This class is
    generic over the type of STAC Object to be extended (e.g. :class:`~pystac.Item`,
    :class:`~pystac.Asset`).

    To create a concrete instance of :class:`DatacubeExtension`, use the
    :meth:`DatacubeExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> dc_ext = DatacubeExtension.ext(item)
    """

    def apply(
        self,
        dimensions: Dict[str, Dimension],
        variables: Optional[Dict[str, Variable]] = None,
    ) -> None:
        """Applies label extension properties to the extended
        :class:`~pystac.Collection`, :class:`~pystac.Item` or :class:`~pystac.Asset`.

        Args:
            dimensions : Dictionary mapping dimension name to a :class:`Dimension`
                object.
            variables : Dictionary mapping variable name to a :class:`Variable`
                object.
        """
        self.dimensions = dimensions
        self.variables = variables

    @property
    def dimensions(self) -> Dict[str, Dimension]:
        """Dictionary mapping dimension name to a :class:`Dimension` object."""
        result = get_required(
            self._get_property(DIMENSIONS_PROP, Dict[str, Any]), self, DIMENSIONS_PROP
        )
        return {k: Dimension.from_dict(v) for k, v in result.items()}

    @dimensions.setter
    def dimensions(self, v: Dict[str, Dimension]) -> None:
        self._set_property(DIMENSIONS_PROP, {k: dim.to_dict() for k, dim in v.items()})

    @property
    def variables(self) -> Optional[Dict[str, Variable]]:
        """Dictionary mapping variable name to a :class:`Variable` object."""
        result = self._get_property(VARIABLES_PROP, Dict[str, Any])

        if result is None:
            return None
        return {k: Variable.from_dict(v) for k, v in result.items()}

    @variables.setter
    def variables(self, v: Optional[Dict[str, Variable]]) -> None:
        self._set_property(
            VARIABLES_PROP,
            map_opt(
                lambda variables: {k: var.to_dict() for k, var in variables.items()}, v
            ),
        )

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> DatacubeExtension[T]:
        """Extends the given STAC Object with properties from the :stac-ext:`Datacube
        Extension <datacube>`.

        This extension can be applied to instances of :class:`~pystac.Collection`,
        :class:`~pystac.Item` or :class:`~pystac.Asset`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Collection):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(DatacubeExtension[T], CollectionDatacubeExtension(obj))
        if isinstance(obj, pystac.Item):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(DatacubeExtension[T], ItemDatacubeExtension(obj))
        elif isinstance(obj, pystac.Asset):
            cls.validate_owner_has_extension(obj, add_if_missing)
            return cast(DatacubeExtension[T], AssetDatacubeExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"Datacube extension does not apply to type '{type(obj).__name__}'"
            )


class CollectionDatacubeExtension(DatacubeExtension[pystac.Collection]):
    """A concrete implementation of :class:`DatacubeExtension` on an
    :class:`~pystac.Collection` that extends the properties of the Item to include
    properties defined in the :stac-ext:`Datacube Extension <datacube>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`DatacubeExtension.ext` on an :class:`~pystac.Collection` to extend it.
    """

    collection: pystac.Collection
    properties: Dict[str, Any]

    def __init__(self, collection: pystac.Collection):
        self.collection = collection
        self.properties = collection.extra_fields

    def __repr__(self) -> str:
        return "<CollectionDatacubeExtension Item id={}>".format(self.collection.id)


class ItemDatacubeExtension(DatacubeExtension[pystac.Item]):
    """A concrete implementation of :class:`DatacubeExtension` on an
    :class:`~pystac.Item` that extends the properties of the Item to include properties
    defined in the :stac-ext:`Datacube Extension <datacube>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`DatacubeExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: pystac.Item
    properties: Dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return "<ItemDatacubeExtension Item id={}>".format(self.item.id)


class AssetDatacubeExtension(DatacubeExtension[pystac.Asset]):
    """A concrete implementation of :class:`DatacubeExtension` on an
    :class:`~pystac.Asset` that extends the Asset fields to include properties defined
    in the :stac-ext:`Datacube Extension <datacube>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`EOExtension.ext` on an :class:`~pystac.Asset` to extend it.
    """

    asset_href: str
    properties: Dict[str, Any]
    additional_read_properties: Optional[List[Dict[str, Any]]]

    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]
        else:
            self.additional_read_properties = None

    def __repr__(self) -> str:
        return "<AssetDatacubeExtension Item id={}>".format(self.asset_href)


class DatacubeExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"datacube"}
    stac_object_types = {
        pystac.STACObjectType.COLLECTION,
        pystac.STACObjectType.ITEM,
    }


DATACUBE_EXTENSION_HOOKS: ExtensionHooks = DatacubeExtensionHooks()
