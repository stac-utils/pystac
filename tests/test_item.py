import os
import unittest
import json
from tempfile import TemporaryDirectory
from datetime import datetime
import dateutil

from pystac import *
from pystac.utils import is_absolute_href
from tests.utils import (TestCases, RANDOM_GEOM, RANDOM_BBOX)


class ItemTest(unittest.TestCase):
    def test_to_from_dict(self):
        m = TestCases.get_path('data-files/itemcollections/sample-item-collection.json')
        with open(m) as f:
            item_dict_list = json.load(f)['features']
        
        item = Item.from_dict(item_dict_list[0])
        self.assertIsInstance(item, Item)
        self.assertIsInstance(item.id, str)
        self.assertIsInstance(item.geometry, dict)
        self.assertIsInstance(item.bbox, list)
        self.assertIsInstance(item.datetime, datetime)
        self.assertIsInstance(item.properties, dict)
        self.assertEqual(item.get_self_href(), 'http://cool-sat.com/catalog/CS3-20160503_132130_04/CS3-20160503_132130_04.json')
        for l in item.links:
            self.assertIsInstance(l, Link)
        self.assertEqual(item.collection, 'CS3')

        d = item.to_dict()
        self.assertEqual(d['id'], item.id)
        self.assertEqual(d['geometry'], item.geometry)
        self.assertEqual(d['bbox'], item.bbox)
        dt = dateutil.parser.parse(d['properties']['datetime'])
        self.assertEqual(dt, item.datetime.replace(microsecond=0))
        self.assertIsInstance(d['properties'], dict)
        for l in d['links']:
            self.assertIsInstance(l, dict)
        self.assertEqual(item.collection, d['collection'])
        

