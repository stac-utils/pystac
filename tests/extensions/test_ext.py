import logging

import pytest

import pystac
from pystac.errors import ExtensionNotImplemented
from tests.conftest import get_data_file

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


@pytest.fixture
def eo_ext_item() -> pystac.Item:
    ext_item_uri = get_data_file("eo/eo-landsat-example.json")
    return pystac.Item.from_file(ext_item_uri)


def test_ext_syntax_raises_if_ext_not_on_obj(eo_ext_item: pystac.Item) -> None:
    with pytest.raises(ExtensionNotImplemented):
        eo_ext_item.ext.proj.epsg


def test_ext_syntax_ext_can_be_added(eo_ext_item: pystac.Item) -> None:
    eo_ext_item.ext.add("proj")
    assert eo_ext_item.ext.proj.epsg is None


def test_ext_syntax_ext_can_be_removed(eo_ext_item: pystac.Item) -> None:
    original_n = len(eo_ext_item.stac_extensions)
    eo_ext_item.ext.remove("eo")
    with pytest.raises(ExtensionNotImplemented):
        eo_ext_item.ext.eo
    assert len(eo_ext_item.stac_extensions) == original_n - 1
