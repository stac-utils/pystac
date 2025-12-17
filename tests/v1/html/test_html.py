import sys
from typing import Any

import html5lib
import pytest
from pystac.html.jinja_env import get_jinja_env
from pytest_mock import MockerFixture

import pystac
from tests.v1.utils import TestCases


def parse_html(stac_html: str) -> None:
    html5lib.HTMLParser(strict=True).parse("<!DOCTYPE html>\n" + stac_html)


@pytest.mark.parametrize(
    "path,cls",
    [
        ("data-files/item/sample-item.json", pystac.Item),
        (
            "data-files/catalogs/test-case-1/country-1/area-1-1/collection.json",
            pystac.Collection,
        ),
        ("data-files/catalogs/test-case-1/catalog.json", pystac.Catalog),
        (
            "data-files/item-collection/sample-item-collection.json",
            pystac.ItemCollection,
        ),
    ],
)
def test_from_file_valid_html(path: str, cls: Any) -> None:
    href = TestCases.get_path(path)
    obj = cls.from_file(href)
    parse_html(obj._repr_html_())


@pytest.mark.parametrize(
    "path,cls",
    [
        ("data-files/item/sample-item.json", pystac.Item),
        (
            "data-files/catalogs/test-case-1/country-1/area-1-1/collection.json",
            pystac.Collection,
        ),
        ("data-files/catalogs/test-case-1/catalog.json", pystac.Catalog),
        (
            "data-files/item-collection/sample-item-collection.json",
            pystac.ItemCollection,
        ),
    ],
)
def test_from_file_missing_jinja2(mocker: MockerFixture, path: str, cls: Any) -> None:
    get_jinja_env.cache_clear()

    mocker.patch.dict(sys.modules, {"jinja2": None})
    assert get_jinja_env() is None

    href = TestCases.get_path(path)
    obj = cls.from_file(href)
    assert cls.__name__ in obj._repr_html_()

    get_jinja_env.cache_clear()


def test_nested_objects_valid_html() -> None:
    href = TestCases.get_path("data-files/item/sample-item-asset-properties.json")
    item = pystac.Item.from_file(href)

    link = item.links[0]
    parse_html(link._repr_html_())

    asset = item.assets["thumbnail"]
    parse_html(asset._repr_html_())

    provider = (asset.common_metadata.providers or [])[0]
    parse_html(provider._repr_html_())


def test_nested_objects_missing_jinja2(mocker: MockerFixture) -> None:
    get_jinja_env.cache_clear()

    mocker.patch.dict(sys.modules, {"jinja2": None})
    assert get_jinja_env() is None

    href = TestCases.get_path("data-files/item/sample-item-asset-properties.json")
    item = pystac.Item.from_file(href)

    link = item.links[0]
    assert pystac.Link.__name__ in link._repr_html_()

    asset = item.assets["thumbnail"]
    assert pystac.Asset.__name__ in asset._repr_html_()

    provider = (asset.common_metadata.providers or [])[0]
    assert pystac.Provider.__name__ in provider._repr_html_()

    get_jinja_env.cache_clear()
