import json
from pystac.item_collection import ItemCollection
from typing import cast
import unittest
import pystac

from tests.utils import TestCases


class TestItemCollection(unittest.TestCase):
    SIMPLE_ITEM = TestCases.get_path("data-files/examples/1.0.0-RC1/simple-item.json")
    CORE_ITEM = TestCases.get_path("data-files/examples/1.0.0-RC1/core-item.json")
    EXTENDED_ITEM = TestCases.get_path(
        "data-files/examples/1.0.0-RC1/extended-item.json"
    )

    ITEM_COLLECTION = TestCases.get_path(
        "data-files/item-collection/sample-item-collection.json"
    )

    def setUp(self) -> None:
        self.maxDiff = None
        with open(self.ITEM_COLLECTION) as src:
            self.item_collection_dict = json.load(src)
        self.items = [
            pystac.Item.from_dict(f) for f in self.item_collection_dict["features"]
        ]
        self.stac_io = pystac.StacIO.default()

    def test_item_collection_length(self) -> None:
        item_collection = pystac.ItemCollection(items=self.items)

        self.assertEqual(len(item_collection), len(self.items))

    def test_item_collection_iter(self) -> None:
        expected_ids = [item.id for item in self.items]
        item_collection = pystac.ItemCollection(items=self.items)

        actual_ids = [item.id for item in item_collection]

        self.assertListEqual(expected_ids, actual_ids)

    def test_item_collection_get_item_by_index(self) -> None:
        expected_id = self.items[0].id
        item_collection = pystac.ItemCollection(items=self.items)

        self.assertEqual(item_collection[0].id, expected_id)

    def test_item_collection_contains(self) -> None:
        item = pystac.Item.from_file(self.SIMPLE_ITEM)
        item_collection = pystac.ItemCollection(items=[item], clone_items=False)

        self.assertIn(item, item_collection)

    def test_item_collection_extra_fields(self) -> None:
        item_collection = pystac.ItemCollection(
            items=self.items, extra_fields={"custom_field": "My value"}
        )

        self.assertEqual(item_collection.extra_fields.get("custom_field"), "My value")

    def test_item_collection_to_dict(self) -> None:
        item_collection = pystac.ItemCollection(
            items=self.items, extra_fields={"custom_field": "My value"}
        )

        d = item_collection.to_dict()

        self.assertEqual(len(d["features"]), len(self.items))
        self.assertEqual(d.get("custom_field"), "My value")

    def test_item_collection_from_dict(self) -> None:
        features = [item.to_dict() for item in self.items]
        d = {
            "type": "FeatureCollection",
            "features": features,
            "custom_field": "My value",
        }
        item_collection = pystac.ItemCollection.from_dict(d)
        expected = len(features)
        self.assertEqual(expected, len(item_collection.items))
        self.assertEqual(item_collection.extra_fields.get("custom_field"), "My value")

    def test_item_collection_from_dict_top_level(self) -> None:
        features = [item.to_dict() for item in self.items]
        d = {
            "type": "FeatureCollection",
            "features": features,
            "custom_field": "My value",
        }
        item_collection = pystac.read_dict(d)
        item_collection = cast(pystac.ItemCollection, item_collection)
        expected = len(features)
        self.assertEqual(expected, len(item_collection.items))
        self.assertEqual(item_collection.extra_fields.get("custom_field"), "My value")

    def test_clone_item_collection(self) -> None:
        item_collection_1 = pystac.ItemCollection.from_file(self.ITEM_COLLECTION)
        item_collection_2 = item_collection_1.clone()

        item_ids_1 = [item.id for item in item_collection_1]
        item_ids_2 = [item.id for item in item_collection_2]

        # All items from the original collection should be in the clone...
        self.assertListEqual(item_ids_1, item_ids_2)
        # ... but they should not be the same objects
        self.assertIsNot(item_collection_1[0], item_collection_2[0])

    def test_raise_error_for_invalid_object(self) -> None:
        item_dict = self.stac_io.read_json(self.SIMPLE_ITEM)

        with self.assertRaises(pystac.STACTypeError):
            _ = pystac.ItemCollection.from_dict(item_dict)

    def test_from_relative_path(self) -> None:
        _ = pystac.ItemCollection.from_file(
            "./tests/data-files/item-collection/sample-item-collection.json"
        )

    def test_from_list_of_dicts(self) -> None:
        item_dict = self.stac_io.read_json(self.SIMPLE_ITEM)
        item_collection = ItemCollection(items=[item_dict])

        self.assertEqual(item_collection[0].id, item_dict.get("id"))
