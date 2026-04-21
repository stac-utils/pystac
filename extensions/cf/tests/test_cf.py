import json
from pathlib import Path

import pytest
from pytest_pystac.plugin import assert_to_from_dict

import pystac
from pystac import Collection, ExtensionTypeError, Item
from pystac.errors import ExtensionNotImplemented
from pystac.extensions.cf import CF_EXTENSION_HOOKS, PARAMETER_PROP, CFExtension, Parameter

DATA_FILES = Path(__file__).resolve().parent / "data-files"

SAMPLE_ITEM_URI = str(DATA_FILES / "item/sample-item.json")
SAMPLE_COLLECTION_URI = str(DATA_FILES / "cf-collection.json")


@pytest.fixture
def cf_item() -> Item:
    return Item.from_file(SAMPLE_ITEM_URI)


@pytest.fixture
def cf_collection() -> Collection:
    return Collection.from_file(SAMPLE_COLLECTION_URI)


# --- Parameter ---


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


def test_parameter_eq_non_parameter() -> None:
    param = Parameter(name="air_temperature", unit="K")
    assert param.__eq__(object()) is NotImplemented


def test_parameter_repr() -> None:
    param = Parameter(name="air_temperature", unit="K")
    assert repr(param) == "<Parameter name=air_temperature unit=K>"


def test_parameter_to_dict() -> None:
    param = Parameter(name="air_temperature", unit="K")
    assert param.to_dict() == {"name": "air_temperature", "unit": "K"}


def test_parameter_to_dict_no_unit() -> None:
    param = Parameter(name="wind_speed")
    assert param.to_dict() == {"name": "wind_speed", "unit": None}


def test_parameter_from_dict() -> None:
    param = Parameter.from_dict({"name": "air_temperature", "unit": "K"})
    assert param.name == "air_temperature"
    assert param.unit == "K"


def test_parameter_from_dict_no_unit() -> None:
    param = Parameter.from_dict({"name": "wind_speed"})
    assert param.name == "wind_speed"
    assert param.unit is None


def test_parameter_from_dict_missing_name() -> None:
    with pytest.raises(ValueError, match="'name' must be a non-empty string"):
        Parameter.from_dict({})


# --- Extension management ---


def test_to_from_dict() -> None:
    with open(SAMPLE_ITEM_URI) as f:
        item_dict = json.load(f)
    assert_to_from_dict(Item, item_dict)


def test_add_to(sample_item: Item) -> None:
    assert CFExtension.get_schema_uri() not in sample_item.stac_extensions
    CFExtension.add_to(sample_item)
    assert CFExtension.get_schema_uri() in sample_item.stac_extensions
    n = len(sample_item.stac_extensions)

    # Adding multiple times should only add the URI once
    CFExtension.add_to(sample_item)
    assert len(sample_item.stac_extensions) == n


def test_extension_not_implemented(sample_item: Item) -> None:
    with pytest.raises(ExtensionNotImplemented):
        CFExtension.ext(sample_item)

    # Asset whose owner lacks the extension also raises
    owned_asset = pystac.Asset(href="https://example.com/data.nc")
    owned_asset.owner = sample_item
    with pytest.raises(ExtensionNotImplemented):
        CFExtension.ext(owned_asset)

    # Asset with no owner succeeds
    ownerless_asset = pystac.Asset(href="https://example.com/data.nc")
    CFExtension.ext(ownerless_asset)


def test_item_ext_add_to(sample_item: Item) -> None:
    assert CFExtension.get_schema_uri() not in sample_item.stac_extensions
    CFExtension.ext(sample_item, add_if_missing=True)
    assert CFExtension.get_schema_uri() in sample_item.stac_extensions


def test_asset_ext_add_to(sample_item: Item) -> None:
    assert CFExtension.get_schema_uri() not in sample_item.stac_extensions
    asset = pystac.Asset(href="https://example.com/data.nc")
    asset.owner = sample_item
    CFExtension.ext(asset, add_if_missing=True)
    assert CFExtension.get_schema_uri() in sample_item.stac_extensions


def test_ext_invalid_type() -> None:
    with pytest.raises(
        ExtensionTypeError, match=r"^CFExtension does not apply to type 'object'$"
    ):
        CFExtension.ext(object())  # type: ignore


# --- Item extension ---


def test_parameters_get(cf_item: Item) -> None:
    cf_ext = CFExtension.ext(cf_item)
    assert cf_ext.parameters == [Parameter(name="air_temperature", unit="K")]


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


def test_item_ext_repr(cf_item: Item) -> None:
    cf_ext = CFExtension.ext(cf_item)
    assert repr(cf_ext) == f"<ItemCFExtension Item id={cf_item.id}>"


# --- Asset extension ---


def test_asset_parameters_get(cf_item: Item) -> None:
    asset = cf_item.assets["data"]
    cf_ext = CFExtension.ext(asset)
    assert cf_ext.parameters == [Parameter(name="air_temperature", unit="K")]


def test_asset_parameters_set(cf_item: Item) -> None:
    asset = cf_item.assets["data"]
    cf_ext = CFExtension.ext(asset)
    new_params = [Parameter(name="precipitation_flux", unit="kg m-2 s-1")]
    cf_ext.parameters = new_params
    assert cf_ext.parameters == new_params


def test_asset_ext_repr(cf_item: Item) -> None:
    asset = cf_item.assets["data"]
    cf_ext = CFExtension.ext(asset)
    assert repr(cf_ext) == f"<AssetCFExtension Asset href={asset.href}>"


# --- Collection extension ---


def test_collection_ext(cf_collection: Collection) -> None:
    cf_ext = CFExtension.ext(cf_collection)
    assert repr(cf_ext) == f"<CollectionCFExtension Collection id={cf_collection.id}>"


def test_collection_parameters_get(cf_collection: Collection) -> None:
    cf_ext = CFExtension.ext(cf_collection)
    assert cf_ext.parameters == [Parameter(name="air_temperature", unit="K")]


def test_collection_parameters_set(cf_collection: Collection) -> None:
    cf_ext = CFExtension.ext(cf_collection)
    new_params = [Parameter(name="sea_surface_temperature", unit="K")]
    cf_ext.parameters = new_params
    assert cf_ext.parameters == new_params
    assert cf_collection.extra_fields[PARAMETER_PROP] == [
        {"name": "sea_surface_temperature", "unit": "K"}
    ]


# --- ItemAssetDefinition extension ---


def test_item_assets_ext() -> None:
    item_asset = pystac.ItemAssetDefinition(
        properties={
            "title": "data",
            "type": "application/x-netcdf",
            PARAMETER_PROP: [{"name": "air_temperature", "unit": "K"}],
        }
    )
    cf_ext = CFExtension.ext(item_asset)
    assert cf_ext.parameters == [Parameter(name="air_temperature", unit="K")]


def test_item_assets_ext_set() -> None:
    item_asset = pystac.ItemAssetDefinition(properties={"title": "data"})
    cf_ext = CFExtension.ext(item_asset)
    new_params = [Parameter(name="wind_speed", unit="m s-1")]
    cf_ext.parameters = new_params
    assert cf_ext.parameters == new_params


# --- Extension hooks ---


def test_extension_hooks() -> None:
    assert CF_EXTENSION_HOOKS.schema_uri == CFExtension.get_schema_uri()
    assert pystac.STACObjectType.COLLECTION in CF_EXTENSION_HOOKS.stac_object_types
    assert pystac.STACObjectType.ITEM in CF_EXTENSION_HOOKS.stac_object_types
