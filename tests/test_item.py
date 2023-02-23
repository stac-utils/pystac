from __future__ import annotations

import json
import os
import tempfile
import unittest
from copy import deepcopy
from typing import Any, Dict, Optional

import dateutil.relativedelta
import pytest

import pystac
import pystac.serialization.common_properties
from pystac import Asset, Catalog, Item
from pystac.utils import datetime_to_str, get_opt, is_absolute_href, str_to_datetime
from pystac.validation import validate_dict
from tests.utils import TestCases, assert_to_from_dict


class ItemTest(unittest.TestCase):
    def get_example_item_dict(self) -> Dict[str, Any]:
        m = TestCases.get_path("data-files/item/sample-item.json")
        with open(m) as f:
            item_dict: Dict[str, Any] = json.load(f)
        return item_dict

    def test_to_from_dict(self) -> None:
        self.maxDiff = None

        item_dict = self.get_example_item_dict()
        param_dict = deepcopy(item_dict)

        assert_to_from_dict(self, Item, param_dict)
        item = Item.from_dict(param_dict)
        self.assertEqual(item.id, "CS3-20160503_132131_05")

        # test asset creation additional field(s)
        self.assertEqual(
            item.assets["analytic"].extra_fields["product"],
            "http://cool-sat.com/catalog/products/analytic.json",
        )
        self.assertEqual(len(item.assets["thumbnail"].extra_fields), 0)

        # test that the parameter is preserved
        self.assertEqual(param_dict, item_dict)

        # assert that the parameter is preserved regardless of
        # preserve_dict
        _ = Item.from_dict(param_dict, preserve_dict=False)
        self.assertEqual(param_dict, item_dict)

    def test_from_dict_set_root(self) -> None:
        item_dict = self.get_example_item_dict()
        catalog = pystac.Catalog(id="test", description="test desc")
        item = Item.from_dict(item_dict, root=catalog)
        self.assertIs(item.get_root(), catalog)

    def test_set_self_href_does_not_break_asset_hrefs(self) -> None:
        cat = TestCases.case_2()
        for item in cat.get_all_items():
            for asset in item.assets.values():
                if is_absolute_href(asset.href):
                    asset.href = f"./{os.path.basename(asset.href)}"
            item.set_self_href("http://example.com/item.json")
            for asset in item.assets.values():
                self.assertTrue(is_absolute_href(asset.href))

    def test_set_self_href_none_ignores_relative_asset_hrefs(self) -> None:
        cat = TestCases.case_2()
        for item in cat.get_all_items():
            for asset in item.assets.values():
                if is_absolute_href(asset.href):
                    asset.href = f"./{os.path.basename(asset.href)}"
            item.set_self_href(None)
            for asset in item.assets.values():
                self.assertFalse(is_absolute_href(asset.href))

    def test_asset_absolute_href(self) -> None:
        item_path = TestCases.get_path("data-files/item/sample-item.json")
        item_dict = self.get_example_item_dict()
        item = Item.from_dict(item_dict)
        item.set_self_href(item_path)
        rel_asset = Asset("./data.geojson")
        rel_asset.set_owner(item)
        expected_href = os.path.abspath(
            os.path.join(os.path.dirname(item_path), "./data.geojson")
        )
        actual_href = rel_asset.get_absolute_href()
        self.assertEqual(expected_href, actual_href)

    def test_asset_absolute_href_no_item_self(self) -> None:
        item_dict = self.get_example_item_dict()
        item = Item.from_dict(item_dict)
        assert item.get_self_href() is None

        rel_asset = Asset("./data.geojson")
        rel_asset.set_owner(item)
        actual_href = rel_asset.get_absolute_href()
        self.assertEqual(None, actual_href)

    def test_extra_fields(self) -> None:
        item = pystac.Item.from_file(
            TestCases.get_path("data-files/item/sample-item.json")
        )

        item.extra_fields["test"] = "extra"

        with tempfile.TemporaryDirectory() as tmp_dir:
            p = os.path.join(tmp_dir, "item.json")
            item.save_object(include_self_link=False, dest_href=p)
            with open(p) as f:
                item_json = json.load(f)
            self.assertTrue("test" in item_json)
            self.assertEqual(item_json["test"], "extra")

            read_item = pystac.Item.from_file(p)
            self.assertTrue("test" in read_item.extra_fields)
            self.assertEqual(read_item.extra_fields["test"], "extra")

    def test_clearing_collection(self) -> None:
        collection = TestCases.case_4().get_child("acc")
        assert isinstance(collection, pystac.Collection)
        item = next(iter(collection.get_all_items()))
        self.assertEqual(item.collection_id, collection.id)
        item.set_collection(None)
        self.assertIsNone(item.collection_id)
        self.assertIsNone(item.get_collection())
        item.set_collection(collection)
        self.assertEqual(item.collection_id, collection.id)
        self.assertIs(item.get_collection(), collection)

    def test_datetime_ISO8601_format(self) -> None:
        item_dict = self.get_example_item_dict()

        item = Item.from_dict(item_dict)

        formatted_time = item.to_dict()["properties"]["datetime"]

        self.assertEqual("2016-05-03T13:22:30.040000Z", formatted_time)

    def test_null_datetime(self) -> None:
        item = pystac.Item.from_file(
            TestCases.get_path("data-files/item/sample-item.json")
        )

        with self.assertRaises(pystac.STACError):
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
                "start_datetime": datetime_to_str(get_opt(item.datetime)),
                "end_datetime": datetime_to_str(get_opt(item.datetime)),
            },
        )

        null_dt_item.validate()

    def test_get_assets(self) -> None:
        item = pystac.Item.from_file(
            TestCases.get_path("data-files/item/sample-item.json")
        )

        media_type_filter = item.get_assets(media_type=pystac.MediaType.COG)
        self.assertCountEqual(media_type_filter.keys(), ["analytic"])
        role_filter = item.get_assets(role="data")
        self.assertCountEqual(role_filter.keys(), ["analytic"])
        multi_filter = item.get_assets(
            media_type=pystac.MediaType.PNG, role="thumbnail"
        )
        self.assertCountEqual(multi_filter.keys(), ["thumbnail"])

        no_filter = item.get_assets()
        self.assertCountEqual(no_filter.keys(), ["analytic", "thumbnail"])
        no_assets = item.get_assets(media_type=pystac.MediaType.HDF)
        self.assertEqual(no_assets, {})

    def test_null_datetime_constructor(self) -> None:
        item = pystac.Item.from_file(
            TestCases.get_path("data-files/item/sample-item.json")
        )
        with self.assertRaises(pystac.STACError):
            Item(
                "test",
                geometry=item.geometry,
                bbox=item.bbox,
                datetime=None,
                end_datetime=item.datetime,
                properties={},
            )
        with self.assertRaises(pystac.STACError):
            Item(
                "test",
                geometry=item.geometry,
                bbox=item.bbox,
                datetime=None,
                start_datetime=item.datetime,
                properties={},
            )
        assert item.datetime
        null_dt_item = Item(
            "test",
            geometry=item.geometry,
            bbox=item.bbox,
            datetime=None,
            start_datetime=item.datetime,
            end_datetime=item.datetime + dateutil.relativedelta.relativedelta(days=1),
            properties={},
        )
        null_dt_item.validate()

    def test_get_set_asset_datetime(self) -> None:
        item = pystac.Item.from_file(
            TestCases.get_path("data-files/item/sample-item-asset-properties.json")
        )
        item_datetime = item.datetime

        # No property on asset
        self.assertEqual(item.get_datetime(item.assets["thumbnail"]), item.datetime)

        # Property on asset
        self.assertNotEqual(item.get_datetime(item.assets["analytic"]), item.datetime)
        self.assertEqual(
            item.get_datetime(item.assets["analytic"]),
            str_to_datetime("2017-05-03T13:22:30.040Z"),
        )

        item.set_datetime(
            str_to_datetime("2018-05-03T13:22:30.040Z"), item.assets["thumbnail"]
        )
        self.assertEqual(item.get_datetime(), item_datetime)
        self.assertEqual(
            item.get_datetime(item.assets["thumbnail"]),
            str_to_datetime("2018-05-03T13:22:30.040Z"),
        )

    def test_read_eo_item_owns_asset(self) -> None:
        item = next(iter(TestCases.case_1().get_all_items()))
        assert len(item.assets) > 0
        for asset_key in item.assets:
            self.assertEqual(item.assets[asset_key].owner, item)

    def test_null_geometry(self) -> None:
        m = TestCases.get_path(
            "data-files/examples/1.0.0-beta.2/item-spec/examples/null-geom-item.json"
        )
        with open(m) as f:
            item_dict = json.load(f)

        validate_dict(item_dict, pystac.STACObjectType.ITEM)

        item = Item.from_dict(item_dict)
        self.assertIsInstance(item, Item)
        item.validate()

        item_dict = item.to_dict()
        self.assertIsNone(item_dict["geometry"])
        self.assertNotIn("bbox", item_dict)

    def test_0_9_item_with_no_extensions_does_not_read_collection_data(self) -> None:
        item_json = pystac.StacIO.default().read_json(
            TestCases.get_path("data-files/examples/hand-0.9.0/010100/010100.json")
        )
        assert item_json.get("stac_extensions") is None
        assert item_json.get("stac_version") == "0.9.0"

        did_merge = pystac.serialization.common_properties.merge_common_properties(
            item_json
        )
        self.assertFalse(did_merge)

    def test_clone_preserves_assets(self) -> None:
        cat = TestCases.case_2()
        original_item = next(iter(cat.get_all_items()))
        assert len(original_item.assets) > 0
        assert all(
            asset.owner is original_item for asset in original_item.assets.values()
        )

        cloned_item = original_item.clone()

        for key in original_item.assets:
            with self.subTest(f"Preserves {key} asset"):
                self.assertIn(key, cloned_item.assets)
            cloned_asset = cloned_item.assets.get(key)
            if cloned_asset is not None:
                with self.subTest(f"Sets owner for {key}"):
                    self.assertIs(cloned_asset.owner, cloned_item)

    def test_make_asset_href_relative_is_noop_on_relative_hrefs(self) -> None:
        cat = TestCases.case_2()
        item = next(iter(cat.get_all_items()))
        asset = list(item.assets.values())[0]
        assert not is_absolute_href(asset.href)
        original_href = asset.get_absolute_href()

        item.make_asset_hrefs_relative()
        self.assertEqual(asset.get_absolute_href(), original_href)

    def test_from_invalid_dict_raises_exception(self) -> None:
        stac_io = pystac.StacIO.default()
        catalog_dict = stac_io.read_json(
            TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
        )
        with self.assertRaises(pystac.STACTypeError):
            _ = pystac.Item.from_dict(catalog_dict)

    def test_geo_interface(self) -> None:
        item = pystac.Item.from_file(
            TestCases.get_path("data-files/item/sample-item.json")
        )
        self.assertEqual(item.geometry, item.__geo_interface__)

    def test_relative_extension_path(self) -> None:
        item = pystac.Item.from_file(
            TestCases.get_path(
                "data-files/item/sample-item-with-relative-extension-path.json"
            )
        )
        item.validate()


class ItemSubClassTest(unittest.TestCase):
    """This tests cases related to creating classes inheriting from pystac.Catalog to
    ensure that inheritance, class methods, etc. function as expected."""

    SAMPLE_ITEM = TestCases.get_path("data-files/item/sample-item.json")

    class BasicCustomItem(pystac.Item):
        pass

    def setUp(self) -> None:
        self.stac_io = pystac.StacIO.default()

    def test_from_dict_returns_subclass(self) -> None:
        item_dict = self.stac_io.read_json(self.SAMPLE_ITEM)
        custom_item = self.BasicCustomItem.from_dict(item_dict)

        self.assertIsInstance(custom_item, self.BasicCustomItem)

    def test_from_file_returns_subclass(self) -> None:
        custom_item = self.BasicCustomItem.from_file(self.SAMPLE_ITEM)

        self.assertIsInstance(custom_item, self.BasicCustomItem)

    def test_clone(self) -> None:
        custom_item = self.BasicCustomItem.from_file(self.SAMPLE_ITEM)
        cloned_item = custom_item.clone()

        self.assertIsInstance(cloned_item, self.BasicCustomItem)


class AssetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        with open(TestCases.get_path("data-files/item/sample-item.json")) as src:
            item_dict = json.load(src)

        self.asset_dict = item_dict["assets"]["analytic"]

    def example_asset(self) -> Asset:
        return Asset.from_dict(self.asset_dict)

    def test_clone(self) -> None:
        original_asset = self.example_asset()
        cloned_asset = original_asset.clone()

        self.assertDictEqual(original_asset.to_dict(), self.asset_dict)
        self.assertDictEqual(cloned_asset.to_dict(), self.asset_dict)

        # Changes to original asset should not affect cloned Asset
        original_asset.description = "Some new description"
        self.assertDictEqual(cloned_asset.to_dict(), self.asset_dict)

        original_asset.href = "/path/to/new/href"
        self.assertDictEqual(cloned_asset.to_dict(), self.asset_dict)

        original_asset.title = "New Title"
        self.assertDictEqual(cloned_asset.to_dict(), self.asset_dict)

        original_asset.roles = ["new role"]
        self.assertDictEqual(cloned_asset.to_dict(), self.asset_dict)

        original_asset.roles.append("new role")
        self.assertDictEqual(cloned_asset.to_dict(), self.asset_dict)

        original_asset.extra_fields["new_field"] = "new_value"
        self.assertDictEqual(cloned_asset.to_dict(), self.asset_dict)


class AssetSubClassTest(unittest.TestCase):
    class CustomAsset(Asset):
        pass

    def setUp(self) -> None:
        self.maxDiff = None
        with open(TestCases.get_path("data-files/item/sample-item.json")) as src:
            item_dict = json.load(src)

        self.asset_dict = item_dict["assets"]["analytic"]

    def test_from_dict(self) -> None:
        asset = self.CustomAsset.from_dict(self.asset_dict)

        self.assertIsInstance(asset, self.CustomAsset)

    def test_clone(self) -> None:
        asset = self.CustomAsset.from_dict(self.asset_dict)
        cloned_asset = asset.clone()

        self.assertIsInstance(cloned_asset, self.CustomAsset)
        self.assertIsInstance(cloned_asset, self.CustomAsset)


def test_custom_item_from_dict(item: Item) -> None:
    # https://github.com/stac-utils/pystac/issues/862
    class CustomItem(Item):
        @classmethod
        def from_dict(
            cls,
            d: Dict[str, Any],
            href: Optional[str] = None,
            root: Optional[Catalog] = None,
            migrate: bool = False,
            preserve_dict: bool = True,
        ) -> CustomItem:
            return super().from_dict(d)

    _ = CustomItem.from_dict(item.to_dict())


def test_item_from_dict_raises_useful_error() -> None:
    item_dict = {"type": "Feature", "stac_version": "1.0.0", "id": "lalalalala"}
    with pytest.raises(pystac.STACError, match="Invalid Item: "):
        Item.from_dict(item_dict)


def test_item_from_dict_with_missing_stac_version_raises_useful_error() -> None:
    item_dict = {"type": "Feature", "id": "lalalalala"}
    with pytest.raises(pystac.STACTypeError, match="'stac_version' is missing"):
        Item.from_dict(item_dict)


def test_item_from_dict_with_missing_type_raises_useful_error() -> None:
    item_dict = {"stac_version": "0.8.0", "id": "lalalalala"}
    with pytest.raises(pystac.STACTypeError, match="'type' is missing"):
        Item.from_dict(item_dict)


@pytest.mark.parametrize("add_canonical", (True, False))
def test_remove_hierarchical_links(
    test_case_1_catalog: Catalog, add_canonical: bool
) -> None:
    item = list(test_case_1_catalog.get_all_items())[0]
    item.remove_hierarchical_links(add_canonical=add_canonical)
    for link in item.links:
        assert not link.is_hierarchical()
    assert bool(item.get_single_link("canonical")) == add_canonical
