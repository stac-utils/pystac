import os
import unittest
from tempfile import TemporaryDirectory
import json

import pystac
from pystac.extensions.single_file_stac import create_single_file_stac
from tests.utils import TestCases


class SingleFileSTACTest(unittest.TestCase):
    def setUp(self):
        self.EXAMPLE_SINGLE_FILE = TestCases.get_path(
            'data-files/examples/1.0.0-beta.2/'
            'extensions/single-file-stac/examples/example-search.json')
        with open(TestCases.get_path(self.EXAMPLE_SINGLE_FILE)) as f:
            self.EXAMPLE_SF_DICT = json.load(f)

    def test_read_single_file_stac(self):
        cat = pystac.read_file(self.EXAMPLE_SINGLE_FILE)

        cat.validate()

        features = cat.ext['single-file-stac'].features
        self.assertEqual(len(features), 2)

        self.assertEqual(features[0].ext.view.sun_azimuth, 152.63804142)

        collections = cat.ext['single-file-stac'].collections

        self.assertEqual(len(collections), 1)
        self.assertEqual(collections[0].license, "PDDL-1.0")

    def test_create_single_file_stac(self):
        cat = TestCases.test_case_1()
        sfs = create_single_file_stac(TestCases.test_case_1())

        with TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, 'single_file_stac.json')
            pystac.write_file(sfs, include_self_link=False, dest_href=path)

            sfs_read = pystac.read_file(path)

            sfs_read.validate()

            self.assertTrue(sfs_read.ext.implements('single-file-stac'))

            read_fids = set([f.id for f in sfs_read.ext['single-file-stac'].features])
            expected_fids = set([f.id for f in cat.get_all_items()])

            self.assertEqual(read_fids, expected_fids)

            read_col_ids = set([col.id for col in sfs_read.ext['single-file-stac'].collections])
            expected_col_ids = set(['area-1-1', 'area-1-2', 'area-2-1', 'area-2-2'])

            self.assertEqual(read_col_ids, expected_col_ids)
