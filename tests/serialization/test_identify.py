import unittest
from urllib.error import HTTPError

from pystac import STAC_IO
from pystac.cache import CollectionCache
from pystac.serialization import (identify_stac_object, identify_stac_object_type,
                                  merge_common_properties, STACObjectType)
from pystac.serialization.identify import (STACVersionRange, STACVersionID)

from tests.utils import TestCases


class IdentifyTest(unittest.TestCase):
    def setUp(self):
        self.examples = TestCases.get_examples_info()

    def test_identify(self):
        collection_cache = CollectionCache()
        for example in self.examples:
            path = example['path']
            d = STAC_IO.read_json(path)
            if identify_stac_object_type(d) == STACObjectType.ITEM:
                try:
                    merge_common_properties(d, json_href=path, collection_cache=collection_cache)
                except HTTPError:
                    pass

            actual = identify_stac_object(d)
            # Explicitly cover __repr__ functions in tests
            str_info = str(actual)
            self.assertIsInstance(str_info, str)

            msg = 'Failed {}:'.format(path)

            self.assertEqual(actual.object_type, example['object_type'], msg=msg)
            version_contained_in_range = actual.version_range.contains(example['stac_version'])
            self.assertTrue(version_contained_in_range, msg=msg)
            self.assertEqual(set(actual.common_extensions),
                             set(example['common_extensions']),
                             msg=msg)
            self.assertEqual(set(actual.custom_extensions),
                             set(example['custom_extensions']),
                             msg=msg)


class VersionTest(unittest.TestCase):
    def test_version_ordering(self):
        self.assertEqual(STACVersionID('0.9.0'), STACVersionID('0.9.0'))
        self.assertFalse(STACVersionID('0.9.0') < STACVersionID('0.9.0'))
        self.assertFalse(STACVersionID('0.9.0') != STACVersionID('0.9.0'))
        self.assertFalse(STACVersionID('0.9.0') > STACVersionID('0.9.0'))
        self.assertTrue(STACVersionID('1.0.0-beta.2') < '1.0.0')
        self.assertTrue(STACVersionID('0.9.1') > '0.9.0')
        self.assertFalse(STACVersionID('0.9.0') > '0.9.0')
        self.assertTrue(STACVersionID('0.9.0') <= '0.9.0')
        self.assertTrue(STACVersionID('1.0.0-beta.1') <= STACVersionID('1.0.0-beta.2'))
        self.assertFalse(STACVersionID('1.0.0') < STACVersionID('1.0.0-beta.2'))

    def test_version_range_ordering(self):
        version_range = STACVersionRange('0.9.0', '1.0.0-beta.2')
        self.assertIsInstance(str(version_range), str)
        self.assertTrue(version_range.contains('1.0.0-beta.1'))
        self.assertFalse(version_range.contains('1.0.0'))
        self.assertTrue(version_range.is_later_than('0.8.9'))

        version_range = STACVersionRange('0.9.0', '1.0.0-beta.1')
        self.assertFalse(version_range.contains('1.0.0-beta.2'))

        version_range = STACVersionRange(min_version='0.6.0-rc1', max_version='0.9.0')
        self.assertTrue(version_range.contains('0.9.0'))
