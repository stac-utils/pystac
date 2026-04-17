import json
from pathlib import Path

import pytest
from pytest_pystac.plugin import assert_to_from_dict

import pystac
from pystac import ExtensionTypeError, Item
from pystac.errors import ExtensionNotImplemented
from pystac.extensions.cf import CF_EXTENSION_HOOKS, PARAMETER_PROP, CFExtension, Parameter

DATA_FILES = Path(__file__).resolve().parent / "data-files"

SAMPLE_ITEM_URI = str(DATA_FILES / "item/sample-item.json")


@pytest.fixture
def cf_item() -> Item:
    return Item.from_file(SAMPLE_ITEM_URI)


def test_parameter_create() -> None:
    param = Parameter(name="air_temperature", unit="K")
    assert param.name == "air_temperature"
    assert param.unit == "K"


def test_parameter_create_no_unit() -> None:
    param = Parameter(name="wind_speed")
    assert param.name == "wind_speed"
    assert param.unit is None


def test_parameter_eq() -> None:
    p1 = Parameter(name="air_temperature", unit="K")
    p2 = Parameter(name="air_temperature", unit="K")
    p3 = Parameter(name="air_temperature", unit="degC")
    assert p1 == p2
    assert p1 != p3


def test_parameter_repr() -> None:
    param = Parameter(name="air_temperature", unit="K")
    assert repr(param) == "<Parameter name=air_temperature unit=K>"


def test_parameter_to_dict() -> None:
    param = Parameter(name="air_temperature", unit="K")
    d = param.to_dict()
    assert d == {"name": "air_temperature", "unit": "K"}


def test_parameter_from_dict() -> None:
    d = {"name": "air_temperature", "unit": "K"}
    param = Parameter.from_dict(d)
    assert param.name == "air_temperature"
    assert param.unit == "K"


def test_parameter_from_dict_no_unit() -> None:
    d = {"name": "wind_speed"}
    param = Parameter.from_dict(d)
    assert param.name == "wind_speed"
    assert param.unit is None


def test_parameter_from_dict_missing_name() -> None:
    with pytest.raises(ValueError, match="'name' must be a non-empty string"):
        Parameter.from_dict({})


def test_to_from_dict() -> None:
    with open(SAMPLE_ITEM_URI) as f:
        item_dict = json.load(f)
    assert_to_from_dict(Item, item_dict)


def test_add_to(sample_item: Item) -> None:
    assert CFExtension.get_schema_uri() not in sample_item.stac_extensions
    CFExtension.add_to(sample_item)
    assert CFExtension.get_schema_uri() in sample_item.stac_extensions

    # Adding multiple times should only add the URI once
    CFExtension.add_to(sample_item)
    uris = [u for u in sample_item.stac_extensions if u == CFExtension.get_schema_uri()]
    assert len(uris) == 1


def test_extension_not_implemented(sample_item: Item) -> None:
    with pytest.raises(ExtensionNotImplemented):
        _ = CFExtension.ext(sample_item)

    asset = sample_item.assets["thumbnail"]
    with pytest.raises(ExtensionNotImplemented):
        _ = CFExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = CFExtension.ext(ownerless_asset)


def test_extend_invalid_object() -> None:
    link = pystac.Link("child", "https://example.com/item.json")
    with pytest.raises(ExtensionTypeError):
        CFExtension.ext(link)  # type: ignore


def test_item_ext_add_to(sample_item: Item) -> None:
    assert CFExtension.get_schema_uri() not in sample_item.stac_extensions
    _ = CFExtension.ext(sample_item, add_if_missing=True)
    assert CFExtension.get_schema_uri() in sample_item.stac_extensions


def test_asset_ext_add_to(sample_item: Item) -> None:
    assert CFExtension.get_schema_uri() not in sample_item.stac_extensions
    asset = sample_item.assets["thumbnail"]
    _ = CFExtension.ext(asset, add_if_missing=True)
    assert CFExtension.get_schema_uri() in sample_item.stac_extensions


def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError, match=r"^CFExtension does not apply to type 'object'$"
    ):
        CFExtension.ext(object())  # type: ignore


def test_parameters_get(cf_item: Item) -> None:
    cf_ext = CFExtension.ext(cf_item)
    params = cf_ext.parameters
    assert params is not None
    assert len(params) == 1
    assert params[0].name == "air_temperature"
    assert params[0].unit == "K"


def test_parameters_set(cf_item: Item) -> None:
    cf_ext = CFExtension.ext(cf_item)

    new_params = [Parameter(name="wind_speed", unit="m s-1")]
    cf_ext.parameters = new_params

    assert cf_ext.parameters == new_params
    assert cf_item.properties[PARAMETER_PROP] == [{"name": "wind_speed", "unit": "m s-1"}]


def test_parameters_set_none(cf_item: Item) -> None:
    cf_ext = CFExtension.ext(cf_item)
    cf_ext.parameters = None
    assert PARAMETER_PROP not in cf_item.properties


def test_apply(cf_item: Item) -> None:
    cf_ext = CFExtension.ext(cf_item)
    new_params = [
        Parameter(name="sea_surface_temperature", unit="K"),
        Parameter(name="sea_ice_area_fraction"),
    ]
    cf_ext.apply(parameters=new_params)

    assert cf_ext.parameters == new_params


def test_asset_parameters(cf_item: Item) -> None:
    asset = cf_item.assets["data"]
    cf_ext = CFExtension.ext(asset)
    params = cf_ext.parameters
    assert params is not None
    assert len(params) == 1
    assert params[0].name == "air_temperature"

    # Set new value and verify
    new_params = [Parameter(name="precipitation_flux", unit="kg m-2 s-1")]
    cf_ext.parameters = new_params
    assert cf_ext.parameters == new_params


def test_extension_hooks_schema_uri() -> None:
    assert CF_EXTENSION_HOOKS.schema_uri == CFExtension.get_schema_uri()
