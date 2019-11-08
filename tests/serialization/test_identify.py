import os
import unittest
import csv

from pystac import STAC_IO
from pystac.serialization import identify_stac_object

from tests.utils import TestCases


class IdentifyTest(unittest.TestCase):
    def setUp(self):
        self.examples = []

        info_path = TestCases.get_path('data-files/examples/example-info.csv')
        with open(TestCases.get_path(
                'data-files/examples/example-info.csv')) as f:
            for row in csv.reader(f):
                path = os.path.abspath(
                    os.path.join(os.path.dirname(info_path), row[0]))
                object_type = row[1]
                stac_version = row[2]
                common_extensions = []
                if row[3]:
                    common_extensions = row[3].split('|')
                custom_extensions = []
                if row[4]:
                    custom_extensions = row[4].split('|')

                self.examples.append({
                    'path': path,
                    'object_type': object_type,
                    'stac_version': stac_version,
                    'common_extensions': common_extensions,
                    'custom_extensions': custom_extensions
                })

    def test_identify(self):
        collection_cache = {}
        for example in self.examples:
            path = example['path']
            d = STAC_IO.read_json(path)

            actual = identify_stac_object(d,
                                          merge_collection_properties=True,
                                          json_href=path,
                                          collection_cache=collection_cache)

            msg = 'Failed {}:'.format(path)

            self.assertEqual(actual.object_type,
                             example['object_type'],
                             msg=msg)
            version_contained_in_range = actual.version_range.contains(
                example['stac_version'])
            self.assertTrue(version_contained_in_range, msg=msg)
            self.assertEqual(set(actual.common_extensions),
                             set(example['common_extensions']),
                             msg=msg)
            self.assertEqual(set(actual.custom_extensions),
                             set(example['custom_extensions']),
                             msg=msg)
