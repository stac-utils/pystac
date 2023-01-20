import sys

import html5lib
from pytest_mock import MockerFixture

import pystac
from pystac.html.jinja_env import get_jinja_env
from tests.utils import TestCases


def test_valid_html() -> None:
    def parse_html(stac_html: str) -> None:
        html5lib.HTMLParser(strict=True).parse("<!DOCTYPE html>\n" + stac_html)

    href = TestCases.get_path(
        "data-files/catalogs/test-case-1/country-1/area-1-1/area-1-1-imagery/"
        "area-1-1-imagery.json"
    )
    item = pystac.Item.from_file(href)
    parse_html(item._repr_html_())

    # These can be uncommented once psytac issue #955 is fixed
    # href = TestCases.get_path(
    #     "data-files/catalogs/test-case-1/country-1/area-1-1/collection.json"
    # )
    # collection = pystac.Collection.from_file(href)
    # parse_html(collection._repr_html_())

    # href = TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
    # catalog = pystac.Catalog.from_file(href)
    # parse_html(catalog._repr_html_())

    href = TestCases.get_path("data-files/item-collection/sample-item-collection.json")
    item_collection = pystac.ItemCollection.from_file(href)
    parse_html(item_collection._repr_html_())


def test_missing_jinja2(mocker: MockerFixture) -> None:
    get_jinja_env.cache_clear()

    mocker.patch.dict(sys.modules, {"jinja2": None})
    assert get_jinja_env() is None

    item_stac_href = TestCases.get_path("data-files/item/sample-item.json")
    item = pystac.Item.from_file(item_stac_href)
    assert item._repr_html_() == "&lt;Item id=CS3-20160503_132131_05&gt;"

    get_jinja_env.cache_clear()
