import os
from os.path import join, isfile
import unittest
from tempfile import TemporaryDirectory
import json

from pystac import *
from pystac.utils import is_absolute_href
from tests.utils import (TestCases, RANDOM_GEOM, RANDOM_BBOX)
from pystac.single_file import Search

class SingleFileTest(unittest.TestCase):
    def test_single_file(self):
        with TemporaryDirectory() as tmp_dir:
            m = TestCases.get_path('data-files/itemcollections/example-search.json')
            sf_from_file = SingleFile.from_file(m)
            with open(m) as f:
                sf_dict = json.load(f)
                sf_from_dict = SingleFile.from_dict(sf_dict)
            sf_from_const = SingleFile('FeatureClass', [], [])

            for i, sf in enumerate((sf_from_file, sf_from_dict, sf_from_const)):
                for feature in sf.get_items():
                    self.assertIsInstance(feature, Item)
                for collection in sf.collections:
                    self.assertIsInstance(collection, Collection)
                with self.assertRaises(AttributeError):
                    sf.links
                self.assertIsInstance(sf.to_dict(), dict)

                dk = ['type', 'features', 'collections']
                if sf.search:
                    self.assertIsInstance(sf.search, Search)
                    dk.append('search')
                
                dk.sort()
                keys = list(sf.to_dict().keys())
                keys.sort()
                self.assertEqual(keys, dk)

                tmp_uri = join(tmp_dir, 'test-single-file-{}.json'.format(i))
                sf.save(tmp_uri)
                self.assertTrue(isfile(tmp_uri))

class SearchTest(unittest.TestCase):
    def test_search(self):
        s_empty = Search()
        
        
        self.assertIsInstance(s_empty.to_dict(), dict)

        m = TestCases.get_path('data-files/itemcollections/example-search.json')
        s_from_ic = SingleFile.from_file(m).search
        with open(m) as f:
            sd = json.load(f)['search']
            s_from_dict = Search.from_dict(sd)

        for s in (s_empty, s_from_ic, s_from_dict):
            self.assertIsInstance(s, Search)
            if s.endpoint:
                self.assertIsInstance(s.endpoint, str)
            if s.parameters:
                self.assertIsInstance(s.parameters, dict)
            
            self.assertIsInstance(s.to_dict(), dict)
            keys = list(s.to_dict().keys())
            keys.sort()
            self.assertEqual(keys, ['endpoint', 'parameters'])
        
