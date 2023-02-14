import json
import os
import tempfile
import unittest

import pytest

import pystac
from pystac.stac_io import DefaultStacIO, DuplicateKeyReportingMixin, StacIO
from tests.utils import TestCases


class StacIOTest(unittest.TestCase):
    def setUp(self) -> None:
        self.stac_io = StacIO.default()

    def test_read_write_collection(self) -> None:
        collection = pystac.read_file(
            TestCases.get_path("data-files/collections/multi-extent.json")
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_href = os.path.join(tmp_dir, "collection.json")
            pystac.write_file(collection, dest_href=dest_href)
            self.assertTrue(os.path.exists(dest_href), msg="File was not written.")

    def test_read_item(self) -> None:
        item = pystac.read_file(TestCases.get_path("data-files/item/sample-item.json"))
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_href = os.path.join(tmp_dir, "item.json")
            pystac.write_file(item, dest_href=dest_href)
            self.assertTrue(os.path.exists(dest_href), msg="File was not written.")

    def test_read_write_catalog(self) -> None:
        catalog = pystac.read_file(
            TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
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

    def test_read_item_dict(self) -> None:
        item_dict = self.stac_io.read_json(
            TestCases.get_path("data-files/item/sample-item.json")
        )
        item = pystac.read_dict(item_dict)
        self.assertIsInstance(item, pystac.Item)

    def test_read_collection_dict(self) -> None:
        collection_dict = self.stac_io.read_json(
            TestCases.get_path("data-files/collections/multi-extent.json")
        )
        collection = pystac.read_dict(collection_dict)
        self.assertIsInstance(collection, pystac.Collection)

    def test_read_catalog_dict(self) -> None:
        catalog_dict = self.stac_io.read_json(
            TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
        )
        catalog = pystac.read_dict(catalog_dict)
        self.assertIsInstance(catalog, pystac.Catalog)

    def test_read_from_stac_object(self) -> None:
        catalog = pystac.STACObject.from_file(
            TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
        )
        self.assertIsInstance(catalog, pystac.Catalog)

    def test_report_duplicate_keys(self) -> None:
        # Directly from dict
        class ReportingStacIO(DefaultStacIO, DuplicateKeyReportingMixin):
            pass

        stac_io = ReportingStacIO()
        test_json = """{
            "key": "value_1",
            "key": "value_2"
        }"""

        with self.assertRaises(pystac.DuplicateObjectKeyError) as excinfo:
            stac_io.json_loads(test_json)
        self.assertEqual(str(excinfo.exception), 'Found duplicate object name "key"')

        # From file
        with tempfile.TemporaryDirectory() as tmp_dir:
            src_href = os.path.join(tmp_dir, "test.json")
            with open(src_href, "w") as dst:
                dst.write(test_json)

            with self.assertRaises(pystac.DuplicateObjectKeyError) as excinfo:
                stac_io.read_json(src_href)
            self.assertEqual(
                str(excinfo.exception),
                f'Found duplicate object name "key" in {src_href}',
            )

    @unittest.mock.patch("pystac.stac_io.urlopen")
    def test_headers_stac_io(self, urlopen_mock: unittest.mock.MagicMock) -> None:
        stac_io = DefaultStacIO(headers={"Authorization": "api-key fake-api-key-value"})

        catalog = pystac.Catalog("an-id", "a description").to_dict()
        # required until https://github.com/stac-utils/pystac/pull/896 is merged
        catalog["links"] = []
        urlopen_mock.return_value.__enter__.return_value.read.return_value = json.dumps(
            catalog
        ).encode("utf-8")
        pystac.Catalog.from_file("https://example.com/catalog.json", stac_io=stac_io)

        request_obj = urlopen_mock.call_args[0][0]
        self.assertEqual(request_obj.headers, stac_io.headers)


@pytest.mark.vcr()
def test_retry_stac_io() -> None:
    # This doesn't test any retry behavior, but it does make sure that we can
    # still read objects.
    _ = pytest.importorskip("urllib3")
    from pystac.stac_io import RetryStacIO

    stac_io = RetryStacIO()
    _ = stac_io.read_stac_object("https://planetarycomputer.microsoft.com/api/stac/v1")


@pytest.mark.vcr()
def test_retry_stac_io_404() -> None:
    # This doesn't test any retry behavior, but it does make sure that we can
    # error when an object doesn't exist.
    _ = pytest.importorskip("urllib3")
    from pystac.stac_io import RetryStacIO

    stac_io = RetryStacIO()
    with pytest.raises(Exception):
        _ = stac_io.read_stac_object(
            "https://planetarycomputer.microsoft.com"
            "/api/stac/v1/collections/not-a-collection-id"
        )
