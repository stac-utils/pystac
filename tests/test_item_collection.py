import os
import unittest
from tempfile import TemporaryDirectory
import json

from pystac import ItemCollection
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
            self.assertIsNone(ic.get_self_href())