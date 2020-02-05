import unittest
from urllib.error import HTTPError

from pystac import STAC_IO
from pystac.cache import CollectionCache
from pystac.serialization import (identify_stac_object, identify_stac_object_type,
                                  merge_common_properties, STACObjectType)

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
