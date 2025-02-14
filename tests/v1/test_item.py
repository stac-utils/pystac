import json
import os.path
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from pystac import Asset, Catalog, Collection, Item, STACError, utils

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


def test_set_self_href_none_ignores_relative_asset_hrefs() -> None:
    cat = TestCases.case_2()
    for item in cat.get_items(recursive=True):
        for asset in item.assets.values():
            if utils.is_absolute_href(asset.href):
                asset.href = f"./{os.path.basename(asset.href)}"
        with pytest.warns(FutureWarning):
            item.set_self_href(None)
        for asset in item.assets.values():
            assert not utils.is_absolute_href(asset.href)


def test_asset_absolute_href(sample_item: Item) -> None:
    item_path = TestCases.get_path("data-files/item/sample-item.json")
    with pytest.warns(FutureWarning):
        sample_item.set_self_href(item_path)
    rel_asset = Asset("./data.geojson")
    with pytest.warns(FutureWarning):
        rel_asset.set_owner(sample_item)
    expected_href = utils.make_posix_style(
        os.path.abspath(os.path.join(os.path.dirname(item_path), "./data.geojson"))
    )
    with pytest.warns(FutureWarning):
        actual_href = rel_asset.get_absolute_href()
    assert expected_href == actual_href


def test_asset_absolute_href_no_item_self(sample_item_dict: dict[str, Any]) -> None:
    item = Item.from_dict(sample_item_dict)
    with pytest.warns(FutureWarning):
        assert item.get_self_href() is None

    rel_asset = Asset("./data.geojson")
    with pytest.warns(FutureWarning):
        rel_asset.set_owner(item)
    with pytest.warns(FutureWarning):
        actual_href = rel_asset.get_absolute_href()
    assert actual_href is None


def test_item_field_order() -> None:
    item = Item.from_file(TestCases.get_path("data-files/item/sample-item.json"))
    with pytest.warns(FutureWarning):
        item_dict = item.to_dict(include_self_link=False)
    expected_order = [
        "type",
        "stac_version",
        "stac_extensions",
        "id",
        "geometry",
        "bbox",
        "properties",
        "links",
        "assets",
        "collection",
    ]
    actual_order = list(item_dict.keys())
    assert actual_order == expected_order


def test_extra_fields(tmp_path: Path) -> None:
    item = Item.from_file(TestCases.get_path("data-files/item/sample-item.json"))

    item.extra_fields["test"] = "extra"

    p = os.path.join(tmp_path, "item.json")
    with pytest.warns(FutureWarning):
        item.save_object(include_self_link=False, dest_href=p)
    with open(p) as f:
        item_json = json.load(f)
    assert "test" in item_json
    assert item_json["test"] == "extra"

    read_item = Item.from_file(p)
    assert "test" in read_item.extra_fields
    assert read_item.extra_fields["test"] == "extra"


def test_clearing_collection() -> None:
    collection = TestCases.case_4().get_child("acc")
    assert isinstance(collection, Collection)
    item = next(collection.get_items(recursive=True))
    assert item.collection_id == collection.id
    item.set_collection(None)
    assert item.collection_id is None
    assert item.get_collection() is None
    item.set_collection(collection)
    assert item.collection_id == collection.id
    assert item.get_collection() is collection


def test_datetime_ISO8601_format(sample_item: Item) -> None:
    formatted_time = sample_item.to_dict()["properties"]["datetime"]
    assert "2016-05-03T13:22:30.040000Z" == formatted_time


@pytest.mark.xfail
def test_null_datetime() -> None:
    item = Item.from_file(TestCases.get_path("data-files/item/sample-item.json"))

    with pytest.raises(STACError):
        Item(
            "test",
            geometry=item.geometry,
            bbox=item.bbox,
            datetime=None,
            properties={},
        )

    null_dt_item = Item(
        "test",
        geometry=item.geometry,
        bbox=item.bbox,
        datetime=None,
        properties={
            "start_datetime": utils.datetime_to_str(utils.get_opt(item.datetime)),
            "end_datetime": utils.datetime_to_str(utils.get_opt(item.datetime)),
        },
    )

    null_dt_item.validate()


def test_null_datetime_relaxed() -> None:
    item = Item.from_file(TestCases.get_path("data-files/item/sample-item.json"))

    Item(
        "test",
        geometry=item.geometry,
        bbox=item.bbox,
        datetime=None,
        properties={},
    )

    null_dt_item = Item(
        "test",
        geometry=item.geometry,
        bbox=item.bbox,
        datetime=None,
        properties={
            "start_datetime": utils.datetime_to_str(utils.get_opt(item.datetime)),
            "end_datetime": utils.datetime_to_str(utils.get_opt(item.datetime)),
        },
    )

    null_dt_item.validate()
