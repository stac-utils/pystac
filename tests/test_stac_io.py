import os
import unittest
import warnings

import pystac
from pystac.stac_io import STAC_IO
from tests.utils import TestCases, get_temp_dir


class StacIOTest(unittest.TestCase):
    def test_stac_io_issues_warnings(self) -> None:
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")
            # Trigger a warning.
            STAC_IO.read_text(
                TestCases.get_path("data-files/collections/multi-extent.json")
            )

            # Verify some things
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test_read_write_collection(self) -> None:
        collection = pystac.read_file(
            TestCases.get_path("data-files/collections/multi-extent.json")
        )
        with get_temp_dir() as tmp_dir:
            dest_href = os.path.join(tmp_dir, "collection.json")
            pystac.write_file(collection, dest_href=dest_href)
            self.assertTrue(os.path.exists(dest_href), msg="File was not written.")

    def test_read_item(self) -> None:
        item = pystac.read_file(TestCases.get_path("data-files/item/sample-item.json"))
        with get_temp_dir() as tmp_dir:
            dest_href = os.path.join(tmp_dir, "item.json")
            pystac.write_file(item, dest_href=dest_href)
            self.assertTrue(os.path.exists(dest_href), msg="File was not written.")

    def test_read_write_catalog(self) -> None:
        catalog = pystac.read_file(
            TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
        )
        with get_temp_dir() as tmp_dir:
            dest_href = os.path.join(tmp_dir, "catalog.json")
            pystac.write_file(catalog, dest_href=dest_href)
            self.assertTrue(os.path.exists(dest_href), msg="File was not written.")

    def test_read_item_collection_raises_exception(self) -> None:
        with self.assertRaises(pystac.STACTypeError):
            _ = pystac.read_file(
                TestCases.get_path(
                    "data-files/item-collection/sample-item-collection.json"
                )
            )
