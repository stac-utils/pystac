import json
import os
import tempfile
import threading
import unittest
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, cast

import pytest
from pytest import MonkeyPatch

import pystac
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
    request_mock.return_value.__enter__.return_value.status = 200
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


def test_read_text_raises_on_429_with_urllib3(
    monkeypatch: MonkeyPatch,
) -> None:
    # https://github.com/stac-utils/pystac/issues/1738
    urllib3 = pytest.importorskip("urllib3")

    class FakeResponse:
        status = 429

        def read(self) -> bytes:
            return b'{"error": "Nope!"}'

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            pass

    class FakePoolManager:
        def request(self, *args: object, **kwargs: object) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr(urllib3, "PoolManager", FakePoolManager)

    stac_io = DefaultStacIO()
    with pytest.raises(Exception):
        stac_io.read_text("http://localhost:5000")


def test_retry_stac_io_raises_on_429(monkeypatch: MonkeyPatch) -> None:
    # https://github.com/stac-utils/pystac/issues/1738
    pytest.importorskip("urllib3")
    from urllib3 import PoolManager

    from pystac.stac_io import RetryStacIO

    class FakeResponse:
        status = 429
        reason = "Too Many Requests"
        headers: dict[str, str] = {}
        data = b'{"error": "Nope!"}'

    def fake_request(
        self: PoolManager, *args: object, **kwargs: object
    ) -> FakeResponse:
        return FakeResponse()

    monkeypatch.setattr(PoolManager, "request", fake_request)

    stac_io = RetryStacIO()
    with pytest.raises(Exception):
        stac_io.read_text("http://localhost:5000")


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


@pytest.mark.vcr()
def test_custom_stac_io() -> None:
    class CustomStacIO(DefaultStacIO):
        def __init__(self, headers: dict[str, str] | None = None):
            super().__init__(headers)
            self.calls = 0

        def read_text_from_href(self, href: str) -> str:
            self.calls += 1
            return super().read_text_from_href(href)

    stac_io = CustomStacIO()
    item = pystac.read_file(
        "https://raw.githubusercontent.com/radiantearth/stac-spec/refs/heads/master/examples/simple-item.json",
        stac_io=stac_io,
    )
    link = item.get_single_link(rel="self")
    assert link
    link.get_href()
    assert stac_io.calls == 2


@pytest.fixture
def redirecting_server() -> Iterator[str]:
    """Serves a catalog at /new/ and permanently redirects /old/ to it."""
    catalog = pystac.Catalog("redirected", "a catalog behind a redirect").to_dict(
        include_self_link=False
    )
    catalog["links"] = [
        {"rel": "child", "href": "./child/catalog.json", "type": "application/json"}
    ]
    child = pystac.Catalog("child", "the child catalog").to_dict(
        include_self_link=False
    )
    child["links"] = []
    documents = {
        "/new/catalog.json": json.dumps(catalog).encode("utf-8"),
        "/new/child/catalog.json": json.dumps(child).encode("utf-8"),
    }

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path.startswith("/old/"):
                # 301, not 308: urllib only follows 308 from Python 3.11 on.
                self.send_response(301)
                self.send_header("Location", "/new/" + self.path[len("/old/") :])
                self.end_headers()
            elif self.path in documents:
                body = documents[self.path]
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_error(404)

        def log_message(self, *_: Any) -> None:
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()


def _stac_ios() -> list[Any]:
    from pystac.stac_io import HAS_URLLIB3

    params: list[Any] = [pytest.param(False, DefaultStacIO, id="urllib")]
    if HAS_URLLIB3:
        from pystac.stac_io import RetryStacIO

        params.append(pytest.param(True, DefaultStacIO, id="urllib3"))
        params.append(pytest.param(True, RetryStacIO, id="retry"))
    return params


@pytest.mark.block_network(allowed_hosts=["127.0.0.1"])
@pytest.mark.parametrize("use_urllib3,stac_io_class", _stac_ios())
@pytest.mark.parametrize("read", ["from_file", "read_file"])
def test_relative_links_resolve_against_redirected_url(
    redirecting_server: str,
    monkeypatch: MonkeyPatch,
    use_urllib3: bool,
    stac_io_class: type[StacIO],
    read: str,
) -> None:
    # https://github.com/stac-utils/pystac/issues/1816
    monkeypatch.setattr("pystac.stac_io.HAS_URLLIB3", use_urllib3)
    stac_io = stac_io_class()
    href = f"{redirecting_server}/old/catalog.json"
    if read == "from_file":
        catalog = pystac.Catalog.from_file(href, stac_io=stac_io)
    else:
        catalog = cast(pystac.Catalog, pystac.read_file(href, stac_io=stac_io))

    assert catalog.get_self_href() == f"{redirecting_server}/new/catalog.json"
    child = next(iter(catalog.get_children()))
    assert child.get_self_href() == f"{redirecting_server}/new/child/catalog.json"


def test_final_href_is_forgotten_when_a_read_is_not_redirected() -> None:
    stac_io = DefaultStacIO()
    href = "https://example.com/catalog.json"
    stac_io._set_final_href(href, "https://example.com/moved/catalog.json")
    assert stac_io._get_final_href(href) == "https://example.com/moved/catalog.json"

    stac_io._set_final_href(href, href)
    assert stac_io._get_final_href(href) == href
