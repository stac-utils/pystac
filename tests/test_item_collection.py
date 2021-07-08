from copy import deepcopy
import json
from pystac.item_collection import ItemCollection
import unittest
from os.path import relpath

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
        item_collection = pystac.ItemCollection(items=[item])

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
            relpath(
                TestCases.get_path(
                    "data-files/item-collection/sample-item-collection.json"
                )
            )
        )

    def test_from_list_of_dicts(self) -> None:
        item_dict = self.stac_io.read_json(self.SIMPLE_ITEM)
        item_collection = pystac.ItemCollection(items=[item_dict])

        self.assertEqual(item_collection[0].id, item_dict.get("id"))

    def test_add_item_collections(self) -> None:
        item_1 = pystac.Item.from_file(self.SIMPLE_ITEM)
        item_2 = pystac.Item.from_file(self.EXTENDED_ITEM)
        item_3 = pystac.Item.from_file(self.CORE_ITEM)

        item_collection_1 = pystac.ItemCollection(items=[item_1, item_2])
        item_collection_2 = pystac.ItemCollection(items=[item_2, item_3])

        combined = item_collection_1 + item_collection_2

        self.assertEqual(len(combined), 3)

    def test_add_other_raises_error(self) -> None:
        item_collection = pystac.ItemCollection.from_file(self.ITEM_COLLECTION)

        with self.assertRaises(TypeError):
            _ = item_collection + 2

    def test_identify_0_8_itemcollection_type(self) -> None:
        itemcollection_path = TestCases.get_path(
            "data-files/examples/0.8.1/item-spec/"
            "examples/itemcollection-sample-full.json"
        )
        itemcollection_dict = pystac.StacIO.default().read_json(itemcollection_path)

        self.assertTrue(
            pystac.ItemCollection.is_item_collection(itemcollection_dict),
            msg="Did not correctly identify valid STAC 0.8 ItemCollection.",
        )

    def test_identify_0_9_itemcollection(self) -> None:
        itemcollection_path = TestCases.get_path(
            "data-files/examples/0.9.0/item-spec/"
            "examples/itemcollection-sample-full.json"
        )
        itemcollection_dict = pystac.StacIO.default().read_json(itemcollection_path)

        self.assertTrue(
            pystac.ItemCollection.is_item_collection(itemcollection_dict),
            msg="Did not correctly identify valid STAC 0.9 ItemCollection.",
        )

    def test_from_dict_preserves_dict(self) -> None:
        param_dict = deepcopy(self.item_collection_dict)

        # test that the parameter is preserved
        _ = ItemCollection.from_dict(param_dict)
        self.assertEqual(param_dict, self.item_collection_dict)

        # assert that the parameter is not preserved with
        # non-default parameter
        _ = ItemCollection.from_dict(param_dict, preserve_dict=False)
        self.assertNotEqual(param_dict, self.item_collection_dict)
