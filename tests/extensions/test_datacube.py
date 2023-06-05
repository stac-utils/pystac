"""Tests for pystac.tests.extensions.datacube"""
import json
from typing import Any

import pytest

import pystac
import pystac.extensions.datacube as dc
from pystac.errors import ExtensionTypeError
from tests.conftest import get_data_file


@pytest.fixture
def ext_item_uri() -> str:
    return get_data_file("datacube/item.json")


@pytest.fixture
def ext_item(ext_item_uri: str) -> pystac.Item:
    return pystac.Item.from_file(ext_item_uri)


@pytest.fixture
def horizontal_dimension(ext_item: pystac.Item) -> dc.Dimension:
    return dc.DatacubeExtension.ext(ext_item).dimensions["x"]


@pytest.fixture
def temporal_dimension(ext_item: pystac.Item) -> dc.Dimension:
    return dc.DatacubeExtension.ext(ext_item).dimensions["time"]


@pytest.fixture
def additional_dimension(ext_item: pystac.Item) -> dc.Dimension:
    return dc.DatacubeExtension.ext(ext_item).dimensions["spectral"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("axis", "y"),
        ("extent", [-102, -120]),
        ("reference_system", 100),
    ],
)
def test_horizontal_dimension_fields(
    horizontal_dimension: dc.Dimension, field: str, value: Any
) -> None:
    dim = horizontal_dimension
    original = dim.properties[field]
    assert original == getattr(dim, field)

    setattr(dim, field, value)
    new = dim.properties[field]

    assert new != original
    assert new == value


def test_horizontal_dimension_values(
    horizontal_dimension: dc.HorizontalSpatialDimension,
) -> None:
    dim = horizontal_dimension
    assert dim.values is None

    dim.values = [0, 180]
    assert dim.values == [0, 180]
    assert dim.properties["values"] == [0, 180]

    dim.clear_step()
    assert dim.step is None
    assert "step" not in dim.properties


def test_horizontal_dimension_step(
    horizontal_dimension: dc.HorizontalSpatialDimension,
) -> None:
    dim = horizontal_dimension
    assert dim.step is None

    dim.step = 3
    assert dim.step == 3
    assert dim.properties["step"] == 3

    dim.values = None
    assert dim.values is None
    assert "values" not in dim.properties


def test_temporal_dimension_type(temporal_dimension: dc.TemporalDimension) -> None:
    assert isinstance(temporal_dimension, dc.TemporalDimension)
    assert temporal_dimension.dim_type == "temporal"

    temporal_dimension.dim_type = "foo"
    assert temporal_dimension.dim_type == "foo"


def test_temporal_dimension_description(
    temporal_dimension: dc.TemporalDimension,
) -> None:
    assert temporal_dimension.description is None
    value = "Dimension in time"

    temporal_dimension.description = value
    assert temporal_dimension.properties["description"] == value

    temporal_dimension.description = None
    assert "description" not in temporal_dimension.properties


def test_stac_extensions(ext_item: pystac.Item) -> None:
    assert dc.DatacubeExtension.has_extension(ext_item)


def test_get_schema_uri(ext_item: pystac.Item) -> None:
    assert dc.DatacubeExtension.get_schema_uri() in ext_item.stac_extensions


def test_ext_raises_if_item_does_not_conform(item: pystac.Item) -> None:
    with pytest.raises(pystac.errors.ExtensionNotImplemented):
        dc.DatacubeExtension.ext(item)


def test_ext_raises_if_asset_does_not_conform(sample_item: pystac.Item) -> None:
    asset = sample_item.assets["analytic"]
    with pytest.raises(pystac.errors.ExtensionNotImplemented):
        dc.DatacubeExtension.ext(asset)


def test_ext_always_passes_if_asset_has_no_owner(sample_item: pystac.Item) -> None:
    asset = sample_item.assets["analytic"]

    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    dc.DatacubeExtension.ext(ownerless_asset)


def test_ext_raises_if_passed_a_non_stac_object() -> None:
    with pytest.raises(
        ExtensionTypeError, match="Datacube extension does not apply to type 'object'"
    ):
        dc.DatacubeExtension.ext(object())  # type: ignore


def test_to_from_dict(ext_item_uri: str, ext_item: pystac.Item) -> None:
    with open(ext_item_uri) as f:
        d = json.load(f)
    actual = ext_item.to_dict(include_self_link=False)
    assert d.keys() == actual.keys()
    for k, v in d.items():
        if k not in ["links"]:
            assert actual[k] == v


def test_add_to_collection(collection: pystac.Collection) -> None:
    assert not dc.DatacubeExtension.has_extension(collection)
    dc.DatacubeExtension.add_to(collection)

    assert dc.DatacubeExtension.has_extension(collection)
    assert dc.DatacubeExtension.get_schema_uri() in collection.stac_extensions


def test_add_ext_to_collection(collection: pystac.Collection) -> None:
    assert not dc.DatacubeExtension.has_extension(collection)
    dc.DatacubeExtension.ext(collection, add_if_missing=True)

    assert dc.DatacubeExtension.has_extension(collection)
    assert dc.DatacubeExtension.get_schema_uri() in collection.stac_extensions


def test_add_to_item(item: pystac.Item) -> None:
    assert not dc.DatacubeExtension.has_extension(item)
    dc.DatacubeExtension.add_to(item)

    assert dc.DatacubeExtension.has_extension(item)
    assert dc.DatacubeExtension.get_schema_uri() in item.stac_extensions


def test_add_ext_to_item(item: pystac.Item) -> None:
    assert not dc.DatacubeExtension.has_extension(item)
    dc.DatacubeExtension.ext(item, add_if_missing=True)

    assert dc.DatacubeExtension.has_extension(item)
    assert dc.DatacubeExtension.get_schema_uri() in item.stac_extensions


def test_add_ext_to_asset(sample_item: pystac.Item) -> None:
    assert not dc.DatacubeExtension.has_extension(sample_item)
    asset = sample_item.assets["analytic"]
    dc.DatacubeExtension.ext(asset, add_if_missing=True)

    assert dc.DatacubeExtension.has_extension(sample_item)
    assert dc.DatacubeExtension.get_schema_uri() in sample_item.stac_extensions


def test_apply(item: pystac.Item) -> None:
    dc.DatacubeExtension.add_to(item)
    dc.DatacubeExtension.ext(item).apply(
        dimensions={
            "time": dc.Dimension.from_dict(
                {"type": "temporal", "values": ["2016-05-03T13:21:30.040Z"]}
            ),
        },
        variables={
            "temp": dc.Variable.from_dict(
                {
                    "dimensions": [
                        "time",
                    ],
                }
            ),
        },
    )
    assert dc.DatacubeExtension.ext(item).dimensions
    assert dc.DatacubeExtension.ext(item).variables


def test_apply_without_required_fields_raises(item: pystac.Item) -> None:
    dc.DatacubeExtension.add_to(item)
    with pytest.raises(TypeError, match="missing 1 required positional argument"):
        dc.DatacubeExtension.ext(item).apply()  # type: ignore


def test_validate(ext_item: pystac.Item) -> None:
    assert ext_item.validate()


def test_get_variables(ext_item: pystac.Item) -> None:
    prop = ext_item.properties[dc.VARIABLES_PROP]
    attr = dc.DatacubeExtension.ext(ext_item).variables

    assert attr is not None
    assert isinstance(attr["temp"], dc.Variable)
    assert attr["temp"].to_dict() == prop["temp"]


def test_get_dimensions(ext_item: pystac.Item) -> None:
    prop = ext_item.properties[dc.DIMENSIONS_PROP]
    attr = dc.DatacubeExtension.ext(ext_item).dimensions

    assert attr is not None
    assert isinstance(attr["spectral"], dc.Dimension)
    assert attr["spectral"].to_dict() == prop["spectral"]
    assert attr["x"].to_dict() == prop["x"]


def test_set_variables(ext_item: pystac.Item) -> None:
    original = ext_item.properties[dc.VARIABLES_PROP]
    value = dc.Variable({"dimensions": ["foo"]})

    dc.DatacubeExtension.ext(ext_item).variables = {"temp": value}
    new = ext_item.properties[dc.VARIABLES_PROP]

    assert new != original
    assert new == {"temp": value.to_dict()}
    assert ext_item.validate()


def test_set_dimensions(ext_item: pystac.Item) -> None:
    original = ext_item.properties[dc.DIMENSIONS_PROP]
    value = dc.Dimension(
        {"type": "bands", "values": ["red", "coastal", "green", "blue"]}
    )

    dc.DatacubeExtension.ext(ext_item).dimensions = {"spectral": value}
    new = ext_item.properties[dc.DIMENSIONS_PROP]

    assert new != original
    assert new == {"spectral": value.to_dict()}
    assert ext_item.validate()
