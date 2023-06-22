"""Tests for pystac.tests.extensions.mgrs"""
import json

import pytest

import pystac
from pystac.extensions.mgrs import MgrsExtension
from tests.conftest import get_data_file


@pytest.fixture
def ext_item_uri() -> str:
    return get_data_file("mgrs/item.json")


@pytest.fixture
def ext_item(ext_item_uri: str) -> pystac.Item:
    return pystac.Item.from_file(ext_item_uri)


def test_stac_extensions(ext_item: pystac.Item) -> None:
    assert MgrsExtension.has_extension(ext_item)


def test_get_schema_uri(ext_item: pystac.Item) -> None:
    assert MgrsExtension.get_schema_uri() in ext_item.stac_extensions


def test_ext_raises_if_item_does_not_conform(item: pystac.Item) -> None:
    with pytest.raises(pystac.errors.ExtensionNotImplemented):
        MgrsExtension.ext(item)


def test_ext_raises_on_collection(collection: pystac.Collection) -> None:
    with pytest.raises(
        pystac.errors.ExtensionTypeError,
        match="MgrsExtension does not apply to type 'Collection'",
    ) as e:
        MgrsExtension.ext(collection)  # type: ignore
    assert "Hint" not in str(e.value)


def test_to_from_dict(ext_item_uri: str, ext_item: pystac.Item) -> None:
    with open(ext_item_uri) as f:
        d = json.load(f)
    actual = ext_item.to_dict(include_self_link=False)
    assert actual == d


def test_add_to(item: pystac.Item) -> None:
    assert not MgrsExtension.has_extension(item)
    MgrsExtension.add_to(item)

    assert MgrsExtension.has_extension(item)


def test_apply(item: pystac.Item) -> None:
    MgrsExtension.add_to(item)
    MgrsExtension.ext(item).apply(latitude_band="X", grid_square="DH")
    assert MgrsExtension.ext(item).latitude_band
    assert MgrsExtension.ext(item).grid_square


def test_apply_without_required_fields_raises(item: pystac.Item) -> None:
    MgrsExtension.add_to(item)
    with pytest.raises(TypeError, match="missing 2 required positional arguments"):
        MgrsExtension.ext(item).apply()  # type: ignore


@pytest.mark.vcr()
def test_validate(ext_item: pystac.Item) -> None:
    assert ext_item.validate()


@pytest.mark.parametrize("field", ["latitude_band", "grid_square", "utm_zone"])
def test_get_field(ext_item: pystac.Item, field: str) -> None:
    prop = ext_item.properties[f"mgrs:{field}"]
    attr = getattr(MgrsExtension.ext(ext_item), field)

    assert attr is not None
    assert attr == prop


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "field,value",
    [
        ("latitude_band", "C"),
        ("grid_square", "ZA"),
        ("utm_zone", 59),
    ],
)
def test_set_field(ext_item: pystac.Item, field: str, value) -> None:  # type: ignore
    original = ext_item.properties[f"mgrs:{field}"]
    setattr(MgrsExtension.ext(ext_item), field, value)
    new = ext_item.properties[f"mgrs:{field}"]

    assert new != original
    assert new == value
    assert ext_item.validate()


def test_utm_zone_set_to_none_pops_from_dict(ext_item: pystac.Item) -> None:
    assert "mgrs:utm_zone" in ext_item.properties

    MgrsExtension.ext(ext_item).utm_zone = None
    assert "mgrs:utm_zone" not in ext_item.properties


def test_invalid_latitude_band_raises_informative_error(ext_item: pystac.Item) -> None:
    with pytest.raises(ValueError, match="must be str"):
        MgrsExtension.ext(ext_item).latitude_band = 2  # type: ignore

    with pytest.raises(ValueError, match="must be str"):
        MgrsExtension.ext(ext_item).latitude_band = None

    with pytest.raises(ValueError, match="a is not in "):
        MgrsExtension.ext(ext_item).latitude_band = "a"


def test_invalid_grid_square_raises_informative_error(ext_item: pystac.Item) -> None:
    with pytest.raises(ValueError, match="must be str"):
        MgrsExtension.ext(ext_item).grid_square = 2  # type: ignore

    with pytest.raises(ValueError, match="must be str"):
        MgrsExtension.ext(ext_item).grid_square = None

    with pytest.raises(ValueError, match="nv does not match the regex "):
        MgrsExtension.ext(ext_item).grid_square = "nv"


def test_invalid_utm_zone_raises_informative_error(ext_item: pystac.Item) -> None:
    with pytest.raises(ValueError, match="must be None or int"):
        MgrsExtension.ext(ext_item).utm_zone = "foo"  # type: ignore

    with pytest.raises(ValueError, match="61 is not in "):
        MgrsExtension.ext(ext_item).utm_zone = 61
