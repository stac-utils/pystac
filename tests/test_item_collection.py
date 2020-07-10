import os
from os.path import basename, join, isfile
import unittest
from tempfile import TemporaryDirectory
import json
from copy import deepcopy

from pystac import (ItemCollection, Link, Item, STACObjectType)
from tests.utils import (TestCases, SchemaValidator, STACValidationError)


class ItemCollectionTest(unittest.TestCase):
    def setUp(self):
        self.IC_MINIMAL_URI = TestCases.get_path(
            'data-files/itemcollections/minimal-itemcollection.json')
        with open(self.IC_MINIMAL_URI) as f:
            self.IC_MINIMAL_DICT = json.load(f)

        self.IC_URI = TestCases.get_path('data-files/itemcollections/sample-item-collection.json')
        with open(self.IC_URI) as f:
            self.IC_DICT = json.load(f)

    def test_minimal_item_collection(self):
        with TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'item_collection.json')
            ic = ItemCollection.from_file(self.IC_MINIMAL_URI)
            ic.set_self_href(path)
            self.assertIsInstance(ic, ItemCollection)
            self.assertEqual(len(ic.links), 1)
            self.assertEqual(ic.get_self_href(), path)
            self.assertEqual(len(ic.links), 1)

            ic.links = [Link(link.rel, join(tmp_dir, basename(link.target))) for link in ic.links]
            ic.save()
            self.assertTrue(isfile(path))
            with open(path) as f:
                ic_val_dict = json.load(f)
            SchemaValidator().validate_dict(ic_val_dict, STACObjectType.ITEMCOLLECTION)

    def test_item_collection_features(self):
        ic = ItemCollection.from_file(self.IC_URI)
        self.assertIsInstance(ic, ItemCollection)

        ic_json = deepcopy(self.IC_DICT)

        self.assertEqual(ic_json.keys(), ic.to_dict().keys())
        self.assertEqual(ic_json['links'], ic.to_dict(include_self_link=True)['links'])
        self.assertNotEqual(ic_json['links'], ic.to_dict(include_self_link=False)['links'])

        for item in ic.get_items():
            self.assertIsInstance(item, Item)

        for link in ic.links:
            self.assertIsInstance(link, Link)

        href = ic.get_self_href()
        self.assertEqual(href, 'http://stacspec.org/sample-item-collection.json')

        ic_empty = ItemCollection([])
        self.assertIsInstance(ic_empty, ItemCollection)
        self.assertEqual(len(ic_empty.links), 0)

    def test_validate_item_collection(self):
        sv = SchemaValidator()
        ic_1 = ItemCollection([])
        sv.validate_object(ic_1)
        sv.validate_dict(self.IC_DICT, STACObjectType.ITEMCOLLECTION)
        ic_2 = ItemCollection.from_file(self.IC_URI)
        ic_val_dict = ic_2.to_dict()
        ic_val_dict['features'] = 'not an array'
        with self.assertRaises(STACValidationError):
            sv.validate_dict(ic_val_dict, STACObjectType.ITEMCOLLECTION)
