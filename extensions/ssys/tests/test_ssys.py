import json
from pathlib import Path
from typing import Any, cast

import pytest

import pystac
from pystac.extensions.ssys import (
    CatalogSolSysExtension,
    ItemSolSysExtension,
    SolSysExtension,
    SolSysTargetClass,
)

DATA_FILES = Path(__file__).resolve().parent / "data-files"

EXAMPLE_ITEM = DATA_FILES / "item.json"
EXAMPLE_COLLECTION = DATA_FILES / "collection.json"
EXAMPLE_CATALOG = DATA_FILES / "catalog.json"


@pytest.fixture
def item_as_url() -> str:
    return str(EXAMPLE_ITEM)


@pytest.fixture
def item_as_dict(item_as_url: str) -> dict[str, Any]:
    with open(item_as_url) as f:
        d = json.load(f)
    return cast(dict[str, Any], d)


@pytest.fixture
def example_item(item_as_url: str) -> pystac.Item:
    return pystac.Item.from_file(item_as_url)


@pytest.fixture
def example_collection() -> pystac.Collection:
    return pystac.Collection.from_file(str(EXAMPLE_COLLECTION))


@pytest.fixture
def example_catalog() -> pystac.Catalog:
    return pystac.Catalog.from_file(str(EXAMPLE_CATALOG))


@pytest.mark.vcr()
def test_item_validate_schema(example_item: pystac.Item) -> None:
    assert example_item.validate()


def test_add_ext_to_item(sample_item: pystac.Item) -> None:
    assert not SolSysExtension.has_extension(sample_item)
    SolSysExtension.ext(sample_item, add_if_missing=True)

    assert SolSysExtension.has_extension(sample_item)
    assert SolSysExtension.get_schema_uri() in sample_item.stac_extensions

    assert isinstance(
        SolSysExtension.ext(sample_item, add_if_missing=True), ItemSolSysExtension
    )

    uris = [
        uri
        for uri in sample_item.stac_extensions
        if uri == SolSysExtension.get_schema_uri()
    ]
    assert len(uris) == 1


def test_item_with_ssys_ext(example_item: pystac.Item) -> None:
    assert SolSysExtension.has_extension(example_item)
    assert SolSysExtension.get_schema_uri() in example_item.stac_extensions

    item_ssys = SolSysExtension.ext(example_item)
    assert isinstance(item_ssys, ItemSolSysExtension)

    targets = item_ssys.targets
    target_class = item_ssys.target_class

    assert targets is not None
    assert len(targets) == 1
    assert targets[0] == "Europa"

    assert target_class is not None
    assert target_class == SolSysTargetClass.PLANET


def test_item_conversion_dict(
    example_item: pystac.Item, item_as_dict: dict[str, Any]
) -> None:
    example_as_dict = example_item.to_dict(
        include_self_link=False, transform_hrefs=False
    )
    example_properties = example_as_dict.get("properties")
    item_properties = item_as_dict.get("properties")

    assert example_properties is not None
    assert item_properties is not None

    ssys_elements = {
        k: v for k, v in example_properties.items() if k.startswith("ssys:")
    }
    assert len(ssys_elements) == 2
    assert "ssys:local_time" not in ssys_elements

    targets = ssys_elements.get("ssys:targets")
    target_class = ssys_elements.get("ssys:target_class")

    assert targets is not None
    assert len(targets) == 1
    assert targets[0] == "Europa"
    assert targets == item_properties["ssys:targets"]

    assert target_class is not None
    assert target_class == SolSysTargetClass.PLANET
    assert target_class == item_properties["ssys:target_class"]


def test_add_ext_to_catalog(example_catalog: pystac.Catalog) -> None:
    assert SolSysExtension.has_extension(example_catalog)
    SolSysExtension.ext(example_catalog)

    assert SolSysExtension.get_schema_uri() in example_catalog.stac_extensions

    uris = [
        uri
        for uri in example_catalog.stac_extensions
        if uri == SolSysExtension.get_schema_uri()
    ]
    assert len(uris) == 1

    catalog_ssys = SolSysExtension.ext(example_catalog)

    assert isinstance(
        catalog_ssys,
        CatalogSolSysExtension,
    )

    targets = catalog_ssys.targets
    assert targets is not None
    assert len(targets) == 1
    assert targets[0] == "Europa"
