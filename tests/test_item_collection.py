import json
import unittest
from copy import deepcopy
from os.path import relpath

import pytest

import pystac
from pystac.item_collection import ItemCollection
from tests.utils import TestCases
from tests.utils.stac_io_mock import MockDefaultStacIO


SIMPLE_ITEM = TestCases.get_path("data-files/examples/1.0.0-RC1/simple-item.json")
CORE_ITEM = TestCases.get_path("data-files/examples/1.0.0-RC1/core-item.json")
EXTENDED_ITEM = TestCases.get_path(
    "data-files/examples/1.0.0-RC1/extended-item.json"
)

ITEM_COLLECTION = TestCases.get_path(
    "data-files/item-collection/sample-item-collection.json"
)


@pytest.fixture
def item_collection_dict():
    with open(ITEM_COLLECTION) as src:
        return json.load(src)


@pytest.fixture
def items(item_collection_dict):
    return [pystac.Item.from_dict(f) for f in item_collection_dict["features"]]


@pytest.fixture
def stac_io():
    return pystac.StacIO.default()


def test_item_collection_length(item_collection_dict, items) -> None:
    item_collection = pystac.ItemCollection(items=items)

    assert len(item_collection) == len(items)

def test_item_collection_iter() -> None:
    expected_ids = [item.id for item in items]
    item_collection = pystac.ItemCollection(items=items)

    actual_ids = [item.id for item in item_collection]

    assert expected_ids == actual_ids

def test_item_collection_get_item_by_index() -> None:
    expected_id = items[0].id
    item_collection = pystac.ItemCollection(items=items)

    assert item_collection[0].id == expected_id

def test_item_collection_contains() -> None:
    item = pystac.Item.from_file(SIMPLE_ITEM)
    item_collection = pystac.ItemCollection(items=[item], clone_items=False)

    assert item in item_collection

def test_item_collection_extra_fields() -> None:
    item_collection = pystac.ItemCollection(
        items=items, extra_fields={"custom_field": "My value"}
    )

    assert item_collection.extra_fields.get("custom_field") == "My value"

def test_item_collection_to_dict() -> None:
    item_collection = pystac.ItemCollection(
        items=items, extra_fields={"custom_field": "My value"}
    )

    d = item_collection.to_dict()

    assert len(d["features"]) == len(items)
    assert d.get("custom_field") == "My value"

def test_item_collection_from_dict() -> None:
    features = [item.to_dict(transform_hrefs=False) for item in items]
    d = {
        "type": "FeatureCollection",
        "features": features,
        "custom_field": "My value",
    }
    item_collection = pystac.ItemCollection.from_dict(d)
    expected = len(features)
    assert expected == len(item_collection.items)
    assert item_collection.extra_fields.get("custom_field") == "My value"

def test_clone_item_collection() -> None:
    item_collection_1 = pystac.ItemCollection.from_file(ITEM_COLLECTION)
    item_collection_2 = item_collection_1.clone()

    item_ids_1 = [item.id for item in item_collection_1]
    item_ids_2 = [item.id for item in item_collection_2]

    # All items from the original collection should be in the clone...
    assert item_ids_1 == item_ids_2
    # ... but they should not be the same objects
    assert item_collection_1[0] is not item_collection_2[0]

def test_raise_error_for_invalid_object() -> None:
    item_dict = stac_io.read_json(SIMPLE_ITEM)

    with pytest.raises(pystac.STACTypeError):
        _ = pystac.ItemCollection.from_dict(item_dict)

def test_from_relative_path() -> None:
    _ = pystac.ItemCollection.from_file(
        relpath(
            TestCases.get_path(
                "data-files/item-collection/sample-item-collection.json"
            )
        )
    )

def test_from_list_of_dicts() -> None:
    item_dict = stac_io.read_json(SIMPLE_ITEM)
    item_collection = pystac.ItemCollection(items=[item_dict], clone_items=True)

    assert item_collection[0].id == item_dict.get("id")

def test_add_item_collections() -> None:
    item_1 = pystac.Item.from_file(SIMPLE_ITEM)
    item_2 = pystac.Item.from_file(EXTENDED_ITEM)
    item_3 = pystac.Item.from_file(CORE_ITEM)

    item_collection_1 = pystac.ItemCollection(items=[item_1, item_2])
    item_collection_2 = pystac.ItemCollection(items=[item_2, item_3])

    combined = item_collection_1 + item_collection_2

    assert len(combined) == 4

def test_add_other_raises_error() -> None:
    item_collection = pystac.ItemCollection.from_file(ITEM_COLLECTION)

    with pytest.raises(TypeError):
        _ = item_collection + 2

def test_identify_0_8_itemcollection_type() -> None:
    itemcollection_path = TestCases.get_path(
        "data-files/examples/0.8.1/item-spec/"
        "examples/itemcollection-sample-full.json"
    )
    itemcollection_dict = pystac.StacIO.default().read_json(itemcollection_path)

    assert pystac.ItemCollection.is_item_collection(itemcollection_dict), \
        "Did not correctly identify valid STAC 0.8 ItemCollection."

def test_identify_0_9_itemcollection() -> None:
    itemcollection_path = TestCases.get_path(
        "data-files/examples/0.9.0/item-spec/"
        "examples/itemcollection-sample-full.json"
    )
    itemcollection_dict = pystac.StacIO.default().read_json(itemcollection_path)

    assert pystac.ItemCollection.is_item_collection(itemcollection_dict), \
        "Did not correctly identify valid STAC 0.9 ItemCollection."

def test_from_dict_preserves_dict() -> None:
    param_dict = deepcopy(item_collection_dict)

    # test that the parameter is preserved
    _ = ItemCollection.from_dict(param_dict)
    assert param_dict == item_collection_dict

    # assert that the parameter is preserved regardless of
    # preserve_dict
    _ = ItemCollection.from_dict(param_dict, preserve_dict=False)
    assert param_dict == item_collection_dict

def test_from_dict_sets_root() -> None:
    param_dict = deepcopy(item_collection_dict)
    catalog = pystac.Catalog(id="test", description="test desc")
    item_collection = ItemCollection.from_dict(param_dict, root=catalog)
    for item in item_collection.items:
        assert item.get_root() == catalog

def test_to_dict_does_not_read_root_link_of_items() -> None:
    with MockDefaultStacIO() as mock_stac_io:
        item_collection = pystac.ItemCollection.from_file(ITEM_COLLECTION)

        item_collection.to_dict()

        assert mock_stac_io.mock.read_text.call_count == 1
