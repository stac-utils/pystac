import os
import unittest
import tempfile

from pystac import read_dict, read_file, write_file
from pystac.stac_object import STACObject
from pystac.collection import Collection
from pystac.errors import DuplicateObjectKeyError, STACTypeError
from pystac.item import Item
from pystac.catalog import Catalog
from pystac.stac_io import StacIO, DefaultStacIO, DuplicateKeyReportingMixin
from tests.utils.test_cases import TestCases


class StacIOTest(unittest.TestCase):
    def setUp(self) -> None:
        self.stac_io = StacIO.default()

    def test_read_write_collection(self) -> None:
        collection = read_file(
            TestCases.get_path("data-files/collections/multi-extent.json")
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_href = os.path.join(tmp_dir, "collection.json")
            write_file(collection, dest_href=dest_href)
            self.assertTrue(os.path.exists(dest_href), msg="File was not written.")

    def test_read_item(self) -> None:
        item = read_file(TestCases.get_path("data-files/item/sample-item.json"))
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_href = os.path.join(tmp_dir, "item.json")
            write_file(item, dest_href=dest_href)
            self.assertTrue(os.path.exists(dest_href), msg="File was not written.")

    def test_read_write_catalog(self) -> None:
        catalog = read_file(
            TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_href = os.path.join(tmp_dir, "catalog.json")
            write_file(catalog, dest_href=dest_href)
            self.assertTrue(os.path.exists(dest_href), msg="File was not written.")

    def test_read_item_collection_raises_exception(self) -> None:
        with self.assertRaises(STACTypeError):
            _ = read_file(
                TestCases.get_path(
                    "data-files/item-collection/sample-item-collection.json"
                )
            )

    def test_read_item_dict(self) -> None:
        item_dict = self.stac_io.read_json(
            TestCases.get_path("data-files/item/sample-item.json")
        )
        item = read_dict(item_dict)
        self.assertIsInstance(item, Item)

    def test_read_collection_dict(self) -> None:
        collection_dict = self.stac_io.read_json(
            TestCases.get_path("data-files/collections/multi-extent.json")
        )
        collection = read_dict(collection_dict)
        self.assertIsInstance(collection, Collection)

    def test_read_catalog_dict(self) -> None:
        catalog_dict = self.stac_io.read_json(
            TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
        )
        catalog = read_dict(catalog_dict)
        self.assertIsInstance(catalog, Catalog)

    def test_read_from_stac_object(self) -> None:
        catalog = STACObject.from_file(
            TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
        )
        self.assertIsInstance(catalog, Catalog)

    def test_report_duplicate_keys(self) -> None:
        # Directly from dict
        class ReportingStacIO(DefaultStacIO, DuplicateKeyReportingMixin):
            pass

        stac_io = ReportingStacIO()
        test_json = """{
            "key": "value_1",
            "key": "value_2"
        }"""

        with self.assertRaises(DuplicateObjectKeyError) as excinfo:
            stac_io.json_loads(test_json)
        self.assertEqual(str(excinfo.exception), 'Found duplicate object name "key"')

        # From file
        with tempfile.TemporaryDirectory() as tmp_dir:
            src_href = os.path.join(tmp_dir, "test.json")
            with open(src_href, "w") as dst:
                dst.write(test_json)

            with self.assertRaises(DuplicateObjectKeyError) as excinfo:
                stac_io.read_json(src_href)
            self.assertEqual(
                str(excinfo.exception),
                f'Found duplicate object name "key" in {src_href}',
            )
