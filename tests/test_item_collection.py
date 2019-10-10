import os
from os.path import basename, join, isfile
import unittest
from tempfile import TemporaryDirectory
import json

from pystac import *
from pystac.utils import is_absolute_href
from tests.utils import (TestCases, RANDOM_GEOM, RANDOM_BBOX)

class ItemCollectionTest(unittest.TestCase):
    def test_minimal_item_collection(self):
         with TemporaryDirectory() as tmp_dir:
            m = TestCases.get_path('data-files/itemcollections/minimal-itemcollection.json')
            ic = ItemCollection.from_file(m)
            self.assertIsInstance(ic, ItemCollection)
            self.assertEqual(len(ic.links), 1)
            self.assertEqual(ic.get_self_href(), './{}'.format(ItemCollection.DEFAULT_FILE_NAME))
            self.assertEqual(len(ic.links), 1)

            ic.links = [Link(l.rel, join(tmp_dir, basename(l.target))) for l in ic.links]
            ic.save()
            self.assertTrue(isfile(join(tmp_dir, ItemCollection.DEFAULT_FILE_NAME)))

    def test_item_collection_features(self):
        m = TestCases.get_path('data-files/itemcollections/sample-item-collection.json')
        ic = ItemCollection.from_file(m)
        self.assertIsInstance(ic, ItemCollection)

        with open(m) as f:
            ic_json = json.load(f)
        
        self.assertEqual(ic_json.keys(), ic.to_dict().keys())
        self.assertEqual(ic_json['links'], ic.to_dict(include_self_link=True)['links'])
        self.assertNotEqual(ic_json['links'], ic.to_dict(include_self_link=False)['links'])

        for item in ic.get_items():
            self.assertIsInstance(item, Item)
        
        for link in ic.links:
            self.assertIsInstance(link, Link)

        href = ic.get_self_href()
        self.assertEqual(href, './sample-item-collection.json')

        ic_empty = ItemCollection([])
        self.assertIsInstance(ic_empty, ItemCollection)
        self.assertGreater(len(ic_empty.links), 0)
        for link in ic_empty.links:
            self.assertIsInstance(link, Link)