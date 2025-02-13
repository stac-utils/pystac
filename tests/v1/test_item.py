from copy import deepcopy
from typing import Any

from pystac import Item

from . import utils


def test_to_from_dict(sample_item_dict: dict[str, Any]) -> None:
    param_dict = deepcopy(sample_item_dict)

    utils.assert_to_from_dict(Item, param_dict)
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
    Item.from_dict(param_dict, preserve_dict=False)
    assert param_dict == sample_item_dict
