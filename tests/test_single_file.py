import os
from os.path import join, isfile
import unittest
from tempfile import TemporaryDirectory
import json
from jsonschema import ValidationError

from pystac import *
from pystac.utils import is_absolute_href
from tests.utils import (TestCases, RANDOM_GEOM, RANDOM_BBOX, SchemaValidator)
from pystac.single_file import Search

class SingleFileSTACTest(unittest.TestCase):
    def setUp(self):
        self.EXAMPLE_SINGLE_FILE = TestCases.get_path('data-files/itemcollections/example-search.json')
        with open(TestCases.get_path(self.EXAMPLE_SINGLE_FILE)) as f:
            self.EXAMPLE_SF_DICT = json.load(f)

    def test_single_file(self):
        with TemporaryDirectory() as tmp_dir:
            sf_from_file = SingleFileSTAC.from_file(self.EXAMPLE_SINGLE_FILE)
            sf_from_dict = SingleFileSTAC.from_dict(self.EXAMPLE_SF_DICT)
            sf_from_const = SingleFileSTAC('FeatureClass', [], [])

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
                
                keys = list(sf.to_dict().keys())
                self.assertEqual(set(keys), set(dk))

                tmp_uri = join(tmp_dir, 'test-single-file-{}.json'.format(i))
                sf.save(tmp_uri)
                self.assertTrue(isfile(tmp_uri))
    
    def test_validate_single_file(self):
        sv = SchemaValidator()
        sv.validate_dict(self.EXAMPLE_SF_DICT, SingleFileSTAC)
        sf_from_file = SingleFileSTAC.from_file(self.EXAMPLE_SINGLE_FILE)
        sv.validate_object(sf_from_file)

        with TemporaryDirectory() as tmp_dir:
            tmp_uri = join(tmp_dir, 'test-single-file-val.json')
            sf_from_file.save(tmp_uri)
            with open(tmp_uri) as f:
                val_dict = json.load(f)
        sv.validate_dict(val_dict, SingleFileSTAC)

        val_dict['properties']['endpoint'] = 1
        with self.assertRaises(ValidationError):
            sv.validate_dict(val_dict, SingleFileSTAC)


class SearchTest(unittest.TestCase):
    def test_search(self):
        s_empty = Search()
        self.assertIsInstance(s_empty.to_dict(), dict)

        m = TestCases.get_path('data-files/itemcollections/example-search.json')
        s_from_ic = SingleFileSTAC.from_file(m).search
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
        
