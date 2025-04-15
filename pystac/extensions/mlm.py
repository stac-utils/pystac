"""Implements the :stac-ext:`Machine Learning Model (MLM) Extension <mlm>`.

This documentation does not provide a full-detail description of the meaning of each
parameter and how to use them. For an in-depth description of this extension, and the
use of each property, please refer to the official
:stac-ext:`documentation <mlm>`
"""

from __future__ import annotations

from abc import ABC
from collections.abc import Iterable
from typing import Any, Generic, Literal, TypeVar, cast

import pystac
from pystac.errors import STACError
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
)
from pystac.extensions.classification import Classification
from pystac.extensions.hooks import ExtensionHooks
from pystac.extensions.raster import DataType
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.utils import StringEnum, get_required

#: Generalized version of :class:`pystac.Item`, :class:`pystac.ItemAssetDefinition`,
#: :class:`pystac.Collection`, or :class:`pystac.Asset`
T = TypeVar(
    "T", pystac.Item, pystac.ItemAssetDefinition, pystac.Collection, pystac.Asset
)
AssetExtensionType = TypeVar("AssetExtensionType", bound="_AssetMLMExtension")

SCHEMA_URI_PATTERN: str = "https://stac-extensions.github.io/mlm/v{version}/schema.json"
DEFAULT_VERSION: str = "1.4.0"
SUPPORTED_VERSIONS: list[str] = ["1.0.0", "1.1.0", "1.2.0", "1.3.0", "1.4.0"]

PREFIX: str = "mlm:"

# Model Band Object properties
NAME_MODEL_BAND_OBJECT_PROP = "name"
FORMAT_MODEL_BAND_OBJECT_PROP = "format"
EXPRESSION_MODEL_BAND_OBJECT_PROP = "expression"

# Input Structure properties
SHAPE_INPUT_STRUCTURE_PROP = "shape"
DIM_ORDER_INPUT_STRUCTURE_PROP = "dim_order"
DATA_TYPE_INPUT_STRUCTURE_PROP = "data_type"

# Field names: Model Input Object
NAME_INPUT_OBJECT_PROP: str = "name"
BANDS_INPUT_OBJECT_PROP: str = "bands"
INPUT_INPUT_OBJECT_PROP: str = "input"
DESCRIPTION_INPUT_OBJECT_PROP: str = "description"
VALUE_SCALING_INPUT_OBJECT_PROP: str = "value_scaling"
RESIZE_TYPE_INPUT_OBJECT_PROP: str = "resize_type"
PRE_PROCESSING_FUNCTION_INPUT_OBJECT_PROP: str = "pre_processing_function"

# Output Structure properties
SHAPE_RESULT_STRUCTURE_PROP = "shape"
DIM_ORDER_RESULT_STRUCTURE_PROP = "dim_order"
DATA_TYPE_RESULT_STRUCTURE_PROP = "data_type"

# ProcessingExpression fields
FORMAT_PROCESSING_EXPRESSION_PROP = "format"
EXPRESSION_PROCESSING_EXPRESSION_PROP = "expression"

# ValueScaling fields
TYPE_VALUE_SCALING_PROP = "type"
MINIMUM_VALUE_SCALING_PROP = "minimum"
MAXIMUM_VALUE_SCALING_PROP = "maximum"
MEAN_VALUE_SCALING_PROP = "mean"
STDDEV_VALUE_SCALING_PROP = "stddev"
VALUE_VALUE_SCALING_PROP = "value"
FORMAT_VALUE_SCALING_PROP = "format"
EXPRESSION_VALUE_SCALING_PROP = "expression"

# Output properties
NAME_RESULT_PROP = "name"
TASKS_RESULT_PROP = "tasks"
RESULT_RESULT_PROP = "result"
DESCRIPTION_RESULT_PROP = "description"
CLASSES_RESULT_PROP = "classification:classes"
POST_PROCESSING_FUNCTION_RESULT_PROP = "post_processing_function"

# Field names
NAME_PROP: str = PREFIX + "name"
ARCHITECTURE_PROP: str = PREFIX + "architecture"
TASKS_PROP: str = PREFIX + "tasks"
FRAMEWORK_PROP: str = PREFIX + "framework"
FRAMEWORK_VERSION_PROP: str = PREFIX + "framework_version"
MEMORY_SIZE_PROP: str = PREFIX + "memory_size"
TOTAL_PARAMETERS_PROP: str = PREFIX + "total_parameters"
PRETRAINED_PROP: str = PREFIX + "pretrained"
PRETRAINED_SOURCE_PROP: str = PREFIX + "pretrained_source"
BATCH_SIZE_SUGGESTION_PROP: str = PREFIX + "batch_size_suggestion"
ACCELERATOR_PROP: str = PREFIX + "accelerator"
ACCELERATOR_CONSTRAINED_PROP: str = PREFIX + "accelerator_constrained"
ACCELERATOR_SUMMARY_PROP: str = PREFIX + "accelerator_summary"
ACCELERATOR_COUNT_PROP: str = PREFIX + "accelerator_count"
INPUT_PROP: str = PREFIX + "input"
OUTPUT_PROP: str = PREFIX + "output"
HYPERPARAMETERS_PROP: str = PREFIX + "hyperparameters"

ARTIFACT_TYPE_ASSET_PROP = PREFIX + "artifact_type"
COMPILE_METHOD_ASSET_PROP = PREFIX + "compile_method"
ENTRYPOINT_ASSET_PROP = PREFIX + "entrypoint"


class TaskType(StringEnum):
    """
    An enumeration of Tasks supported by the extension
    """

    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    SCENE_CLASSIFICATION = "scene-classification"
    DETECTION = "detection"
    OBJECT_DETECTION = "object-detection"
    SEGMENTATION = "segmentation"
    SEMANTIC_SEGMENTATION = "semantic-segmentation"
    INSTANCE_SEGMENTATION = "instance-segmentation"
    PANOPTIC_SEGMENTATION = "panoptic-segmentation"
    SIMILARITY_SEARCH = "similarity-search"
    GENERATIVE = "generative"
    IAMGE_CAPTIONING = "image-captioning"
    SUPER_RESOLUTION = "super-resolution"


class AcceleratorType(StringEnum):
    """
    An enumeration of accelerators supported by the extension
    """

    AMD64 = "amd64"
    CUDA = "cuda"
    XLA = "xla"
    AMD_ROCM = "amd-rocm"
    INTEL_IPEX_CPU = "intel-ipex-cpu"
    INTEL_IPEX_GPU = "intel-ipex-gpu"
    MACOS_ARM = "macos-arm"


class ResizeType(StringEnum):
    """
    An enumeration of Resize operations supported by the extension
    """

    CROP = "crop"
    PAD = "pad"
    INTERPOLATION_NEAREST = "interpolate-nearest"
    INTERPOLATION_LINEAR = "interpolate-linear"
    INTERPOLATION_CUBIC = "interpolation-cubic"
    INTERPOLATION_AREA = "interpolation-area"
    INTERPOLATION_LANCZOS4 = "interpolation-lanczos4"
    INTERPOLATION_MAX = "interpolation-max"
    WRAP_FILL_OUTLIERS = "wrap-fill-outliers"
    WRAP_INVERSE_MAP = "wrap-inverse-map"


class ValueScalingType(StringEnum):
    """
    An enumeratino of Value Scaling operations supported by the extension
    """

    MIN_MAX = "min-max"
    Z_SCORE = "z-score"
    CLIP = "clip"
    CLIP_MIN = "clip-min"
    CLIP_MAX = "clip-max"
    OFFSET = "offset"
    SCALE = "scale"
    PROCESSING = "processing"


class ModelBand:
    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]):
        self.properties = properties

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ModelBand):
            raise NotImplementedError
        return (
            self.name == other.name
            and self.format == other.format
            and self.expression == other.expression
        )

    def apply(
        self, name: str, format: str | None = None, expression: Any | None = None
    ) -> None:
        """
        Set the properties for a new ModelBand.

        Args:
            name: Name of the band referring to an extended band definition
            format: The type of expression that is specified in the expression property
            expression: An expression compliant with the format specified.
                The cxpression can be applied to any data type and depends on the format
                given
        """
        self.name = name
        self.format = format
        self.expression = expression

    @classmethod
    def create(
        cls, name: str, format: str | None = None, expression: Any | None = None
    ) -> ModelBand:
        """
        Create a new ModelBand.

        Args:
            name: Name of the band referring to an extended band definition
            format: The type of expression that is specified in the expression property
            expression: An expression compliant with the format specified.
                The expression can be applied to any data type and depends on the
                format given
        """
        c = cls({})
        c.apply(name=name, format=format, expression=expression)
        return c

    @property
    def name(self) -> str:
        """
        Get or set the required name property of a ModelBand object
        """
        return get_required(
            self.properties.get(NAME_MODEL_BAND_OBJECT_PROP),
            self,
            NAME_MODEL_BAND_OBJECT_PROP,
        )

    @name.setter
    def name(self, v: str) -> None:
        self.properties[NAME_MODEL_BAND_OBJECT_PROP] = v

    @property
    def format(self) -> str | None:
        """
        Get or set the optional format property of a ModelBand object
        """
        return self.properties.get(FORMAT_MODEL_BAND_OBJECT_PROP)

    @format.setter
    def format(self, v: str | None) -> None:
        if v is not None:
            self.properties[FORMAT_MODEL_BAND_OBJECT_PROP] = v
        else:
            self.properties.pop(FORMAT_MODEL_BAND_OBJECT_PROP, None)

    @property
    def expression(self) -> Any:
        """
        Get or set the optional expression property of a ModelBand object
        """
        return self.properties.get(EXPRESSION_MODEL_BAND_OBJECT_PROP)

    @expression.setter
    def expression(self, v: Any) -> None:
        if v is not None:
            self.properties[EXPRESSION_MODEL_BAND_OBJECT_PROP] = v
        else:
            self.properties.pop(EXPRESSION_MODEL_BAND_OBJECT_PROP, None)

    def to_dict(self) -> dict[str, Any]:
        """
        Returns the dictionary encoding of this ModelBand object

        Returns:
            dict[str, Any
        """
        return self.properties


class ProcessingExpression:
    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]):
        self.properties = properties

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ProcessingExpression):
            raise NotImplementedError
        else:
            return self.format == other.format and self.expression == other.expression

    def apply(self, format: str, expression: Any) -> None:
        """
        Set the properties for a new ProcessingExpression

        Args:
            format: The type of the expression that is specified in the expression
                property.
            expression: An expression compliant with the format specified. The
                expression can be any data type and depends on the format given,
                e.g. string or object.
        """
        self.format = format
        self.expression = expression

    @classmethod
    def create(cls, format: str, expression: Any) -> ProcessingExpression:
        """
        Creates a new ProcessingExpression

        Args:
            format: The type of the expression that is specified in the expression
                property.
            expression: An expression compliant with the format specified. The
                expression can be any data type and depends on the format given,
                e.g. string or object.
        Returns:
            ProcessingExpression
        """
        c = cls({})
        c.apply(format=format, expression=expression)
        return c

    @property
    def format(self) -> str:
        """
        Get or set the required format property of this ProcessingExpression
        """
        return get_required(
            self.properties.get(FORMAT_PROCESSING_EXPRESSION_PROP),
            self,
            FORMAT_PROCESSING_EXPRESSION_PROP,
        )

    @format.setter
    def format(self, v: str) -> None:
        self.properties[FORMAT_PROCESSING_EXPRESSION_PROP] = v

    @property
    def expression(self) -> Any:
        """
        Get or set the required expression property of this ProcessingExpression
        """
        return get_required(
            self.properties.get(EXPRESSION_PROCESSING_EXPRESSION_PROP),
            self,
            EXPRESSION_PROCESSING_EXPRESSION_PROP,
        )

    @expression.setter
    def expression(self, v: Any) -> None:
        self.properties[EXPRESSION_PROCESSING_EXPRESSION_PROP] = v

    def to_dict(self) -> dict[str, Any]:
        """
        Returns the dictionary encoding of this ProcessingExpression
        Returns:
            dict[str, Any]
        """
        return self.properties


class ValueScaling:
    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]):
        self.properties = properties

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ValueScaling):
            raise NotImplementedError
        return (
            self.type == other.type
            and self.minimum == other.minimum
            and self.maximum == other.maximum
            and self.mean == other.mean
            and self.stddev == other.stddev
            and self.value == other.value
            and self.format == other.format
            and self.expression == other.expression
        )

    def apply(
        self,
        type: ValueScalingType,
        minimum: int | float | None = None,
        maximum: int | float | None = None,
        mean: int | float | None = None,
        stddev: int | float | None = None,
        value: int | float | None = None,
        format: str | None = None,
        expression: str | None = None,
    ) -> None:
        """
        Creates new ValueScaling object. Depending on the type
        parameter, different parameters are required. Consult STAC:MLM documentation
        or use :meth:`~get_required_props` for details on what parameters are required
        for which ValueScaling ``type``.

        Args:
            type: The type of ValueScaling object.
            minimum: A minimum value
            maximum: A maximum value
            mean: A mean value
            stddev: A standard deviation value
            value: A scalar value
            format: The format of the expression
            expression: The expression itself
        """
        self.validate_property_dict(type, locals())

        self.type = type
        self.minimum = minimum
        self.maximum = maximum
        self.mean = mean
        self.stddev = stddev
        self.value = value
        self.format = format
        self.expression = expression

    @classmethod
    def create(
        cls,
        type: ValueScalingType,
        minimum: int | float | None = None,
        maximum: int | float | None = None,
        mean: int | float | None = None,
        stddev: int | float | None = None,
        value: int | float | None = None,
        format: str | None = None,
        expression: str | None = None,
    ) -> ValueScaling:
        """
        Creates new ValueScaling object. Depending on the type
        parameter, different parameters are required. Consult STAC:MLM documentation
        or use :meth:`~get_required_props` for details on what parameters are required
        for which ValueScaling ``type``.

        Args:
            type: The type of ValueScaling object.
            minimum: A minimum value
            maximum: A maximum value
            mean: A mean value
            stddev: A standard deviation value
            value: A scalar value
            format: The format of the expression
            expression: The expression itself

        Returns:
            ValueScaling
        """
        c = cls({})
        c.apply(
            type=type,
            minimum=minimum,
            maximum=maximum,
            mean=mean,
            stddev=stddev,
            value=value,
            format=format,
            expression=expression,
        )
        return c

    @classmethod
    def get_required_props(cls, type: ValueScalingType) -> list[str]:
        """
        Determines the parameters required for a certain ValueScaling operation.

        Args:
            type: The type of ValueScaling operation for which required properties are
                to be retrieved

        Returns:
            list[str]: names of properties required for the given ``type``
        """
        d: dict[str, list[str]] = {
            "min-max": ["minimum", "maximum"],
            "z-score": ["mean", "stddev"],
            "clip": ["minimum", "maximum"],
            "clip-min": ["minimum"],
            "clip-max": ["maximum"],
            "offset": ["value"],
            "scale": ["value"],
            "processing": ["format", "expression"],
        }
        return d[type]

    @classmethod
    def validate_property_dict(
        cls, type: ValueScalingType, props: dict[str, Any]
    ) -> None:
        """
        Validate whether given properties satisfy the requirements set by the
            ValueScaling ``type`` parameter

        Args:
            type: The type of ValueScaling operation
            props: The properties to validate. Keys in this dict are the property
                names, values are the property values

        Raises:
            :class:``STACError``: if the given properties do not satisfy
                the requirements of the ValueScaling ``type``

        """
        required_props = cls.get_required_props(type)
        given_props = [
            prop_name
            for prop_name, prop_value in props.items()
            if prop_value is not None
        ]
        given_props_cleaned = [
            prop for prop in given_props if prop != "self" and prop != "type"
        ]

        valid = all(
            [required_prop in given_props_cleaned for required_prop in required_props]
        )

        if not valid:
            raise STACError(
                f"ValueScaling object of {type=} "
                f"requires properties: {required_props}. Given: {given_props_cleaned}"
            )

    @property
    def type(self) -> str:
        """
        Get or set the required type property of this ValueScaling object
        """
        return get_required(
            self.properties.get(TYPE_VALUE_SCALING_PROP), self, TYPE_VALUE_SCALING_PROP
        )

    @type.setter
    def type(self, v: str) -> None:
        self.properties[TYPE_VALUE_SCALING_PROP] = v

    @property
    def minimum(self) -> int | float | None:
        """
        Get or set the minimum property of this ValueScaling object
        """
        return self.properties.get(MINIMUM_VALUE_SCALING_PROP)

    @minimum.setter
    def minimum(self, v: int | float | None) -> None:
        if v is not None:
            self.properties[MINIMUM_VALUE_SCALING_PROP] = v
        else:
            self.properties.pop(MINIMUM_VALUE_SCALING_PROP, None)

    @property
    def maximum(self) -> int | float | None:
        """
        Get or set the maximum property of this ValueScaling object
        """
        return self.properties.get(MAXIMUM_VALUE_SCALING_PROP)

    @maximum.setter
    def maximum(self, v: int | float | None) -> None:
        if v is not None:
            self.properties[MAXIMUM_VALUE_SCALING_PROP] = v
        else:
            self.properties.get(MAXIMUM_VALUE_SCALING_PROP, None)

    @property
    def mean(self) -> int | float | None:
        """
        Get or set the mean property of this ValueScaling object
        """
        return self.properties.get(MEAN_VALUE_SCALING_PROP)

    @mean.setter
    def mean(self, v: int | float | None) -> None:
        if v is not None:
            self.properties[MEAN_VALUE_SCALING_PROP] = v
        else:
            self.properties.pop(MEAN_VALUE_SCALING_PROP, None)

    @property
    def stddev(self) -> int | float | None:
        """
        Get or set the stddev (standard deviation) property of this ValueScaling object
        """
        return self.properties.get(STDDEV_VALUE_SCALING_PROP)

    @stddev.setter
    def stddev(self, v: int | float | None) -> None:
        if v is not None:
            self.properties[STDDEV_VALUE_SCALING_PROP] = v
        else:
            self.properties.pop(STDDEV_VALUE_SCALING_PROP, None)

    @property
    def value(self) -> int | float | None:
        """
        Get or set the value property of this ValueScaling object
        """
        return self.properties.get(VALUE_VALUE_SCALING_PROP)

    @value.setter
    def value(self, v: int | float | None) -> None:
        if v is not None:
            self.properties[VALUE_VALUE_SCALING_PROP] = v
        else:
            self.properties.pop(VALUE_VALUE_SCALING_PROP, None)

    @property
    def format(self) -> str | None:
        """
        Get or set the format property of this ValueScaling object
        """
        return self.properties.get(FORMAT_VALUE_SCALING_PROP)

    @format.setter
    def format(self, v: str | None) -> None:
        if v is not None:
            self.properties[FORMAT_VALUE_SCALING_PROP] = v
        else:
            self.properties.pop(FORMAT_VALUE_SCALING_PROP, None)

    @property
    def expression(self) -> str | None:
        """
        Get or set the expression property of this ValueScaling object
        """
        return self.properties.get(EXPRESSION_VALUE_SCALING_PROP)

    @expression.setter
    def expression(self, v: str | None) -> None:
        if v is not None:
            self.properties[EXPRESSION_VALUE_SCALING_PROP] = v
        else:
            self.properties.pop(EXPRESSION_VALUE_SCALING_PROP, None)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize a dict representation of this ValueScaling object

        Returns:
            dict[str, Any]
        """
        return self.properties


class InputStructure:
    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]):
        self.properties = properties

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, InputStructure):
            raise NotImplementedError
        return (
            self.shape == other.shape
            and self.dim_order == other.dim_order
            and self.data_type == other.data_type
        )

    def apply(
        self,
        shape: list[int],
        dim_order: list[str],
        data_type: DataType,
    ) -> None:
        """
        Set the properties for a new InputStructure.

        Args:
            shape: Shape of the input n-dimensional array (e.g.: B×C×H×W), including
                the batch size dimension.
                Each dimension must either be greater than 0 or -1 to indicate a
                variable dimension size.
            dim_order: Order of the shape dimensions by name.
            data_type:The data type of values in the n-dimensional array. For model
                inputs, this should be the data type of the processed input supplied to
                the model inference function, not the data type of the source bands.
        """
        self.shape = shape
        self.dim_order = dim_order
        self.data_type = data_type

    @classmethod
    def create(
        cls, shape: list[int], dim_order: list[str], data_type: DataType
    ) -> InputStructure:
        """
        Create a new InputStructure.

        Args:
            shape: Shape of the input n-dimensional array (e.g.: B×C×H×W), including the
                batch size dimension. Each dimension must either be greater than 0 or
                -1 to indicate a variable dimension size.
            dim_order: Order of the shape dimensions by name.
            dim_order: Order of the shape dimensions by name.
            data_type: The data type of values in the n-dimensional array. For model
                inputs, this should be the data type of the processed input supplied to
                the model inference function, not the data type of the source bands.
        Returns:
            InputStructure
        """
        c = cls({})
        c.apply(shape=shape, dim_order=dim_order, data_type=data_type)
        return c

    @property
    def shape(self) -> list[int]:
        """
        Get or set the required shape property of this InputStructure object
        """
        return get_required(
            self.properties.get(SHAPE_INPUT_STRUCTURE_PROP),
            self,
            SHAPE_INPUT_STRUCTURE_PROP,
        )

    @shape.setter
    def shape(self, v: list[int]) -> None:
        self.properties[SHAPE_INPUT_STRUCTURE_PROP] = v

    @property
    def dim_order(self) -> list[str]:
        """
        Get or set the required dim_order property of this InputStructure object
        """
        return get_required(
            self.properties.get(DIM_ORDER_INPUT_STRUCTURE_PROP),
            self,
            DIM_ORDER_INPUT_STRUCTURE_PROP,
        )

    @dim_order.setter
    def dim_order(self, v: list[str]) -> None:
        self.properties[DIM_ORDER_INPUT_STRUCTURE_PROP] = v

    @property
    def data_type(self) -> DataType:
        """
        Get or set the required data_type property of this InputStructure object
        """
        return get_required(
            self.properties.get(DATA_TYPE_INPUT_STRUCTURE_PROP),
            self,
            DATA_TYPE_INPUT_STRUCTURE_PROP,
        )

    @data_type.setter
    def data_type(self, v: DataType) -> None:
        self.properties[DATA_TYPE_INPUT_STRUCTURE_PROP] = v

    def to_dict(self) -> dict[str, Any]:
        """
        Serializes a dict representation of this InputStucture object

        Returns:
            dict[str, Any]
        """
        return self.properties


class ModelInput:
    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]):
        self.properties = properties

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ModelInput):
            raise NotImplementedError
        return (
            self.name == other.name
            and self.bands == other.bands
            and self.input == other.input
            and self.description == other.description
            and self.value_scaling == other.value_scaling
            and self.resize_type == other.resize_type
            and self.pre_processing_function == other.pre_processing_function
        )

    def apply(
        self,
        name: str,
        bands: list[ModelBand] | list[str],
        input: InputStructure,
        description: str | None = None,
        value_scaling: ValueScaling | None = None,
        resize_type: ResizeType | None = None,
        pre_processing_function: ProcessingExpression | None = None,
    ) -> None:
        """
        Sets the Properties for a new Input

        Args:
            name: Name of the input variable defined by the model. If no explicit name
                is defined by the model, an informative name (e.g.: "RGB Time Series")
                can be used instead.
            bands: The raster band references used to train, fine-tune or perform
                inference with the model, which may be all or a subset of bands
                available in a STAC Item's Band Object. If no band applies for one
                input, use an empty array.
            input: The N-dimensional array definition that describes the shape,
                dimension ordering, and data type.
            description: Additional details about the input such as describing its
                purpose or expected source that cannot be represented by other
                properties.
            value_scaling:Method to scale, normalize, or standardize the data inputs
                values, across dimensions, per corresponding dimension index, or null
                if none applies. These values often correspond to dataset or sensor
                statistics employed for training the model, but can come from another
                source as needed by the model definition. Consider using
                pre_processing_function for custom implementations or more complex
                combinations.
            resize_type: High-level descriptor of the resize method to modify the input
                dimensions shape. Select an appropriate option or null when none
                applies. Consider using pre_processing_function for custom
                implementations or more complex combinations.
            pre_processing_function: Custom preprocessing function where rescaling and
                resize, and any other significant data preparation operations takes
                place. The pre_processing_function should be applied over all available
                bands.
        """
        self.name = name
        self.bands = bands
        self.input = input
        self.description = description
        self.value_scaling = value_scaling
        self.resize_type = resize_type
        self.pre_processing_function = pre_processing_function

    @classmethod
    def create(
        cls,
        name: str,
        bands: list[ModelBand] | list[str],
        input: InputStructure,
        description: str | None = None,
        value_scaling: ValueScaling | None = None,
        resize_type: ResizeType | None = None,
        pre_processing_function: ProcessingExpression | None = None,
    ) -> ModelInput:
        """
        Creates a new Input

        Args:
            name: Name of the input variable defined by the model. If no explicit name
                is defined by the model, an informative name (e.g.: "RGB Time Series")
                can be used instead.
            bands: The raster band references used to train, fine-tune or perform
                inference with the model, which may be all or a subset of bands
                available in a STAC Item's Band Object. If no band applies for one
                input, use an empty array.
            input: The N-dimensional array definition that describes the shape,
                dimension ordering, and data type.
            description: Additional details about the input such as describing its
                purpose or expected source that cannot be represented by other
                properties.
            value_scaling:Method to scale, normalize, or standardize the data inputs
                values, across dimensions, per corresponding dimension index, or null
                if none applies. These values often correspond to dataset or sensor
                statistics employed for training the model, but can come from another
                source as needed by the model definition. Consider using
                pre_processing_function for custom implementations or more complex
                combinations.
            resize_type: High-level descriptor of the resize method to modify the input
                dimensions shape. Select an appropriate option or null when none
                applies. Consider using pre_processing_function for custom
                implementations or more complex combinations.
            pre_processing_function: Custom preprocessing function where rescaling and
                resize, and any other significant data preparation operations takes
                place. The pre_processing_function should be applied over all available
                bands.
        """
        c = cls({})
        c.apply(
            name=name,
            bands=bands,
            input=input,
            description=description,
            value_scaling=value_scaling,
            resize_type=resize_type,
            pre_processing_function=pre_processing_function,
        )
        return c

    @property
    def name(self) -> str:
        """
        Gets or sets the required name property of this ModelInput object
        """
        return get_required(
            self.properties.get(NAME_INPUT_OBJECT_PROP), self, NAME_INPUT_OBJECT_PROP
        )

    @name.setter
    def name(self, v: str) -> None:
        self.properties[NAME_INPUT_OBJECT_PROP] = v

    @property
    def bands(self) -> list[ModelBand] | list[str]:
        """
        Gets or sets the required bands property of this ModelInput object
        """
        bands: list[str] | list[dict[str, Any]] = get_required(
            self.properties.get(BANDS_INPUT_OBJECT_PROP), self, BANDS_INPUT_OBJECT_PROP
        )

        if isinstance(bands, list) and all(isinstance(item, str) for item in bands):
            return [band for band in bands if isinstance(band, str)]

        elif isinstance(bands, list) and all(isinstance(item, dict) for item in bands):
            return [ModelBand(band) for band in bands if isinstance(band, dict)]

        raise TypeError("Invalid bands property. Must list[str] or list[ModelBand]")

    @bands.setter
    def bands(self, v: list[ModelBand] | list[str]) -> None:
        v_trans = [c.to_dict() if isinstance(c, ModelBand) else c for c in v]
        self.properties[BANDS_INPUT_OBJECT_PROP] = v_trans

    @property
    def input(self) -> InputStructure:
        """
        Gets or sets the required input property of this ModelInput object
        """
        return InputStructure(
            get_required(
                self.properties.get(INPUT_INPUT_OBJECT_PROP),
                self,
                INPUT_INPUT_OBJECT_PROP,
            )
        )

    @input.setter
    def input(self, v: InputStructure) -> None:
        self.properties[INPUT_INPUT_OBJECT_PROP] = v.to_dict()

    @property
    def description(self) -> str | None:
        """
        Gets or sets the description property of this ModelInput object
        """
        return self.properties.get(DESCRIPTION_INPUT_OBJECT_PROP)

    @description.setter
    def description(self, v: str | None) -> None:
        if v is not None:
            self.properties[DESCRIPTION_INPUT_OBJECT_PROP] = v
        else:
            self.properties.pop(DESCRIPTION_INPUT_OBJECT_PROP, None)

    @property
    def value_scaling(self) -> ValueScaling | None:
        """
        Gets or sets the value_scaling property of this ModelInput object
        """
        v = self.properties.get(VALUE_SCALING_INPUT_OBJECT_PROP)
        return ValueScaling(v) if v is not None else v

    @value_scaling.setter
    def value_scaling(self, v: ValueScaling | None) -> None:
        # add None to properties dict and do not pop it, according to specification
        self.properties[VALUE_SCALING_INPUT_OBJECT_PROP] = (
            None if v is None else v.to_dict()
        )

    @property
    def resize_type(self) -> ResizeType | None:
        """
        Gets or sets the resize_type property of this ModelInput object
        """
        return self.properties.get(RESIZE_TYPE_INPUT_OBJECT_PROP)

    @resize_type.setter
    def resize_type(self, v: ResizeType | None) -> None:
        # add to dict even if v is None and do not pop it, according to specification
        self.properties[RESIZE_TYPE_INPUT_OBJECT_PROP] = v

    @property
    def pre_processing_function(self) -> ProcessingExpression | None:
        """
        Gets or sets the pre_processing_function property of this ModelInput object
        """
        v = self.properties.get(PRE_PROCESSING_FUNCTION_INPUT_OBJECT_PROP)
        return ProcessingExpression(v) if v is not None else None

    @pre_processing_function.setter
    def pre_processing_function(self, v: ProcessingExpression | None) -> None:
        # add to dict even if v is None and do not pop it, according to specification
        self.properties[PRE_PROCESSING_FUNCTION_INPUT_OBJECT_PROP] = (
            None if v is None else v.to_dict()
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Serializes this ModelInput object into its dict representation

        Returns:
            dict[str, Any]
        """
        return self.properties


class ResultStructure:
    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]):
        self.properties = properties

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ResultStructure):
            raise NotImplementedError
        return (
            self.shape == other.shape
            and self.dim_order == other.dim_order
            and self.data_type == other.data_type
        )

    def apply(
        self, shape: list[int], dim_order: list[str], data_type: DataType
    ) -> None:
        """
        Set the properties for a new ResultStructure.

        Args:
            shape: Shape of the n-dimensional result array (e.g.: B×H×W or B×C),
                possibly including a batch size dimension. The dimensions must either
                be greater than 0 or -1 to indicate a variable size.
            dim_order: Order of the shape dimensions by name for the result array.
            data_type: The data type of values in the n-dimensional array. For model
                outputs, this should be the data type of the result of the model
                inference without extra post processing.
        """
        self.shape = shape
        self.dim_order = dim_order
        self.data_type = data_type

    @classmethod
    def create(
        cls, shape: list[int], dim_order: list[str], data_type: DataType
    ) -> ResultStructure:
        """
        Creates a new ResultStructure.

        Args:
            shape: Shape of the n-dimensional result array (e.g.: B×H×W or B×C),
                possibly including a batch size dimension. The dimensions must either
                be greater than 0 or -1 to indicate a variable size.
            dim_order: Order of the shape dimensions by name for the result array.
            data_type: The data type of values in the n-dimensional array. For model
                outputs, this should be the data type of the result of the model
                inference without extra post processing.

        Returns:
            ResultStructure
        """
        c = cls({})
        c.apply(shape=shape, dim_order=dim_order, data_type=data_type)
        return c

    @property
    def shape(self) -> list[int]:
        """
        Gets or sets the required shape property of the ResultStructure object
        """
        return get_required(
            self.properties.get(SHAPE_RESULT_STRUCTURE_PROP),
            self,
            SHAPE_RESULT_STRUCTURE_PROP,
        )

    @shape.setter
    def shape(self, v: list[int]) -> None:
        self.properties[SHAPE_RESULT_STRUCTURE_PROP] = v

    @property
    def dim_order(self) -> list[str]:
        """
        Gets or sets the required dim_order property of the ResultStructure object
        """
        return get_required(
            self.properties.get(DIM_ORDER_RESULT_STRUCTURE_PROP),
            self,
            DIM_ORDER_RESULT_STRUCTURE_PROP,
        )

    @dim_order.setter
    def dim_order(self, v: list[str]) -> None:
        self.properties[DIM_ORDER_RESULT_STRUCTURE_PROP] = v

    @property
    def data_type(self) -> DataType:
        """
        Gets or sets the required data_type property of the ResultStructure object
        """
        return get_required(
            self.properties.get(DATA_TYPE_RESULT_STRUCTURE_PROP),
            self,
            DIM_ORDER_RESULT_STRUCTURE_PROP,
        )

    @data_type.setter
    def data_type(self, v: DataType) -> None:
        self.properties[DATA_TYPE_RESULT_STRUCTURE_PROP] = v

    def to_dict(self) -> dict[str, Any]:
        """
        Serilaizes this ResultStructure object to a dict
        Returns:
            dict[str, Any]
        """
        return self.properties


class ModelOutput:
    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]):
        self.properties = properties

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ModelOutput):
            raise NotImplementedError
        return (
            self.name == other.name
            and self.tasks == other.tasks
            and self.result == other.result
            and self.description == other.description
            and self.classes == other.classes
            and self.post_processing_function == other.post_processing_function
        )

    def apply(
        self,
        name: str,
        tasks: list[TaskType],
        result: ResultStructure,
        description: str | None = None,
        classes: list[Classification] | None = None,
        post_processing_function: ProcessingExpression | None = None,
    ) -> None:
        """
        Sets the properties for a new Output

        Args:
            name:Name of the output variable defined by the model. If no explicit name
                is defined by the model, an informative name (e.g.: "CLASSIFICATION")
                can be used instead.
            tasks: Specifies the Machine Learning tasks for which the output can be used
                for. This can be a subset of mlm:tasks defined under the Item properties
                as applicable.
            result: The structure that describes the resulting output arrays/tensors
                from one model head.
            description: Additional details about the output such as describing its
                purpose or expected result that cannot be represented by other
                properties.
            classes: A list of class objects adhering to the Classification Extension.
            post_processing_function: Custom postprocessing function where
                normalization, rescaling, or any other
                significant operations takes place.
        """
        self.name = name
        self.tasks = tasks
        self.result = result
        self.description = description
        self.classes = classes
        self.post_processing_function = post_processing_function

    @classmethod
    def create(
        cls,
        name: str,
        tasks: list[TaskType],
        result: ResultStructure,
        description: str | None = None,
        classes: list[Classification] | None = None,
        post_processing_function: ProcessingExpression | None = None,
    ) -> ModelOutput:
        """
        Creates a new Output

        Args:
            name:Name of the output variable defined by the model. If no explicit name
                is defined by the model, an informative name (e.g.: "CLASSIFICATION")
                can be used instead.
            tasks: Specifies the Machine Learning tasks for which the output can be used
                for. This can be a subset of mlm:tasks defined under the Item properties
                as applicable.
            result: The structure that describes the resulting output arrays/tensors
                from one model head. description: Additional details about the output
                such as describing its purpose or expected result that cannot be
                represented by other properties.
            classes: A list of class objects adhering to the Classification Extension.
            post_processing_function: Custom postprocessing function where
                normalization, rescaling, or any other significant operations takes
                place.

        Returns:
            ModelOutput
        """
        c = cls({})
        c.apply(
            name=name,
            tasks=tasks,
            result=result,
            description=description,
            classes=classes,
            post_processing_function=post_processing_function,
        )
        return c

    @property
    def name(self) -> str:
        """
        Gets or sets the required name property of this ModelOutput object
        """
        return get_required(
            self.properties.get(NAME_RESULT_PROP), self, NAME_RESULT_PROP
        )

    @name.setter
    def name(self, v: str) -> None:
        self.properties[NAME_RESULT_PROP] = v

    @property
    def tasks(self) -> list[TaskType]:
        """
        Gets or sets the required tasks property of this ModelOutput object
        """
        return get_required(
            self.properties.get(TASKS_RESULT_PROP), self, TASKS_RESULT_PROP
        )

    @tasks.setter
    def tasks(self, v: list[TaskType]) -> None:
        self.properties[TASKS_RESULT_PROP] = v

    @property
    def result(self) -> ResultStructure:
        """
        Gets or sets the required results property of this ModelOutput object
        """
        return ResultStructure(
            get_required(
                self.properties.get(RESULT_RESULT_PROP), self, RESULT_RESULT_PROP
            )
        )

    @result.setter
    def result(self, v: ResultStructure) -> None:
        self.properties[RESULT_RESULT_PROP] = v.to_dict()

    @property
    def description(self) -> str | None:
        """
        Gets or sets the description property of this ModelOutput object
        """
        return self.properties.get(DESCRIPTION_RESULT_PROP)

    @description.setter
    def description(self, v: str | None) -> None:
        if v is not None:
            self.properties[DESCRIPTION_RESULT_PROP] = v
        else:
            self.properties.pop(DESCRIPTION_RESULT_PROP, None)

    @property
    def classes(self) -> list[Classification] | None:
        """
        Gets or sets the classes property of this ModelOutput object
        """
        classes = self.properties.get(CLASSES_RESULT_PROP)
        return [Classification(c) for c in classes] if classes is not None else None

    @classes.setter
    def classes(self, v: list[Classification] | None) -> None:
        if v is not None:
            self.properties[CLASSES_RESULT_PROP] = [c.to_dict() for c in v]
        else:
            self.properties.pop(CLASSES_RESULT_PROP, None)

    @property
    def post_processing_function(self) -> ProcessingExpression | None:
        """
        Gets or sets the post_processing_function property of this ModelOutput object
        """
        v = self.properties.get(POST_PROCESSING_FUNCTION_RESULT_PROP)
        return ProcessingExpression(v) if v is not None else None

    @post_processing_function.setter
    def post_processing_function(self, v: ProcessingExpression | None) -> None:
        if v is not None:
            self.properties[POST_PROCESSING_FUNCTION_RESULT_PROP] = v.to_dict()
        else:
            self.properties.pop(POST_PROCESSING_FUNCTION_RESULT_PROP, None)

    def to_dict(self) -> dict[str, Any]:
        """
        Serializes this ModelOutput object into a dict
        Returns:
            dict[str, Any]
        """
        return self.properties


class Hyperparameters:
    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]):
        self.properties = properties

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Hyperparameters):
            raise NotImplementedError
        return self.properties == other.properties

    def apply(self, **kwargs: Any) -> None:
        """
        Sets the properties for a new Hyperparameters object. The stac:mlm specification
        defines neither their names nor their values, so any key-value pair is allowed.
        Args:
            **kwargs: any model hyperparameter name and its value, as key-value paris
        """
        self.properties.update(kwargs)

    @classmethod
    def create(cls, **kwargs: Any) -> Hyperparameters:
        c = cls({})
        c.apply(**kwargs)
        return c

    def to_dict(self) -> dict[str, Any]:
        """
        Serializes this Hyperparameters object into a dictionary
        Returns:
            dict[str, Any]
        """
        return self.properties


class MLMExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """An abstract class that can be used to extend to properties of an
    :class:`pystac.Item` or :class:`pystac.Collection` with properties from the
    :stac-ext:`Machine Learning Model Extension <mlm>`.

    This class can be used to extend :class:`pystac.Item`, :class:`pystac.Collection`
    and :class:`pystac.ItemAssetDefinition`. For extending :class:`pystac.Asset`, use
    either :class:`~AssetGeneralMLMExtension`: or :class:`AssetDetailedMLMExtension`.
    """

    name: Literal["mlm"] = "mlm"
    properties: dict[str, Any]

    def apply(
        self,
        name: str,
        architecture: str,
        tasks: list[TaskType],
        input: list[ModelInput],
        output: list[ModelOutput],
        framework: str | None = None,
        framework_version: str | None = None,
        memory_size: int | None = None,
        total_parameters: int | None = None,
        pretrained: bool | None = None,
        pretrained_source: str | None = None,
        batch_size_suggestion: int | None = None,
        accelerator: AcceleratorType | None = None,
        accelerator_constrained: bool | None = None,
        accelerator_summary: str | None = None,
        accelerator_count: int | None = None,
        hyperparameters: Hyperparameters | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Sets the properties of a new MLMExtension

        Args:
            name:  name for the model
            architecture: A generic and well established architecture name of the model
            tasks: Specifies the Machine Learning tasks for which the model can be
                used for
            input: Describes the transformation between the EO data and the model input
            output: Describes each model output and how to interpret it.
            framework: Framework used to train the model
            framework_version: The ``framework`` library version
            memory_size: The in-memory size of the model on the accelerator during
                inference (bytes)
            total_parameters: Total number of model parameters, including trainable and
                non-trainable parameters.
            pretrained: Indicates if the model was pretrained. If the model was
                pretrained, consider providing ``pretrained_source`` if it is known
            pretrained_source: The source of the pretraining.
            batch_size_suggestion: A suggested batch size for the accelerator and
                summarized hardware.
            accelerator: The intended computational hardware that runs inference
            accelerator_constrained: Indicates if the intended ``accelerator`` is the
                only accelerator that can run inference
            accelerator_summary: A high level description of the ``accelerator``
            accelerator_count: A minimum amount of ``accelerator`` instances required to
                run the model
            hyperparameters: Additional hyperparameters relevant for the model
            *args: Unused (no effect, only here for signature compliance with apply
                method in derived classes
            **kwargs: Unused (no effect, only here for signature compliance with apply
                method in derived classes
        """
        self.mlm_name = name
        self.architecture = architecture
        self.tasks = tasks
        self.input = input
        self.output = output
        self.framework = framework
        self.framework_version = framework_version
        self.memory_size = memory_size
        self.total_parameters = total_parameters
        self.pretrained = pretrained
        self.pretrained_source = pretrained_source
        self.batch_size_suggestion = batch_size_suggestion
        self.accelerator = accelerator
        self.accelerator_constrained = accelerator_constrained
        self.accelerator_summary = accelerator_summary
        self.accelerator_count = accelerator_count
        self.hyperparameters = hyperparameters

    @classmethod
    def get_schema_uri(cls) -> str:
        """
        Retrieves this extension's schema URI

        Returns:
            str: the schema URI
        """
        return SCHEMA_URI_PATTERN.format(version=DEFAULT_VERSION)

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> MLMExtension[T]:
        """
        Extend a STAC object (``obj``) with the MLMExtension

        Args:
            obj: The STAC object to be extended.
            add_if_missing: Defines whether this extension's URI should be added to
                this object's  (or its parent's) list of extensions if it is not already
                listed there.

        Returns:
            MLMExtension[T]: The extended object

        Raises:
            TypeError: When a :class:`pystac.Asset` object is passed as the
                `obj` parameter
            pystac.ExtensionTypeError: When any unsupported object is passed as the
                `obj` parameter. If you see this extension in this context, please
                raise an issue on github.
        """
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(MLMExtension[T], ItemMLMExtension(obj))
        elif isinstance(obj, pystac.Collection):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(MLMExtension[T], CollectionMLMExtension(obj))
        elif isinstance(obj, pystac.ItemAssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(MLMExtension[T], ItemAssetMLMExtension(obj))
        elif isinstance(obj, pystac.Asset):
            raise TypeError(
                "This class cannot be used to extend STAC objects of type Assets. "
                "To extend Asset objects, use either AssetGeneralMLMExtension or "
                "AssetDetailedMLMExtension"
            )
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @property
    def mlm_name(self) -> str:
        """
        Get or set the required (mlm) name property. It is named mlm_name in this
        context to not break convention and overwrite the extension name class property.
        """
        return get_required(self.properties.get(NAME_PROP), self, NAME_PROP)

    @mlm_name.setter
    def mlm_name(self, v: str) -> None:
        self._set_property(NAME_PROP, v)

    @property
    def architecture(self) -> str:
        """
        Get or set the required architecture property
        """
        return get_required(
            self.properties.get(ARCHITECTURE_PROP), self, ARCHITECTURE_PROP
        )

    @architecture.setter
    def architecture(self, v: str) -> None:
        self._set_property(ARCHITECTURE_PROP, v)

    @property
    def tasks(self) -> list[TaskType]:
        """
        Get or set the required tasks property
        """
        return get_required(self.properties.get(TASKS_PROP), self, TASKS_PROP)

    @tasks.setter
    def tasks(self, v: list[TaskType]) -> None:
        self._set_property(TASKS_PROP, v)

    @property
    def framework(self) -> str | None:
        """
        Get or set the framework property
        """
        return self._get_property(FRAMEWORK_PROP, str)

    @framework.setter
    def framework(self, v: str | None) -> None:
        self._set_property(FRAMEWORK_PROP, v)

    @property
    def framework_version(self) -> str | None:
        """
        Get or set the framework_version property
        """
        return self._get_property(FRAMEWORK_VERSION_PROP, str)

    @framework_version.setter
    def framework_version(self, v: str | None) -> None:
        self._set_property(FRAMEWORK_VERSION_PROP, v)

    @property
    def memory_size(self) -> int | None:
        """
        Get or set the memory_size property
        """
        return self._get_property(MEMORY_SIZE_PROP, int)

    @memory_size.setter
    def memory_size(self, v: int | None) -> None:
        self._set_property(MEMORY_SIZE_PROP, v)

    @property
    def total_parameters(self) -> int | None:
        """
        Get or set the total_parameters property
        """
        return self._get_property(TOTAL_PARAMETERS_PROP, int)

    @total_parameters.setter
    def total_parameters(self, v: int | None) -> None:
        self._set_property(TOTAL_PARAMETERS_PROP, v)

    @property
    def pretrained(self) -> bool | None:
        """
        Get or set the pretrained property
        """
        return self._get_property(PRETRAINED_PROP, bool)

    @pretrained.setter
    def pretrained(self, v: bool | None) -> None:
        self._set_property(PRETRAINED_PROP, v)

    @property
    def pretrained_source(self) -> str | None:
        """
        Get or set the pretrained_source property
        """
        return self._get_property(PRETRAINED_SOURCE_PROP, str)

    @pretrained_source.setter
    def pretrained_source(self, v: str | None) -> None:
        self._set_property(
            PRETRAINED_SOURCE_PROP, v, False
        )  # dont pop as per documentation

    @property
    def batch_size_suggestion(self) -> int | None:
        """
        Get or set the batch_size_suggestion property
        """
        return self._get_property(BATCH_SIZE_SUGGESTION_PROP, int)

    @batch_size_suggestion.setter
    def batch_size_suggestion(self, v: int | None) -> None:
        self._set_property(BATCH_SIZE_SUGGESTION_PROP, v)

    @property
    def accelerator(self) -> AcceleratorType | None:
        """
        Get or set the accelerator property
        """
        return self._get_property(ACCELERATOR_PROP, AcceleratorType)

    @accelerator.setter
    def accelerator(self, v: AcceleratorType | None) -> None:
        # dont pop as per documentation
        self._set_property(ACCELERATOR_PROP, v, False)

    @property
    def accelerator_constrained(self) -> bool | None:
        """
        Get or set the accelerator_constrained property
        """
        return self._get_property(ACCELERATOR_CONSTRAINED_PROP, bool)

    @accelerator_constrained.setter
    def accelerator_constrained(self, v: bool | None) -> None:
        self._set_property(ACCELERATOR_CONSTRAINED_PROP, v)

    @property
    def accelerator_summary(self) -> str | None:
        """
        Get or set the accelerator_summary property
        """
        return self._get_property(ACCELERATOR_SUMMARY_PROP, str)

    @accelerator_summary.setter
    def accelerator_summary(self, v: str | None) -> None:
        self._set_property(ACCELERATOR_SUMMARY_PROP, v)

    @property
    def accelerator_count(self) -> int | None:
        """
        Get or set the accelerator_count property
        """
        return self._get_property(ACCELERATOR_COUNT_PROP, int)

    @accelerator_count.setter
    def accelerator_count(self, v: int | None) -> None:
        self._set_property(ACCELERATOR_COUNT_PROP, v)

    @property
    def input(self) -> list[ModelInput]:
        """
        Get or set the required input property
        """
        return [
            ModelInput(inp)
            for inp in get_required(
                self._get_property(INPUT_PROP, list[dict[str, Any]]), self, INPUT_PROP
            )
        ]

    @input.setter
    def input(self, v: list[ModelInput]) -> None:
        self._set_property(INPUT_PROP, [inp.to_dict() for inp in v])

    @property
    def output(self) -> list[ModelOutput]:
        """
        Get or set the required output property
        """
        return [
            ModelOutput(outp)
            for outp in get_required(
                self._get_property(OUTPUT_PROP, list[dict[str, Any]]), self, OUTPUT_PROP
            )
        ]

    @output.setter
    def output(self, v: list[ModelOutput]) -> None:
        self._set_property(OUTPUT_PROP, [outp.to_dict() for outp in v])

    @property
    def hyperparameters(self) -> Hyperparameters | None:
        """
        Get or set the hyperparameters property
        """
        prop = self._get_property(HYPERPARAMETERS_PROP, dict[str, Any])
        return Hyperparameters(prop) if prop is not None else None

    @hyperparameters.setter
    def hyperparameters(self, v: Hyperparameters | None) -> None:
        self._set_property(HYPERPARAMETERS_PROP, v.to_dict() if v is not None else None)

    def to_dict(self) -> dict[str, Any]:
        """
        Serializes this MLMExtension object into a dict

        Returns:
            dict[str, Any]
        """
        return self.properties


class ItemMLMExtension(MLMExtension[pystac.Item]):
    properties: dict[str, Any]
    item: pystac.Item

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemMLMExtension Item id={self.item.id}>"


class CollectionMLMExtension(MLMExtension[pystac.Collection]):
    collection: pystac.Collection
    properties: dict[str, Any]
    links: list[pystac.Link]

    def __init__(self, collection: pystac.Collection):
        self.collection = collection
        self.properties = collection.extra_fields
        self.links = collection.links

    def __repr__(self) -> str:
        return f"<CollectionMLMExtension Collection id={self.collection.id}>"


class _AssetMLMExtension(ABC):
    """
    Abstract base class for (derived) MLM asset extensions.
    """

    name: Literal["mlm"] = "mlm"
    asset: pystac.Asset
    asset_href: str
    properties: dict[str, Any]
    additional_read_properties: Iterable[dict[str, Any]] | None

    def __init__(self, asset: pystac.Asset):
        self.asset = asset
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    @classmethod
    def _ext(cls: type[AssetExtensionType], obj: pystac.Asset) -> AssetExtensionType:
        if not isinstance(obj, pystac.Asset):
            raise TypeError(
                "This class can only be used to extend Assets. "
                "For Items and Collections use MLMExtension."
            )
        return cls(obj)

    def to_dict(self) -> dict[str, Any]:
        """
        Serializes the extended asset's properties into a dict

        Returns:
            dict[str, Any]
        """
        return self.properties

    @classmethod
    def get_schema_uri(cls) -> str:
        """
        Retrieve this extension's schema URI

        Returns:
            str: Schema URI
        """
        return SCHEMA_URI_PATTERN.format(version=DEFAULT_VERSION)

    @property
    def artifact_type(self) -> str | None:
        """
        Get or set the artifact_type property. This is required if ``mlm:model`` as one
         of the asset's roles
        """
        prop_value = self.properties.get(ARTIFACT_TYPE_ASSET_PROP)
        if isinstance(self.asset.roles, list) and "mlm:model" in self.asset.roles:
            return get_required(prop_value, self, ARTIFACT_TYPE_ASSET_PROP)
        else:
            return prop_value

    @artifact_type.setter
    def artifact_type(self, v: str | None) -> None:
        if isinstance(self.asset.roles, list) and "mlm:model" in self.asset.roles:
            if v is None:
                raise pystac.errors.RequiredPropertyMissing(
                    self,
                    ARTIFACT_TYPE_ASSET_PROP,
                    f"{ARTIFACT_TYPE_ASSET_PROP} is a required property and must "
                    f"not be None for asset with role mlm:model.",
                )
            self.properties[ARTIFACT_TYPE_ASSET_PROP] = v
        else:
            if v is not None:
                self.properties[ARTIFACT_TYPE_ASSET_PROP] = v
            else:
                self.properties.pop(ARTIFACT_TYPE_ASSET_PROP, None)

    @property
    def compile_method(self) -> str | None:
        """
        Get or set this asset's compile_method property
        """
        return self.properties.get(COMPILE_METHOD_ASSET_PROP)

    @compile_method.setter
    def compile_method(self, v: str | None) -> None:
        if v is not None:
            self.properties[COMPILE_METHOD_ASSET_PROP] = v
        else:
            self.properties.pop(COMPILE_METHOD_ASSET_PROP, None)

    @property
    def entrypoint(self) -> str | None:
        """
        Get or set this asset's entrypoint property
        """
        return self.properties.get(ENTRYPOINT_ASSET_PROP)

    @entrypoint.setter
    def entrypoint(self, v: str | None) -> None:
        if v is not None:
            self.properties[ENTRYPOINT_ASSET_PROP] = v
        else:
            self.properties.pop(ENTRYPOINT_ASSET_PROP, None)


class AssetGeneralMLMExtension(
    _AssetMLMExtension,
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """A class that can be used to extend the properties of an
    :class:`pystac.Asset` object with properties from the
    :stac-ext:`Machine Learning Model Extension <mlm>`.

    Use this class, if model metadata is provided by by the asset's parent object
    (i.e. :class:`pystac.Item` or :class:`pystac.Item`. If Model metadata is provided
    by the asset object itself, use :class:`AssetDetailedMLMExtension`.

    For extending :class:`pystac.Item`, :class:`pystac.Collection` or
    :class:`pystac.ItemAssetDefinition` objects, use :class:`MLMExtension` instead.
    """

    def apply(
        self,
        artifact_type: str | None = None,
        compile_method: str | None = None,
        entrypoint: str | None = None,
    ) -> None:
        """
        Sets the properties of a new AssetGeneralMLMExtension

        Args:
            artifact_type: Specifies the kind of model artifact, any string is allowed.
                Typically related to a particular ML framework. This property is
                required when ``mlm:model`` is listed as a role of this asset
            compile_method: Describes the method used to compile the ML model either
                when the model is saved or at model runtime prior to inference
            entrypoint: Specific entrypoint reference in the code to use for running
                model inference.
        """
        self.artifact_type = artifact_type
        self.compile_method = compile_method
        self.entrypoint = entrypoint

    @classmethod
    def ext(
        cls, obj: pystac.Asset, add_if_missing: bool = False
    ) -> AssetGeneralMLMExtension[pystac.Asset]:
        """
        Extend a :class:`pystac.Asset` (``obj``) with the AssetGeneralMLMExtension

        Args:
            obj: The Asset to be extended.
            add_if_missing: Defines whether this extension's URI should be added to
                this asset's parent's list of extensions if it is not already
                listed there. Use ``False`` if the asset does not specify a parent

        Returns:
            AssetGeneralMLMExtension[pystac.Asset]: The extended object
        """
        cls.ensure_owner_has_extension(obj, add_if_missing)
        return AssetGeneralMLMExtension._ext(obj)

    def __repr__(self) -> str:
        return f"<AssetGeneralMLMExtension Asset href={self.asset_href}>"


class AssetDetailedMLMExtension(_AssetMLMExtension, MLMExtension[pystac.Asset]):
    """A class that can be used to extend the properties of an
    :class:`pystac.Asset` object with properties from the
    :stac-ext:`Machine Learning Model Extension <mlm>`.

    Use this class, if model metadata is provided by the asset. If model metadata is
    provided by the asset's parent object
    (i.e. :class:`pystac.Item` or :class:`pystac.Item`, use
    :class:`AssetGeneralMLMExtension`.

    For extending :class:`pystac.Item`, :class:`pystac.Collection` or
    :class:`pystac.ItemAssetDefinition` objects, use :class:`MLMExtension` instead.
    """

    def __repr__(self) -> str:
        return f"<AssetDetailedMLMExtension Asset href={self.asset_href}>"

    @classmethod
    def ext(
        cls, obj: pystac.Asset, add_if_missing: bool = False
    ) -> AssetDetailedMLMExtension:
        """
        Extend a :class:`pystac.Asset` (``obj``) with the AssetDetailedMLMExtension

        Args:
            obj: The Asset to be extended.
            add_if_missing: Defines whether this extension's URI should be added to
                this asset's parent's list of extensions if it is not already
                listed there. Use ``False`` if the asset does not specify a parent

        Returns:
            AssetDetailedMLMExtension[pystac.Asset]: The extended object
        """
        cls.ensure_owner_has_extension(obj, add_if_missing)
        return AssetDetailedMLMExtension._ext(obj)

    def apply(
        self,
        name: str,
        architecture: str,
        tasks: list[TaskType],
        input: list[ModelInput],
        output: list[ModelOutput],
        framework: str | None = None,
        framework_version: str | None = None,
        memory_size: int | None = None,
        total_parameters: int | None = None,
        pretrained: bool | None = None,
        pretrained_source: str | None = None,
        batch_size_suggestion: int | None = None,
        accelerator: AcceleratorType | None = None,
        accelerator_constrained: bool | None = None,
        accelerator_summary: str | None = None,
        accelerator_count: int | None = None,
        hyperparameters: Hyperparameters | None = None,
        artifact_type: str | None = None,
        compile_method: str | None = None,
        entrypoint: str | None = None,
    ) -> None:
        """
        Sets the properties of a new AssetDetailedMLMExtensions

        Args:
            name:  name for the model
            architecture: A generic and well established architecture name of the model
            tasks: Specifies the Machine Learning tasks for which the model can be
                used for
            input: Describes the transformation between the EO data and the model input
            output: Describes each model output and how to interpret it.
            framework: Framework used to train the model
            framework_version: The ``framework`` library version
            memory_size: The in-memory size of the model on the accelerator during
                inference (bytes)
            total_parameters: Total number of model parameters, including trainable and
                non-trainable parameters.
            pretrained: Indicates if the model was pretrained. If the model was
                pretrained, consider providing ``pretrained_source`` if it is known
            pretrained_source: The source of the pretraining.
            batch_size_suggestion: A suggested batch size for the accelerator and
                summarized hardware.
            accelerator: The intended computational hardware that runs inference
            accelerator_constrained: Indicates if the intended ``accelerator`` is the
                only accelerator that can run inference
            accelerator_summary: A high level description of the ``accelerator``
            accelerator_count: A minimum amount of ``accelerator`` instances required to
                run the model
            hyperparameters: Additional hyperparameters relevant for the model
            artifact_type: Specifies the kind of model artifact, any string is allowed.
                Typically related to a particular ML framework. This property is
                required when ``mlm:model`` is listed as a role of this asset
            compile_method: Describes the method used to compile the ML model either
                when the model is saved or at model runtime prior to inference
            entrypoint: Specific entrypoint reference in the code to use for running
                model inference.
        """
        MLMExtension.apply(
            self,
            name=name,
            architecture=architecture,
            tasks=tasks,
            input=input,
            output=output,
            framework=framework,
            framework_version=framework_version,
            memory_size=memory_size,
            total_parameters=total_parameters,
            pretrained=pretrained,
            pretrained_source=pretrained_source,
            batch_size_suggestion=batch_size_suggestion,
            accelerator=accelerator,
            accelerator_constrained=accelerator_constrained,
            accelerator_summary=accelerator_summary,
            accelerator_count=accelerator_count,
            hyperparameters=hyperparameters,
        )
        self.artifact_type = artifact_type
        self.compile_method = compile_method
        self.entrypoint = entrypoint


class ItemAssetMLMExtension(MLMExtension[pystac.ItemAssetDefinition]):
    properties: dict[str, Any]
    asset_defn: pystac.ItemAssetDefinition

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        self.asset_defn = item_asset
        self.properties = item_asset.properties

    def __repr__(self) -> str:
        return f"<ItemAssetsMLMExtension ItemAssetDefinition={self.asset_defn}"


class MLMExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI_PATTERN.format(version=DEFAULT_VERSION)
    prev_extension_ids = {
        SCHEMA_URI_PATTERN.format(version=v)
        for v in SUPPORTED_VERSIONS
        if v != DEFAULT_VERSION
    }
    stac_object_types = {pystac.STACObjectType.ITEM, pystac.STACObjectType.COLLECTION}

    def migrate(
        self, obj: dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        # mo adjustments to objects needed when migrating yet
        # schema back to v1.0 is fully backwards compatible
        super().migrate(obj, version, info)


MLM_EXTENSION_HOOKS: ExtensionHooks = MLMExtensionHooks()
