import json
import os
import tempfile
import unittest
from pathlib import Path

import pytest

import pystac
import pystac.errors
from pystac.stac_io import DefaultStacIO, DuplicateKeyReportingMixin, StacIO
from tests.utils import TestCases


def test_read_write_collection() -> None:
    collection = pystac.read_file(
        TestCases.get_path("data-files/collections/multi-extent.json")
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        dest_href = os.path.join(tmp_dir, "collection.json")
        pystac.write_file(collection, dest_href=dest_href)
        assert os.path.exists(dest_href), "File was not written."


def test_read_write_collection_with_file_protocol() -> None:
    collection = pystac.read_file(
        "file://" + TestCases.get_path("data-files/collections/multi-extent.json")
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        dest_href = os.path.join(tmp_dir, "collection.json")
        pystac.write_file(collection, dest_href="file://" + dest_href)
        assert os.path.exists(dest_href), "File was not written."


def test_read_item() -> None:
    item = pystac.read_file(TestCases.get_path("data-files/item/sample-item.json"))
    with tempfile.TemporaryDirectory() as tmp_dir:
        dest_href = os.path.join(tmp_dir, "item.json")
        pystac.write_file(item, dest_href=dest_href)
        assert os.path.exists(dest_href), "File was not written."


def test_read_write_catalog() -> None:
    catalog = pystac.read_file(
        TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        dest_href = os.path.join(tmp_dir, "catalog.json")
        pystac.write_file(catalog, dest_href=dest_href)
        assert os.path.exists(dest_href), "File was not written."


def test_read_item_collection_raises_exception() -> None:
    with pytest.raises(pystac.STACTypeError):
        _ = pystac.read_file(
            TestCases.get_path("data-files/item-collection/sample-item-collection.json")
        )


def test_read_item_dict() -> None:
    stac_io = StacIO.default()
    item_dict = stac_io.read_json(
        TestCases.get_path("data-files/item/sample-item.json")
    )
    item = pystac.read_dict(item_dict)
    assert isinstance(item, pystac.Item)


def test_read_collection_dict() -> None:
    stac_io = StacIO.default()
    collection_dict = stac_io.read_json(
        TestCases.get_path("data-files/collections/multi-extent.json")
    )
    collection = pystac.read_dict(collection_dict)
    assert isinstance(collection, pystac.Collection)


def test_read_catalog_dict() -> None:
    stac_io = StacIO.default()
    catalog_dict = stac_io.read_json(
        TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
    )
    catalog = pystac.read_dict(catalog_dict)
    assert isinstance(catalog, pystac.Catalog)


def test_read_from_stac_object() -> None:
    catalog = pystac.STACObject.from_file(
        TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
    )
    assert isinstance(catalog, pystac.Catalog)


def test_report_duplicate_keys() -> None:
    # Directly from dict
    class ReportingStacIO(DefaultStacIO, DuplicateKeyReportingMixin):
        pass

    stac_io = ReportingStacIO()
    test_json = """{
        "key": "value_1",
        "key": "value_2"
    }"""

    with pytest.raises(pystac.DuplicateObjectKeyError) as excinfo:
        stac_io.json_loads(test_json)
    assert str(excinfo.value) == 'Found duplicate object name "key"'

    # From file
    with tempfile.TemporaryDirectory() as tmp_dir:
        src_href = os.path.join(tmp_dir, "test.json")
        with open(src_href, "w") as dst:
            dst.write(test_json)

        with pytest.raises(pystac.DuplicateObjectKeyError) as excinfo:
            stac_io.read_json(src_href)
        assert str(excinfo.value), f'Found duplicate object name "key" in {src_href}'


@unittest.mock.patch("pystac.stac_io.urllib3.PoolManager.request")
def test_headers_stac_io(request_mock: unittest.mock.MagicMock) -> None:
    stac_io = DefaultStacIO(headers={"Authorization": "api-key fake-api-key-value"})

    catalog = pystac.Catalog("an-id", "a description").to_dict()
    # required until https://github.com/stac-utils/pystac/pull/896 is merged
    catalog["links"] = []
    request_mock.return_value.__enter__.return_value.read.return_value = json.dumps(
        catalog
    ).encode("utf-8")
    pystac.Catalog.from_file("https://example.com/catalog.json", stac_io=stac_io)

    headers = request_mock.call_args[1]["headers"]
    assert headers == {"User-Agent": f"pystac/{pystac.__version__}", **stac_io.headers}


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


def test_save_http_href_errors(tmp_path: Path) -> None:
    catalog = pystac.Catalog(id="test-catalog", description="")
    catalog.set_self_href("http://pystac.test/catalog.json")
    with pytest.raises(NotImplementedError):
        catalog.save_object()


@pytest.mark.vcr()
def test_urls_with_non_ascii_characters() -> None:
    from pystac.stac_io import HAS_URLLIB3

    url = "https://capella-open-data.s3.us-west-2.amazonaws.com/stac/capella-open-data-by-capital/capella-open-data-malé/collection.json"

    if HAS_URLLIB3:
        pystac.Collection.from_file(url)
    else:
        with pytest.raises(pystac.STACError):
            pystac.Collection.from_file(url)


@pytest.mark.vcr()
def test_proj_json_schema_is_readable() -> None:
    from pystac.stac_io import DefaultStacIO

    stac_io = DefaultStacIO()
    _ = stac_io.read_text_from_href(
        "https://proj.org/schemas/v0.7/projjson.schema.json"
    )
