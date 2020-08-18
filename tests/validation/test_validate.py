import json
import unittest

import jsonschema

import pystac
from pystac.serialization.common_properties import merge_common_properties
from pystac.validation import STACValidationError
from tests.utils import TestCases


class ValidateTest(unittest.TestCase):
    def test_validate_current_version(self):
        catalog = pystac.read_file(
            TestCases.get_path('data-files/catalogs/test-case-1/'
                               'catalog.json'))
        catalog.validate()

        collection = pystac.read_file(
            TestCases.get_path('data-files/catalogs/test-case-1/'
                               '/country-1/area-1-1/'
                               'collection.json'))
        collection.validate()

        item = pystac.read_file(TestCases.get_path('data-files/item/sample-item.json'))
        item.validate()

    def test_validate_examples(self):
        for example in TestCases.get_examples_info():
            stac_version = example['stac_version']
            path = example['path']
            valid = example['valid']

            if stac_version < '0.8':
                with open(path) as f:
                    stac_json = json.load(f)

                self.assertEqual(len(pystac.validation.validate_dict(stac_json)), 0)
            else:
                with self.subTest(path):
                    with open(path) as f:
                        stac_json = json.load(f)

                    # Check if common properties need to be merged
                    if stac_version < '1.0':
                        if example['object_type'] == pystac.STACObjectType.ITEM:
                            collection_cache = pystac.cache.CollectionCache()
                            merge_common_properties(stac_json, collection_cache, path)

                    if valid:
                        pystac.validation.validate_dict(stac_json)
                    else:
                        with self.assertRaises(STACValidationError):
                            try:
                                pystac.validation.validate_dict(stac_json)
                            except STACValidationError as e:
                                self.assertIsInstance(e.source, jsonschema.ValidationError)
                                raise e

    def test_validate_error_contains_href(self):
        # Test that the exception message contains the HREF of the object if available.
        cat = TestCases.test_case_1()
        item = cat.get_item('area-1-1-labels', recursive=True)
        assert item.get_self_href() is not None

        item.geometry = {'type': 'INVALID'}

        with self.assertRaises(STACValidationError):
            try:
                item.validate()
            except STACValidationError as e:
                self.assertTrue(item.get_self_href() in str(e))
                raise e
