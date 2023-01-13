import sys

from pytest_mock import MockerFixture

import pystac
from pystac.html.jinja_env import get_jinja_env
from tests.utils import TestCases


def test_item_html() -> None:
    item_stac_href = TestCases.get_path("data-files/item/sample-item.json")
    item_html_href = TestCases.get_path("data-files/html/sample-item.html")
    item = pystac.Item.from_file(item_stac_href)
    assert item._repr_html_() == open(item_html_href).read()


def test_missing_jinja2(mocker: MockerFixture) -> None:
    get_jinja_env.cache_clear()
    mocker.patch.dict(sys.modules, {"jinja2": None})
    assert get_jinja_env() is None
    get_jinja_env.cache_clear()
