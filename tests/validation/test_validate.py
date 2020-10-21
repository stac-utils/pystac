from datetime import datetime
import json
import os
import shutil
import unittest
from tempfile import TemporaryDirectory

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

    def test_validate_all(self):
        for test_case in TestCases.all_test_catalogs():
            catalog_href = TestCases.test_case_7().get_self_href()
            stac_dict = pystac.STAC_IO.read_json(catalog_href)

            pystac.validation.validate_all(stac_dict, catalog_href)

        # Modify a 0.8.1 collection in a catalog to be invalid with a since-renamed extension
        # and make sure it catches the validation error.

        with TemporaryDirectory() as tmp_dir:
            dst_dir = os.path.join(tmp_dir, 'catalog')
            # Copy test case 7 to the temporary directory
            catalog_href = TestCases.test_case_7().get_self_href()
            shutil.copytree(os.path.dirname(catalog_href), dst_dir)

            new_cat_href = os.path.join(dst_dir, 'catalog.json')

            # Make sure it's valid before modification
            pystac.validation.validate_all(pystac.STAC_IO.read_json(new_cat_href), new_cat_href)

            # Modify a contained collection to add an extension for which the
            # collection is invalid.
            with open(os.path.join(dst_dir, 'acc/collection.json')) as f:
                col = json.load(f)
            col['stac_extensions'] = ['asset']
            with open(os.path.join(dst_dir, 'acc/collection.json'), 'w') as f:
                json.dump(col, f)

            stac_dict = pystac.STAC_IO.read_json(new_cat_href)

            with self.assertRaises(STACValidationError):
                pystac.validation.validate_all(stac_dict, new_cat_href)

    def test_validates_geojson_with_tuple_coordinates(self):
        """This unit tests guards against a bug where if a geometry
        dict has tuples instead of lists for the coordinate sequence,
        which can be produced by shapely, then the geometry still passses
        validation.
        """
        geom = {
            'type':
            'Polygon',
            # Last , is required to ensure tuple creation.
            'coordinates': (((-115.305, 36.126), (-115.305, 36.128), (-115.307, 36.128),
                             (-115.307, 36.126), (-115.305, 36.126)), )
        }

        item = pystac.Item(id='test-item',
                           geometry=geom,
                           bbox=[-115.308, 36.126, -115.305, 36.129],
                           datetime=datetime.utcnow(),
                           properties={})

        self.assertIsNone(item.validate())
