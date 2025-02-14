import os.path
from copy import deepcopy
from typing import Any

import pytest

from pystac import Catalog, Item, utils

from . import utils as test_utils
from .utils import TestCases


def test_to_from_dict(sample_item_dict: dict[str, Any]) -> None:
    param_dict = deepcopy(sample_item_dict)

    test_utils.assert_to_from_dict(Item, param_dict)
    item = Item.from_dict(param_dict)
    assert item.id == "CS3-20160503_132131_05"

    # test asset creation additional field(s)
    assert (
        item.assets["analytic"].extra_fields["product"]
        == "http://cool-sat.com/catalog/products/analytic.json"
    )
    assert len(item.assets["thumbnail"].extra_fields) == 0

    # test that the parameter is preserved
    assert param_dict == sample_item_dict

    # assert that the parameter is preserved regardless of preserve_dict
    with pytest.warns(FutureWarning):
        Item.from_dict(param_dict, preserve_dict=False)
    assert param_dict == sample_item_dict


def test_from_dict_set_root(sample_item_dict: dict[str, Any]) -> None:
    catalog = Catalog(id="test", description="test desc")
    with pytest.warns(FutureWarning):
        item = Item.from_dict(sample_item_dict, root=catalog)
    assert item.get_root() is catalog


def test_set_self_href_does_not_break_asset_hrefs() -> None:
    cat = TestCases.case_2()
    for item in cat.get_items(recursive=True):
        for asset in item.assets.values():
            if utils.is_absolute_href(asset.href):
                asset.href = f"./{os.path.basename(asset.href)}"
        with pytest.warns(FutureWarning):
            item.set_self_href("http://example.com/item.json")
        for asset in item.assets.values():
            assert utils.is_absolute_href(asset.href)
