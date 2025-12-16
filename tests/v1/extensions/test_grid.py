"""Tests for pystac.extensions.grid."""

# This is for the type checking on GridTest.test_clear_code
# mypy: warn_unused_ignores=False

from datetime import datetime
from typing import Any

import pytest

import pystac
from pystac import ExtensionTypeError
from pystac.extensions import grid
from pystac.extensions.grid import GridExtension
from tests.v1.conftest import get_data_file
from tests.v1.utils import TestCases

code = "MGRS-4CFJ"


@pytest.fixture
def sentinel2_example_item() -> pystac.Item:
    return pystac.Item.from_file(
        TestCases.get_path("data-files/grid/example-sentinel2.json")
    )


@pytest.fixture
def item() -> pystac.Item:
    """Create basic test items that are only slightly different."""
    asset_id = "an/asset"
    start = datetime(2018, 1, 2)
    item = pystac.Item(
        id=asset_id, geometry=None, bbox=None, datetime=start, properties={}
    )

    GridExtension.add_to(item)
    return item


def test_stac_extensions(item: pystac.Item) -> None:
    assert GridExtension.has_extension(item)


def test_item_repr(item: pystac.Item) -> None:
    grid_item_ext = GridExtension.ext(item)
    assert f"<ItemGridExtension Item id={item.id}>" == grid_item_ext.__repr__()


@pytest.mark.vcr()
def test_attributes(item: pystac.Item) -> None:
    GridExtension.ext(item).apply(code)
    assert code == GridExtension.ext(item).code
    item.validate()


def test_invalid_code_value(item: pystac.Item) -> None:
    with pytest.raises(ValueError):
        GridExtension.ext(item).apply("not_a_valid_code")


@pytest.mark.vcr()
def test_modify(item: pystac.Item) -> None:
    GridExtension.ext(item).apply(code)
    GridExtension.ext(item).apply(code + "a")
    assert code + "a" == GridExtension.ext(item).code
    item.validate()


def test_from_dict() -> None:
    d: dict[str, Any] = {
        "type": "Feature",
        "stac_version": "1.1.0",
        "id": "an/asset",
        "properties": {
            "grid:code": code,
            "datetime": "2018-01-02T00:00:00Z",
        },
        "geometry": None,
        "links": [],
        "assets": {},
        "stac_extensions": [GridExtension.get_schema_uri()],
    }
    item = pystac.Item.from_dict(d)
    assert code == GridExtension.ext(item).code


def test_to_from_dict(item: pystac.Item) -> None:
    GridExtension.ext(item).apply(code)
    d = item.to_dict()
    assert code == d["properties"][grid.CODE_PROP]

    item = pystac.Item.from_dict(d)
    assert code == GridExtension.ext(item).code


def test_clear_code(item: pystac.Item) -> None:
    GridExtension.ext(item).apply(code)

    with pytest.raises(ValueError):
        # Ignore type errors because this test intentionally checks behavior
        # that does not conform to the type signature.
        # https://github.com/stac-utils/pystac/pull/878#discussion_r957352232
        GridExtension.ext(item).code = None  # type: ignore
    with pytest.raises(ValueError):
        # First segment has to be all caps
        # https://github.com/stac-utils/pystac/pull/878#discussion_r957354927
        GridExtension.ext(item).code = "this-is-not-a-grid-code"
    with pytest.raises(ValueError):
        # Folks might try to put an epsg code in
        # https://github.com/stac-utils/pystac/pull/878#discussion_r957355415
        GridExtension.ext(item).code = "4326"
    with pytest.raises(ValueError):
        # Folks might try to put an epsg code in
        # https://github.com/stac-utils/pystac/pull/878#discussion_r957355415
        GridExtension.ext(item).code = "EPSG:4326"


def test_extension_not_implemented(sentinel2_example_item: pystac.Item) -> None:
    # Should raise exception if Item does not include extension URI
    item = sentinel2_example_item
    item.stac_extensions.remove(GridExtension.get_schema_uri())

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = GridExtension.ext(item)

    # Should raise exception if owning Item does not include extension URI
    item.properties["grid:code"] = None

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = GridExtension.ext(item)


def test_item_ext_add_to(sentinel2_example_item: pystac.Item) -> None:
    item = sentinel2_example_item
    item.stac_extensions.remove(GridExtension.get_schema_uri())
    assert GridExtension.get_schema_uri() not in item.stac_extensions

    _ = GridExtension.ext(item, add_if_missing=True)

    assert GridExtension.get_schema_uri() in item.stac_extensions


def test_should_raise_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError, match=r"^GridExtension does not apply to type 'object'$"
    ):
        # intentionally calling it wrong so tell mypy to ignore this line:
        GridExtension.ext(object())  # type: ignore


@pytest.fixture
def ext_item() -> pystac.Item:
    ext_item_uri = get_data_file("grid/example-sentinel2.json")
    return pystac.Item.from_file(ext_item_uri)


def test_older_extension_version(ext_item: pystac.Item) -> None:
    old = "https://stac-extensions.github.io/grid/v1.0.0/schema.json"
    new = "https://stac-extensions.github.io/grid/v1.1.0/schema.json"

    stac_extensions = set(ext_item.stac_extensions)
    stac_extensions.remove(new)
    stac_extensions.add(old)
    item_as_dict = ext_item.to_dict(include_self_link=False, transform_hrefs=False)
    item_as_dict["stac_extensions"] = list(stac_extensions)
    item = pystac.Item.from_dict(item_as_dict, migrate=False)
    assert GridExtension.has_extension(item)
    assert old in item.stac_extensions

    migrated_item = pystac.Item.from_dict(item_as_dict, migrate=True)
    assert GridExtension.has_extension(migrated_item)
    assert new in migrated_item.stac_extensions
