import json
import logging
import re
from copy import deepcopy
from typing import Any, cast

import pytest

import pystac.errors
from pystac import Asset, Collection, Item, ItemAssetDefinition
from pystac.errors import STACError
from pystac.extensions.classification import Classification
from pystac.extensions.mlm import (
    ARCHITECTURE_PROP,
    NAME_PROP,
    TASKS_PROP,
    AcceleratorType,
    AssetDetailedMLMExtension,
    AssetGeneralMLMExtension,
    Hyperparameters,
    InputStructure,
    ItemMLMExtension,
    MLMExtension,
    MLMExtensionHooks,
    ModelBand,
    ModelInput,
    ModelOutput,
    ProcessingExpression,
    ResizeType,
    ResultStructure,
    TaskType,
    ValueScaling,
    ValueScalingType,
)
from pystac.extensions.raster import DataType
from tests.utils import TestCases

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

BASIC_MLM_ITEM_URI = TestCases.get_path("data-files/mlm/item_basic.json")
PLAIN_ITEM_URI = TestCases.get_path("data-files/item/sample-item.json")
MLM_COLLECTION_URI = TestCases.get_path("data-files/mlm/collection.json")


@pytest.fixture
def basic_item_dict() -> dict[str, Any]:
    with open(BASIC_MLM_ITEM_URI) as f:
        return cast(dict[str, Any], json.load(f))


@pytest.fixture
def basic_mlm_item() -> Item:
    return Item.from_file(BASIC_MLM_ITEM_URI)


@pytest.fixture
def plain_item() -> Item:
    return Item.from_file(PLAIN_ITEM_URI)


@pytest.fixture
def mlm_collection() -> Collection:
    return Collection.from_file(MLM_COLLECTION_URI)


def test_stac_extension(basic_mlm_item: Item) -> None:
    assert MLMExtension.has_extension(basic_mlm_item)


def test_model_band() -> None:
    d = {"name": "asdf", "format": "qwer", "expression": "asdf"}
    c = ModelBand.create(**d)
    assert c.name == d["name"]
    assert c.format == d["format"]
    assert c.expression == d["expression"]

    assert c.to_dict() == d

    with pytest.raises(NotImplementedError):
        _ = c == "blah"


def test_model_props() -> None:
    c = ModelBand({})
    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = c.name

    c.name = "asdf"
    assert c.name == "asdf"

    c.format = "asdf"
    assert c.name == "asdf"

    assert c.expression is None
    c.expression = "asdf"
    assert c.expression == "asdf"


def test_processing_expression() -> None:
    d = {"format": "python", "expression": "asdf"}
    c = ProcessingExpression.create(**d)
    assert c.format == d["format"]
    assert c.expression == d["expression"]

    assert c.to_dict() == d

    with pytest.raises(NotImplementedError):
        _ = c == "blah"


def test_processint_expression_props() -> None:
    c = ProcessingExpression({})

    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = c.format
    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = c.expression

    c.format = "python"
    assert c.format == "python"

    c.expression = "B01 + B02"
    assert c.expression == "B01 + B02"


@pytest.mark.parametrize(
    "scale_type, min_val, max_val, mean, stddev, value, format_val, expression",
    [
        (ValueScalingType.MIN_MAX, 0, 4, 3, 3, 4, "asdf", "asdf"),
        (ValueScalingType.MIN_MAX, 0.2, 4.3, 3.13, 3.2, 4.5, "asdf", "asdf"),
        (ValueScalingType.MIN_MAX, 0, 4, None, None, None, None, None),
        (ValueScalingType.SCALE, None, None, None, None, 2, None, None),
    ],
)
def test_valuescaling_object(
    scale_type: ValueScalingType,
    min_val: int | float | None,
    max_val: int | float | None,
    mean: int | float | None,
    stddev: int | float | None,
    value: int | float | None,
    format_val: str | None,
    expression: str | None,
) -> None:
    c = ValueScaling.create(
        scale_type,
        minimum=min_val,
        maximum=max_val,
        mean=mean,
        stddev=stddev,
        value=value,
        format=format_val,
        expression=expression,
    )
    assert c.type == scale_type
    assert c.minimum == min_val
    assert c.maximum == max_val
    assert c.mean == mean
    assert c.stddev == stddev
    assert c.value == value
    assert c.format == format_val
    assert c.expression == expression

    with pytest.raises(STACError):
        ValueScaling.create(
            ValueScalingType.MIN_MAX, minimum=1
        )  # missing param maximum

    with pytest.raises(STACError):
        ValueScaling.create(ValueScalingType.Z_SCORE, mean=3)  # missing param stddev

    with pytest.raises(NotImplementedError):
        _ = c == "blah"


def test_valuescaling_required_params() -> None:
    assert ValueScaling.get_required_props(ValueScalingType.MIN_MAX) == [
        "minimum",
        "maximum",
    ]
    assert ValueScaling.get_required_props(ValueScalingType.Z_SCORE) == [
        "mean",
        "stddev",
    ]
    assert ValueScaling.get_required_props(ValueScalingType.CLIP) == [
        "minimum",
        "maximum",
    ]
    assert ValueScaling.get_required_props(ValueScalingType.CLIP_MIN) == ["minimum"]
    assert ValueScaling.get_required_props(ValueScalingType.CLIP_MAX) == ["maximum"]
    assert ValueScaling.get_required_props(ValueScalingType.OFFSET) == ["value"]
    assert ValueScaling.get_required_props(ValueScalingType.SCALE) == ["value"]
    assert ValueScaling.get_required_props(ValueScalingType.PROCESSING) == [
        "format",
        "expression",
    ]


def test_input_structure() -> None:
    c = InputStructure.create(
        shape=[-1, 3, 64, 64],
        dim_order=["batch", "channel", "width", "height"],
        data_type=DataType.FLOAT64,
    )
    assert c.shape == [-1, 3, 64, 64]
    assert c.dim_order == ["batch", "channel", "width", "height"]
    assert c.data_type == DataType.FLOAT64

    with pytest.raises(NotImplementedError):
        _ = c == "blah"


def test_model_input_structure_props() -> None:
    c = InputStructure({})

    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = c.shape
    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = c.dim_order
    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = c.data_type

    c.shape = [1]
    assert c.shape == [1]

    c.dim_order = ["bands"]
    assert c.dim_order == ["bands"]

    c.data_type = DataType.FLOAT64
    assert c.data_type == DataType.FLOAT64


input_testdata = [
    (
        ["B02", "B03", "B04"],
        [ValueScaling.create(ValueScalingType.SCALE, value=3)],
        ResizeType.CROP,
        ProcessingExpression.create("python", "asdf"),
    ),
    (
        ["B02", "B03", "B04"],
        [ValueScaling.create(ValueScalingType.SCALE, value=3)],
        None,
        ProcessingExpression.create("python", "asdf"),
    ),
    (
        [ModelBand.create("B02"), ModelBand.create("B03"), ModelBand.create("B04")],
        [ValueScaling.create(ValueScalingType.SCALE, value=3)],
        ResizeType.CROP,
        ProcessingExpression.create("python", "asdf"),
    ),
    (
        ["B02", "B03", "B04"],
        None,
        ResizeType.CROP,
        ProcessingExpression.create("python", "asdf"),
    ),
    (
        ["B02", "B03", "B04"],
        [ValueScaling.create(ValueScalingType.SCALE, value=3)],
        ResizeType.CROP,
        None,
    ),
]


@pytest.mark.parametrize(
    "bands, value_scaling, resize_type, pre_processing_function", input_testdata
)
def test_model_input(
    bands: list[str] | list[ModelBand],
    value_scaling: list[ValueScaling] | None,
    resize_type: ResizeType | None,
    pre_processing_function: ProcessingExpression | None,
) -> None:
    input_structure = InputStructure.create(
        [1, 2, 3], ["batch", "width", "length"], DataType.FLOAT64
    )

    c = ModelInput.create(
        name="asdf",
        bands=bands,
        input=input_structure,
        description="foo",
        value_scaling=value_scaling,
        resize_type=resize_type,
        pre_processing_function=pre_processing_function,
    )
    assert c.name == "asdf"
    assert c.bands == bands
    assert c.input == input_structure
    assert c.description == "foo"
    assert c.value_scaling == value_scaling
    assert c.resize_type == resize_type
    assert c.pre_processing_function == pre_processing_function

    # assert that some attributes are always included in dict, even if they are None
    d_reverse = c.to_dict()
    assert "value_scaling" in d_reverse
    assert "resize_type" in d_reverse
    assert "pre_processing_function" in d_reverse

    with pytest.raises(NotImplementedError):
        _ = c == "blah"


def test_model_input_props() -> None:
    c = ModelInput({})
    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = c.name
    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = c.bands
    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = c.input

    c.name = "asdf"
    assert c.name == "asdf"

    c.bands = ["B02", "B03"]
    assert c.bands == ["B02", "B03"]

    inp = InputStructure.create([12], ["bands"], DataType.FLOAT64)
    c.input = inp
    assert c.input == inp

    assert c.value_scaling is None
    val_obj = [ValueScaling.create(ValueScalingType.SCALE, value=3)]
    c.value_scaling = val_obj
    assert c.value_scaling == val_obj

    assert c.resize_type is None
    c.resize_type = ResizeType.CROP
    assert c.resize_type == ResizeType.CROP

    assert c.pre_processing_function is None
    exp = ProcessingExpression.create("python", "asdf")
    c.pre_processing_function = exp
    assert c.pre_processing_function == exp


def test_result_structure() -> None:
    c = ResultStructure.create(
        shape=[1, 64, 64],
        dim_order=["time", "width", "height"],
        data_type=DataType.FLOAT64,
    )
    assert c.shape == [1, 64, 64]
    assert c.dim_order == ["time", "width", "height"]
    assert c.data_type == DataType.FLOAT64

    with pytest.raises(NotImplementedError):
        _ = c == "blah"


def test_result_structure_props() -> None:
    c = ResultStructure({})

    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = c.shape
    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = c.dim_order
    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = c.data_type

    c.shape = [1, 2, 3]
    c.dim_order = ["batch", "band", "time"]
    c.data_type = DataType.FLOAT64

    assert c.shape == [1, 2, 3]
    assert c.dim_order == ["batch", "band", "time"]
    assert c.data_type == DataType.FLOAT64


@pytest.mark.parametrize(
    "post_proc_func", (ProcessingExpression.create("asdf", "asdf"), None)
)
def test_model_output(post_proc_func: ProcessingExpression | None) -> None:
    c = ModelOutput.create(
        name="asdf",
        tasks=[TaskType.DETECTION, TaskType.OBJECT_DETECTION],
        result=ResultStructure.create([1, 2, 3], ["a", "b", "c"], DataType.FLOAT64),
        description="asdf",
        classes=[
            Classification.create(1, name="a"),
            Classification.create(2, name="b"),
        ],
        post_processing_function=post_proc_func,
    )
    assert c.name == "asdf"
    assert c.tasks == [TaskType.DETECTION, TaskType.OBJECT_DETECTION]
    assert c.result == ResultStructure.create(
        [1, 2, 3], ["a", "b", "c"], DataType.FLOAT64
    )
    assert c.description == "asdf"
    assert c.classes == [
        Classification.create(1, name="a"),
        Classification.create(2, name="b"),
    ]
    assert c.post_processing_function == post_proc_func

    with pytest.raises(NotImplementedError):
        _ = c == "blah"


def test_model_output_props() -> None:
    c = ModelOutput({})

    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = c.name
    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = c.tasks
    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = c.result

    c.name = "asdf"
    assert c.name == "asdf"

    c.tasks = [TaskType.CLASSIFICATION]
    assert c.tasks == [TaskType.CLASSIFICATION]

    res = ResultStructure.create([1], ["band"], DataType.FLOAT64)
    c.result = res
    assert c.result == res

    assert c.description is None
    c.description = "asdf"
    assert c.description == "asdf"

    assert c.classes is None
    c.classes = [Classification.create(value=3, name="foo")]
    assert c.classes == [Classification.create(value=3, name="foo")]

    exp = ProcessingExpression.create("python", "asdf")
    assert c.post_processing_function is None
    c.post_processing_function = exp
    assert c.post_processing_function == exp


def test_hyperparameters() -> None:
    d = {
        "nms_max_detections": 500,
        "nms_threshold": 0.25,
        "iou_threshold": 0.5,
        "random_state": 12345,
    }
    c = Hyperparameters.create(**d)
    for key in d:
        assert key in c.to_dict()
        assert c.to_dict()[key] == d[key]

    with pytest.raises(NotImplementedError):
        _ = c == "blah"


def teest_get_schema_uri(basic_mlm_item: Item) -> None:
    with pytest.raises(DeprecationWarning):
        assert any(
            [
                uri in basic_mlm_item.stac_extensions
                for uri in MLMExtension.get_schema_uris()
            ]
        )


def test_ext_raises_if_item_does_not_conform(plain_item: Item) -> None:
    with pytest.raises(pystac.errors.ExtensionNotImplemented):
        MLMExtension.ext(plain_item)


@pytest.mark.vcr()
def test_apply(plain_item: Item) -> None:
    plain_item.assets["model"] = Asset(
        href="https://google.com",
        roles=["mlm:model"],
        extra_fields={"mlm:artifact_type": "asdf"},
    )

    MLMExtension.add_to(plain_item)
    assert MLMExtension.get_schema_uri() in plain_item.stac_extensions

    model_input = [
        ModelInput.create(
            name="modelinput",
            bands=[],
            input=InputStructure.create(
                shape=[-1, 64, 64],
                dim_order=["batch", "width", "height"],
                data_type=DataType.FLOAT64,
            ),
        )
    ]
    model_output = [
        ModelOutput.create(
            name="modeloutput",
            tasks=[TaskType.CLASSIFICATION],
            result=ResultStructure.create(
                shape=[1, 64, 64],
                dim_order=["batch", "width", "height"],
                data_type=DataType.FLOAT64,
            ),
        )
    ]
    hyp = Hyperparameters.create(
        nms_max_detections=500,
        nms_threshold=0.25,
        iou_threshold=0.5,
        random_state=12345,
    )

    MLMExtension.ext(plain_item).apply(
        name="asdf",
        architecture="ResNet",
        tasks=[TaskType.CLASSIFICATION],
        framework="PyTorch",
        framework_version="1.2.3",
        memory_size=3,
        total_parameters=123,
        pretrained=True,
        pretrained_source="asdfasdfasdf",
        batch_size_suggestion=32,
        accelerator=AcceleratorType.CUDA,
        accelerator_constrained=False,
        accelerator_summary="This is the summary",
        accelerator_count=1,
        input=model_input,
        output=model_output,
        hyperparameters=hyp,
    )
    plain_item.validate()

    assert (
        MLMExtension.ext(plain_item).mlm_name is not None
        and MLMExtension.ext(plain_item).mlm_name == "asdf"
    )

    assert (
        MLMExtension.ext(plain_item).architecture is not None
        and MLMExtension.ext(plain_item).architecture == "ResNet"
    )

    assert MLMExtension.ext(plain_item).tasks is not None and MLMExtension.ext(
        plain_item
    ).tasks == [TaskType.CLASSIFICATION]

    assert (
        MLMExtension.ext(plain_item).framework is not None
        and MLMExtension.ext(plain_item).framework == "PyTorch"
    )

    assert (
        MLMExtension.ext(plain_item).framework_version is not None
        and MLMExtension.ext(plain_item).framework_version == "1.2.3"
    )

    assert (
        MLMExtension.ext(plain_item).memory_size is not None
        and MLMExtension.ext(plain_item).memory_size == 3
    )

    assert (
        MLMExtension.ext(plain_item).total_parameters is not None
        and MLMExtension.ext(plain_item).total_parameters == 123
    )

    assert (
        MLMExtension.ext(plain_item).pretrained is not None
        and MLMExtension.ext(plain_item).pretrained is True
    )

    assert (
        MLMExtension.ext(plain_item).pretrained_source is not None
        and MLMExtension.ext(plain_item).pretrained_source == "asdfasdfasdf"
    )

    assert (
        MLMExtension.ext(plain_item).batch_size_suggestion is not None
        and MLMExtension.ext(plain_item).batch_size_suggestion == 32
    )

    assert (
        MLMExtension.ext(plain_item).accelerator is not None
        and MLMExtension.ext(plain_item).accelerator == AcceleratorType.CUDA
    )

    assert (
        MLMExtension.ext(plain_item).accelerator_constrained is not None
        and MLMExtension.ext(plain_item).accelerator_constrained is False
    )

    assert (
        MLMExtension.ext(plain_item).accelerator_summary is not None
        and MLMExtension.ext(plain_item).accelerator_summary == "This is the summary"
    )

    assert (
        MLMExtension.ext(plain_item).accelerator_count is not None
        and MLMExtension.ext(plain_item).accelerator_count == 1
    )

    assert MLMExtension.ext(plain_item).input is not None and len(
        MLMExtension.ext(plain_item).input
    ) == len(model_input)

    assert MLMExtension.ext(plain_item).input[0] == model_input[0]

    assert MLMExtension.ext(plain_item).output is not None and len(
        MLMExtension.ext(plain_item).output
    ) == len(model_output)

    assert MLMExtension.ext(plain_item).output[0] == model_output[0]

    assert (
        MLMExtension.ext(plain_item).hyperparameters is not None
        and MLMExtension.ext(plain_item).hyperparameters == hyp
    )

    d = {
        **plain_item.properties,
        "mlm:name": "asdf",
        "mlm:architecture": "ResNet",
        "mlm:tasks": [TaskType.CLASSIFICATION],
        "mlm:framework": "PyTorch",
        "mlm:framework_version": "1.2.3",
        "mlm:memory_size": 3,
        "mlm:total_parameters": 123,
        "mlm:pretrained": True,
        "mlm:pretrained_source": "asdfasdfasdf",
        "mlm:batch_size_suggestion": 32,
        "mlm:accelerator": AcceleratorType.CUDA,
        "mlm:accelerator_constrained": False,
        "mlm:accelerator_summary": "This is the summary",
        "mlm:accelerator_count": 1,
        "mlm:input": [inp.to_dict() for inp in model_input],
        "mlm:output": [out.to_dict() for out in model_output],
        "mlm:hyperparameters": hyp.to_dict(),
    }

    assert MLMExtension.ext(plain_item).to_dict() == d


def test_apply_wrong_object() -> None:
    with pytest.raises(pystac.ExtensionTypeError):
        _ = MLMExtension.ext(1, False)


def test_to_from_dict(basic_item_dict: dict[str, Any]) -> None:
    d1 = deepcopy(basic_item_dict)
    d2 = Item.from_dict(basic_item_dict, migrate=False).to_dict()

    assert d1 == d2


def test_add_to_item(plain_item: Item) -> None:
    # check that URI gets added
    assert MLMExtension.get_schema_uri() not in plain_item.stac_extensions
    MLMExtension.add_to(plain_item)
    assert MLMExtension.get_schema_uri() in plain_item.stac_extensions

    # Assure that it gets added only once
    MLMExtension.add_to(plain_item)
    MLMExtension.add_to(plain_item)

    mlm_uris = [
        uri
        for uri in plain_item.stac_extensions
        if uri == MLMExtension.get_schema_uri()
    ]
    assert len(mlm_uris) == 1


@pytest.mark.vcr()
def test_validate_mlm(basic_mlm_item: Item) -> None:
    basic_mlm_item.validate()


def test_add_required_props(plain_item: Item) -> None:
    item_ext = MLMExtension.ext(plain_item, add_if_missing=True)

    assert isinstance(item_ext, ItemMLMExtension)

    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = item_ext.mlm_name
    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = item_ext.architecture
    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = item_ext.tasks
    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = item_ext.input
    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        _ = item_ext.output

    model_input = ModelInput.create(
        name="DummyModel",
        bands=["B04", "B08"],
        input=InputStructure.create(
            shape=[2, 10], dim_order=["time", "bands"], data_type=DataType.FLOAT64
        ),
    )
    model_output = ModelOutput.create(
        name="out",
        tasks=[TaskType.CLASSIFICATION],
        result=ResultStructure.create(
            shape=[1], dim_order=["classification"], data_type=DataType.FLOAT64
        ),
    )
    item_ext.mlm_name = "DummyModel"
    item_ext.architecture = "ResNet"
    item_ext.tasks = [TaskType.CLASSIFICATION]
    item_ext.input = [model_input]
    item_ext.output = [model_output]

    assert item_ext.mlm_name == "DummyModel"
    assert item_ext.architecture == "ResNet"
    assert item_ext.tasks == [TaskType.CLASSIFICATION]
    assert item_ext.input == [model_input]
    assert item_ext.output == [model_output]


def test_add_optional_props(plain_item: Item) -> None:
    item_ext = MLMExtension.ext(plain_item, add_if_missing=True)

    assert isinstance(item_ext, ItemMLMExtension)
    assert item_ext.framework is None
    item_ext.framework = "pytorch"
    assert item_ext.framework == "pytorch"

    assert item_ext.framework_version is None
    item_ext.framework_version = "1.0.0"
    assert item_ext.framework_version == "1.0.0"

    assert item_ext.memory_size is None
    item_ext.memory_size = 3
    assert item_ext.memory_size == 3

    assert item_ext.total_parameters is None
    item_ext.total_parameters = 10000
    assert item_ext.total_parameters == 10000

    assert item_ext.pretrained is None
    item_ext.pretrained = True
    assert item_ext.pretrained is True

    assert item_ext.pretrained_source is None
    item_ext.pretrained_source = "asdf"
    assert item_ext.pretrained_source == "asdf"

    assert item_ext.batch_size_suggestion is None
    item_ext.batch_size_suggestion = 64
    assert item_ext.batch_size_suggestion == 64

    assert item_ext.accelerator is None
    item_ext.accelerator = AcceleratorType.CUDA
    assert item_ext.accelerator == AcceleratorType.CUDA

    assert item_ext.accelerator_constrained is None
    item_ext.accelerator_constrained = False
    assert item_ext.accelerator_constrained is False

    assert item_ext.accelerator_summary is None
    item_ext.accelerator_summary = "Summary"
    assert item_ext.accelerator_summary == "Summary"

    assert item_ext.accelerator_count is None
    item_ext.accelerator_count = 1
    assert item_ext.accelerator_count == 1


def test_add_to_asset(plain_item: Item) -> None:
    MLMExtension.ext(plain_item, add_if_missing=True)
    asset = plain_item.assets["analytic"]

    assert NAME_PROP not in asset.extra_fields.keys()
    assert ARCHITECTURE_PROP not in asset.extra_fields.keys()
    assert TASKS_PROP not in asset.extra_fields.keys()

    asset_ext = AssetDetailedMLMExtension.ext(asset)
    asset_ext.mlm_name = "asdf"
    asset_ext.architecture = "ResNet"
    asset_ext.tasks = [TaskType.CLASSIFICATION]

    assert NAME_PROP in asset.extra_fields.keys()
    assert ARCHITECTURE_PROP in asset.extra_fields.keys()
    assert TASKS_PROP in asset.extra_fields.keys()

    assert asset.extra_fields[NAME_PROP] == "asdf"
    assert asset.extra_fields[ARCHITECTURE_PROP] == "ResNet"
    assert asset.extra_fields[TASKS_PROP] == [TaskType.CLASSIFICATION]


@pytest.mark.parametrize("is_model_asset", (True, False))
def test_asset_props(plain_item: Item, is_model_asset: bool) -> None:
    asset = plain_item.assets["analytic"]
    asset_ext = AssetGeneralMLMExtension.ext(asset, add_if_missing=True)

    assert asset_ext.artifact_type is None
    assert asset_ext.compile_method is None
    assert asset_ext.entrypoint is None

    # test special behavior if the asset has role "mlm:model"
    if is_model_asset and isinstance(asset_ext.asset.roles, list):
        asset_ext.asset.roles.append("mlm:model")
        with pytest.raises(pystac.errors.RequiredPropertyMissing):
            _ = asset_ext.artifact_type

    asset_ext.artifact_type = "foo"
    asset_ext.compile_method = "bar"
    asset_ext.entrypoint = "baz"

    assert asset_ext.artifact_type == "foo"
    assert asset_ext.compile_method == "bar"
    assert asset_ext.entrypoint == "baz"


def test_add_to_generic_asset() -> None:
    asset = pystac.Asset(
        href="http://example.com/test.tiff",
        title="image",
        description="asdf",
        media_type="application/tiff",
        roles=["mlm:model"],
        extra_fields={
            "mlm:artifact_type": "foo",
            "mlm:compile_method": "bar",
            "mlm:entrypoint": "baz",
        },
    )
    asset_ext = AssetGeneralMLMExtension.ext(asset, add_if_missing=False)
    assert asset_ext.artifact_type == "foo"
    assert asset_ext.compile_method == "bar"
    assert asset_ext.entrypoint == "baz"


def test_apply_generic_asset() -> None:
    asset = pystac.Asset(
        href="http://example.com/test.tiff",
        title="image",
        description="asdf",
        media_type="application/tiff",
        roles=["mlm:model"],
    )
    asset_ext = AssetGeneralMLMExtension.ext(asset, add_if_missing=False)
    asset_ext.apply(artifact_type="foo", compile_method="bar", entrypoint="baz")
    assert asset_ext.artifact_type == "foo"
    assert asset_ext.compile_method == "bar"
    assert asset_ext.entrypoint == "baz"


def test_to_dict_asset_generic() -> None:
    asset = pystac.Asset(
        href="http://example.com/test.tiff",
        title="image",
        description="asdf",
        media_type="application/tiff",
        roles=["mlm:model"],
    )
    asset_ext = AssetGeneralMLMExtension.ext(asset, add_if_missing=False)
    asset_ext.apply(artifact_type="foo", compile_method="bar", entrypoint="baz")

    d = {
        "mlm:artifact_type": "foo",
        "mlm:compile_method": "bar",
        "mlm:entrypoint": "baz",
    }
    assert asset_ext.to_dict() == d


def test_add_to_detailled_asset() -> None:
    model_input = ModelInput.create(
        name="model",
        bands=["B02"],
        input=InputStructure.create(
            shape=[1], dim_order=["batch"], data_type=DataType.FLOAT64
        ),
    )
    model_output = ModelOutput.create(
        name="output",
        tasks=[TaskType.CLASSIFICATION],
        result=ResultStructure.create(
            shape=[1], dim_order=["batch"], data_type=DataType.FLOAT64
        ),
    )

    asset = pystac.Asset(
        href="http://example.com/test.tiff",
        title="image",
        description="asdf",
        media_type="application/tiff",
        roles=["mlm:model"],
        extra_fields={
            "mlm:name": "asdf",
            "mlm:architecture": "ResNet",
            "mlm:tasks": [TaskType.CLASSIFICATION],
            "mlm:input": [model_input.to_dict()],
            "mlm:output": [model_output.to_dict()],
            "mlm:artifact_type": "foo",
            "mlm:compile_method": "bar",
            "mlm:entrypoint": "baz",
        },
    )

    asset_ext = AssetDetailedMLMExtension.ext(asset, add_if_missing=False)

    assert asset_ext.mlm_name == "asdf"
    assert asset_ext.architecture == "ResNet"
    assert asset_ext.tasks == [TaskType.CLASSIFICATION]
    assert asset_ext.input == [model_input]
    assert asset_ext.output == [model_output]
    assert asset_ext.artifact_type == "foo"
    assert asset_ext.compile_method == "bar"
    assert asset_ext.entrypoint == "baz"

    assert repr(asset_ext) == f"<AssetDetailedMLMExtension Asset href={asset.href}>"

    with pytest.raises(pystac.errors.RequiredPropertyMissing):
        asset_ext.artifact_type = None

    asset_ext.compile_method = None
    assert asset_ext.compile_method is None

    asset_ext.entrypoint = None
    assert asset_ext.entrypoint is None

    asset.roles.remove("mlm:model") if isinstance(asset.roles, list) else None
    asset_ext.artifact_type = None
    assert asset_ext.artifact_type is None


def test_correct_asset_extension_is_used() -> None:
    asset = Asset("https://example.com")
    assert isinstance(asset.ext.mlm, AssetGeneralMLMExtension)

    asset.extra_fields["mlm:name"] = "asdf"
    assert isinstance(asset.ext.mlm, AssetDetailedMLMExtension)


def test_asset_accessor() -> None:
    item_asset = ItemAssetDefinition.create(
        title="asdf", description="asdf", media_type="asdf", roles=["asdf"]
    )
    assert isinstance(item_asset.ext.mlm, MLMExtension)


def test_apply_detailled_asset() -> None:
    asset = pystac.Asset(
        href="http://example.com/test.tiff",
        title="image",
        description="asdf",
        media_type="application/tiff",
        roles=["mlm:model"],
    )
    asset_ext = AssetDetailedMLMExtension.ext(asset, add_if_missing=False)

    model_input = ModelInput.create(
        name="model",
        bands=["B02"],
        input=InputStructure.create(
            shape=[1], dim_order=["batch"], data_type=DataType.FLOAT64
        ),
    )
    model_output = ModelOutput.create(
        name="output",
        tasks=[TaskType.CLASSIFICATION],
        result=ResultStructure.create(
            shape=[1], dim_order=["batch"], data_type=DataType.FLOAT64
        ),
    )

    asset_ext.apply(
        "asdf",
        "ResNet",
        [TaskType.CLASSIFICATION],
        [model_input],
        [model_output],
        artifact_type="foo",
        compile_method="bar",
        entrypoint="baz",
    )

    assert asset_ext.mlm_name == "asdf"
    assert asset_ext.architecture == "ResNet"
    assert asset_ext.tasks == [TaskType.CLASSIFICATION]
    assert asset_ext.input == [model_input]
    assert asset_ext.output == [model_output]
    assert asset_ext.artifact_type == "foo"
    assert asset_ext.compile_method == "bar"
    assert asset_ext.entrypoint == "baz"


def test_to_dict_detailed_asset() -> None:
    asset = pystac.Asset(
        href="http://example.com/test.tiff",
        title="image",
        description="asdf",
        media_type="application/tiff",
        roles=["mlm:model"],
    )
    asset_ext = AssetDetailedMLMExtension.ext(asset, add_if_missing=False)

    model_input = ModelInput.create(
        name="model",
        bands=["B02"],
        input=InputStructure.create(
            shape=[1], dim_order=["batch"], data_type=DataType.FLOAT64
        ),
    )
    model_output = ModelOutput.create(
        name="output",
        tasks=[TaskType.CLASSIFICATION],
        result=ResultStructure.create(
            shape=[1], dim_order=["batch"], data_type=DataType.FLOAT64
        ),
    )

    asset_ext.apply(
        "asdf",
        "ResNet",
        [TaskType.CLASSIFICATION],
        [model_input],
        [model_output],
        artifact_type="foo",
        compile_method="bar",
        entrypoint="baz",
    )

    d = {
        "mlm:name": "asdf",
        "mlm:architecture": "ResNet",
        "mlm:tasks": [TaskType.CLASSIFICATION],
        "mlm:input": [model_input.to_dict()],
        "mlm:output": [model_output.to_dict()],
        "mlm:artifact_type": "foo",
        "mlm:compile_method": "bar",
        "mlm:entrypoint": "baz",
        "mlm:accelerator": None,
        "mlm:pretrained_source": None,
    }
    assert asset_ext.to_dict() == d


def test_item_asset_extension(mlm_collection: Collection) -> None:
    assert mlm_collection.item_assets
    item_asset = mlm_collection.item_assets["weights"]
    item_asset_ext = MLMExtension.ext(item_asset, add_if_missing=True)
    assert MLMExtension.get_schema_uri() in mlm_collection.stac_extensions
    assert mlm_collection.item_assets["weights"].ext.has("mlm")

    assert (
        repr(item_asset_ext)
        == f"<ItemAssetsMLMExtension ItemAssetDefinition={item_asset}"
    )


def test_collection_extension(mlm_collection: Collection) -> None:
    coll_ext = MLMExtension.ext(mlm_collection, add_if_missing=True)
    assert MLMExtension.get_schema_uri() in mlm_collection.stac_extensions
    assert mlm_collection.ext.has("mlm")

    coll_ext.mlm_name = "asdf"
    assert coll_ext.mlm_name == "asdf"
    assert (
        repr(coll_ext) == f"<CollectionMLMExtension Collection id={mlm_collection.id}>"
    )


def test_raise_exception_on_mlm_extension_and_asset() -> None:
    asset = pystac.Asset(
        href="http://example.com/test.tiff",
        title="image",
        description="asdf",
        media_type="application/tiff",
        roles=["mlm:model"],
    )
    with pytest.raises(TypeError):
        MLMExtension.ext(asset, add_if_missing=False)


@pytest.mark.parametrize(
    "framework_old, framework_new, valid",
    (
        ("Scikit-learn", "scikit-learn", False),
        ("Huggingface", "Hugging Face", False),
        ("-_ .asdf", "asdf", False),
        ("asdf-_ .", "asdf", False),
        ("-._   asdf-.", "asdf", False),
        ("test_framework", "test_framework", True),
    ),
)
def test_migration_1_0_to_1_1(
    framework_old: None | str, framework_new: None | str, valid: bool
) -> None:
    data: dict[str, Any] = {"properties": {}}

    MLMExtensionHooks._migrate_1_0_to_1_1(data)
    assert "mlm:framework" not in data["properties"]

    pattern = r"^(?=[^\s._\-]).*[^\s._\-]$"
    data["properties"]["mlm:framework"] = framework_old

    if valid:
        MLMExtensionHooks._migrate_1_0_to_1_1(data)
    else:
        with pytest.warns(SyntaxWarning):
            MLMExtensionHooks._migrate_1_0_to_1_1(data)

    assert data["properties"]["mlm:framework"] == framework_new
    assert bool(re.match(pattern, data["properties"]["mlm:framework"]))


def test_migration_1_1_to_1_2() -> None:
    data: dict[str, Any] = {}
    MLMExtensionHooks._migrate_1_1_to_1_2(data)

    data["assets"] = {"asset1": {"roles": ["data"]}, "asset2": {"roles": ["labels"]}}

    with pytest.raises(pystac.errors.STACError):
        MLMExtensionHooks._migrate_1_1_to_1_2(data)

    data["assets"]["asset3"] = {"roles": ["mlm:model"]}

    MLMExtensionHooks._migrate_1_1_to_1_2(data)


@pytest.mark.parametrize(
    "inp_bands, raster_bands, valid",
    (
        ([], None, True),
        (
            ["B02", "B03"],
            [
                {"name": "B02", "data_type": "float64"},
                {"name": "B03", "data_type": "float64"},
            ],
            True,
        ),
        (
            ["B02", "B03"],
            [
                {"name": "", "data_type": "float64"},
                {"name": "", "data_type": "float64"},
            ],
            False,
        ),
        (
            ["B02", "B03"],
            [
                {"name": "B02", "data_type": "float64"},
                {"name": "", "data_type": "float64"},
            ],
            False,
        ),
        (
            ["B02", "B03"],
            [{"name": "B02", "data_type": "float64"}, {"data_type": "float64"}],
            False,
        ),
        (
            ["B02", "B03"],
            [{"name": "", "data_type": "float64"}, {"data_type": "float64"}],
            False,
        ),
        (["B02", "B03"], [{"data_type": "float64"}, {"data_type": "float64"}], False),
    ),
)
def test_migration_1_2_to_1_3(
    inp_bands: list[str], raster_bands: list[dict[str, Any]], valid: bool
) -> None:
    data: dict[str, Any] = {
        "properties": {"mlm:input": {}},
        "assets": {"asset1": {"roles": ["data"]}, "asset2": {"roles": ["mlm:model"]}},
    }

    if inp_bands:
        data["properties"]["mlm:input"]["bands"] = inp_bands
        data["properties"]["raster:bands"] = raster_bands

    if valid:
        MLMExtensionHooks._migrate_1_2_to_1_3(data)
        if raster_bands:
            assert "raster:bands" not in data["assets"]["asset1"]
            assert "raster:bands" in data["assets"]["asset2"]
    else:
        with pytest.raises(STACError):
            MLMExtensionHooks._migrate_1_2_to_1_3(data)


@pytest.mark.parametrize(
    ("norm_by_channel", "norm_type", "norm_clip", "statistics", "value_scaling"),
    (
        (None, None, None, None, None),
        (False, None, None, None, None),
        (
            False,
            "z-score",
            None,
            [{"mean": 5, "stddev": 2}],
            [ValueScaling.create(ValueScalingType.Z_SCORE, mean=5, stddev=2)],
        ),
        (
            False,
            "min-max",
            None,
            [{"minimum": 10, "maximum": 20}],
            [ValueScaling.create(ValueScalingType.MIN_MAX, minimum=10, maximum=20)],
        ),
        (
            True,
            "z-score",
            None,
            [
                {"mean": 5, "stddev": 2},
                {"mean": 6, "stddev": 3},
                {"mean": 10, "stddev": 1},
            ],
            [
                ValueScaling.create(type=ValueScalingType.Z_SCORE, mean=5, stddev=2),
                ValueScaling.create(type=ValueScalingType.Z_SCORE, mean=6, stddev=3),
                ValueScaling.create(type=ValueScalingType.Z_SCORE, mean=10, stddev=1),
            ],
        ),
        (
            True,
            "clip",
            [3, 4, 5],
            None,
            [
                ValueScaling.create(
                    type=ValueScalingType.PROCESSING,
                    format="gdal-calc",
                    expression="numpy.clip(A / 3, 0, 1)",
                ),
                ValueScaling.create(
                    type=ValueScalingType.PROCESSING,
                    format="gdal-calc",
                    expression="numpy.clip(A / 4, 0, 1)",
                ),
                ValueScaling.create(
                    type=ValueScalingType.PROCESSING,
                    format="gdal-calc",
                    expression="numpy.clip(A / 5, 0, 1)",
                ),
            ],
        ),
    ),
)
def test_migration_1_3_to_1_4(
    norm_by_channel: bool | None,
    norm_type: str | None,
    norm_clip: list[int] | None,
    statistics: list[dict[str, Any]] | None,
    value_scaling: list[ValueScaling] | None,
) -> None:
    data: dict[str, Any] = {"properties": {"mlm:input": []}}
    MLMExtensionHooks._migrate_1_3_to_1_4(data)  # nothing is supposed to happen here

    input_obj: dict[str, Any] = {}
    if norm_by_channel is not None:
        input_obj["norm_by_channel"] = norm_by_channel
    if norm_type is not None:
        input_obj["norm_type"] = norm_type
    if norm_clip is not None:
        input_obj["norm_clip"] = norm_clip
    if statistics is not None:
        input_obj["statistics"] = statistics
    data["properties"]["mlm:input"].append(input_obj)

    MLMExtensionHooks._migrate_1_3_to_1_4(data)
    if norm_type is not None and value_scaling is not None:
        assert len(data["properties"]["mlm:input"][0]["value_scaling"]) == len(
            value_scaling
        )
        assert data["properties"]["mlm:input"][0]["value_scaling"] == [
            obj.to_dict() for obj in value_scaling
        ]

    new_input_obj = data["properties"]["mlm:input"]
    assert "norm_by_channel" not in new_input_obj
    assert "norm_type" not in new_input_obj
    assert "norm_clip" not in new_input_obj
    assert "statistics" not in new_input_obj


@pytest.mark.parametrize(
    "norm_type",
    ("l1", "l2", "l2sqr", "hamming", "hamming2", "type-mask", "relative", "inf"),
)
def test_migration_1_3_to_1_4_failure(norm_type: str) -> None:
    data: dict[str, Any] = {"properties": {"mlm:input": [{"norm_type": norm_type}]}}

    with pytest.raises(NotImplementedError):
        MLMExtensionHooks._migrate_1_3_to_1_4(data)
