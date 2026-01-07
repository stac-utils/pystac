from __future__ import annotations

import copy
import json
import os
import pickle
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import dateutil.relativedelta
import pytest

import pystac
import pystac.serialization.common_properties
from pystac import Asset, Catalog, Collection, Item, Link, STACValidationError
from pystac.utils import (
    datetime_to_str,
    get_opt,
    is_absolute_href,
    make_posix_style,
    str_to_datetime,
)
from pystac.validation import validate_dict

from .utils import TestCases, assert_to_from_dict


def test_to_from_dict(sample_item_dict: dict[str, Any]) -> None:
    param_dict = deepcopy(sample_item_dict)

    assert_to_from_dict(Item, param_dict)
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


def test_from_dict_set_root(sample_item_dict: dict[str, Any]) -> None:
    catalog = pystac.Catalog(id="test", description="test desc")
    item = Item.from_dict(sample_item_dict, root=catalog)
    assert item.get_root() is catalog


def test_set_self_href_does_not_break_asset_hrefs() -> None:
    cat = TestCases.case_2()
    for item in cat.get_items(recursive=True):
        for asset in item.assets.values():
            if is_absolute_href(asset.href):
                asset.href = f"./{os.path.basename(asset.href)}"
        item.set_self_href("http://example.com/item.json")
        for asset in item.assets.values():
            assert is_absolute_href(asset.href)


def test_set_self_href_none_ignores_relative_asset_hrefs() -> None:
    cat = TestCases.case_2()
    for item in cat.get_items(recursive=True):
        for asset in item.assets.values():
            if is_absolute_href(asset.href):
                asset.href = f"./{os.path.basename(asset.href)}"
        item.set_self_href(None)
        for asset in item.assets.values():
            assert not is_absolute_href(asset.href)


def test_asset_absolute_href(sample_item: Item) -> None:
    item_path = TestCases.get_path("data-files/item/sample-item.json")
    sample_item.set_self_href(item_path)
    rel_asset = Asset("./data.geojson")
    rel_asset.set_owner(sample_item)
    expected_href = make_posix_style(
        os.path.abspath(os.path.join(os.path.dirname(item_path), "./data.geojson"))
    )
    actual_href = rel_asset.get_absolute_href()
    assert expected_href == actual_href


def test_asset_absolute_href_no_item_self(sample_item_dict: dict[str, Any]) -> None:
    item = Item.from_dict(sample_item_dict)
    assert item.get_self_href() is None

    rel_asset = Asset("./data.geojson")
    rel_asset.set_owner(item)
    actual_href = rel_asset.get_absolute_href()
    assert actual_href is None


def test_item_field_order() -> None:
    item = pystac.Item.from_file(TestCases.get_path("data-files/item/sample-item.json"))
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


def test_extra_fields() -> None:
    item = pystac.Item.from_file(TestCases.get_path("data-files/item/sample-item.json"))

    item.extra_fields["test"] = "extra"

    with tempfile.TemporaryDirectory() as tmp_dir:
        p = os.path.join(tmp_dir, "item.json")
        item.save_object(include_self_link=False, dest_href=p)
        with open(p) as f:
            item_json = json.load(f)
        assert "test" in item_json
        assert item_json["test"] == "extra"

        read_item = pystac.Item.from_file(p)
        assert "test" in read_item.extra_fields
        assert read_item.extra_fields["test"] == "extra"


def test_clearing_collection() -> None:
    collection = TestCases.case_4().get_child("acc")
    assert isinstance(collection, pystac.Collection)
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


@pytest.mark.vcr()
def test_null_datetime() -> None:
    item = pystac.Item.from_file(TestCases.get_path("data-files/item/sample-item.json"))

    with pytest.raises(pystac.STACError):
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


def test_get_assets() -> None:
    item = pystac.Item.from_file(TestCases.get_path("data-files/item/sample-item.json"))

    media_type_filter = item.get_assets(media_type=pystac.MediaType.COG)
    assert set(media_type_filter.keys()) == {"analytic"}
    role_filter = item.get_assets(role="data")
    assert set(role_filter.keys()) == {"analytic"}
    multi_filter = item.get_assets(media_type=pystac.MediaType.PNG, role="thumbnail")
    assert set(multi_filter.keys()) == {"thumbnail"}
    multi_filter["thumbnail"].description = "foo"
    assert item.assets["thumbnail"].description != "foo"

    no_filter = item.get_assets()
    assert set(no_filter.keys()) == {"analytic", "thumbnail"}
    no_assets = item.get_assets(media_type=pystac.MediaType.HDF)
    assert no_assets == {}


@pytest.mark.vcr()
def test_null_datetime_constructor() -> None:
    item = pystac.Item.from_file(TestCases.get_path("data-files/item/sample-item.json"))
    with pytest.raises(pystac.STACError):
        Item(
            "test",
            geometry=item.geometry,
            bbox=item.bbox,
            datetime=None,
            end_datetime=item.datetime,
            properties={},
        )
    with pytest.raises(pystac.STACError):
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


def test_get_set_asset_datetime() -> None:
    item = pystac.Item.from_file(
        TestCases.get_path("data-files/item/sample-item-asset-properties.json")
    )
    item_datetime = item.datetime

    # No property on asset
    assert item.get_datetime(item.assets["thumbnail"]) == item.datetime

    # Property on asset
    assert item.get_datetime(item.assets["analytic"]) != item.datetime
    assert item.get_datetime(item.assets["analytic"]) == str_to_datetime(
        "2017-05-03T13:22:30.040Z"
    )

    item.set_datetime(
        str_to_datetime("2018-05-03T13:22:30.040Z"), item.assets["thumbnail"]
    )
    assert item.get_datetime() == item_datetime
    assert item.get_datetime(item.assets["thumbnail"]) == str_to_datetime(
        "2018-05-03T13:22:30.040Z"
    )


def test_read_eo_item_owns_asset() -> None:
    item = next(TestCases.case_1().get_items(recursive=True))
    assert len(item.assets) > 0
    for asset_key in item.assets:
        assert item.assets[asset_key].owner == item


@pytest.mark.vcr()
def test_null_geometry() -> None:
    m = TestCases.get_path(
        "data-files/examples/1.0.0-beta.2/item-spec/examples/null-geom-item.json"
    )
    with open(m) as f:
        item_dict = json.load(f)

    validate_dict(item_dict, pystac.STACObjectType.ITEM)

    item = Item.from_dict(item_dict)
    assert isinstance(item, Item)
    item.validate()

    item_dict = item.to_dict()
    assert item_dict["geometry"] is None
    assert "bbox" not in item_dict


def test_0_9_item_with_no_extensions_does_not_read_collection_data() -> None:
    item_json = pystac.StacIO.default().read_json(
        TestCases.get_path("data-files/examples/hand-0.9.0/010100/010100.json")
    )
    assert item_json.get("stac_extensions") is None
    assert item_json.get("stac_version") == "0.9.0"

    did_merge = pystac.serialization.common_properties.merge_common_properties(
        item_json
    )
    assert not did_merge


def test_clone_preserves_assets() -> None:
    cat = TestCases.case_2()
    original_item = next(cat.get_items(recursive=True))
    assert len(original_item.assets) > 0
    assert all(asset.owner is original_item for asset in original_item.assets.values())

    cloned_item = original_item.clone()

    for key in original_item.assets:
        assert key in cloned_item.assets, f"Failed to preserve asset {key}"
        cloned_asset = cloned_item.assets.get(key)
        if cloned_asset is not None:
            assert cloned_asset.owner is cloned_item, f"Failed set owner for {key}"


def test_make_asset_href_relative_is_noop_on_relative_hrefs() -> None:
    cat = TestCases.case_2()
    item = next(cat.get_items(recursive=True))
    asset = list(item.assets.values())[0]
    assert not is_absolute_href(asset.href)
    original_href = asset.get_absolute_href()

    item.make_asset_hrefs_relative()
    assert asset.get_absolute_href() == original_href


def test_from_invalid_dict_raises_exception() -> None:
    stac_io = pystac.StacIO.default()
    catalog_dict = stac_io.read_json(
        TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
    )
    with pytest.raises(pystac.STACTypeError):
        _ = pystac.Item.from_dict(catalog_dict)


@pytest.mark.vcr()
def test_relative_extension_path() -> None:
    item = pystac.Item.from_file(
        TestCases.get_path(
            "data-files/item/sample-item-with-relative-extension-path.json"
        )
    )
    item.validate()


class TestItemSubClass:
    """This tests cases related to creating classes inheriting from pystac.Catalog to
    ensure that inheritance, class methods, etc. function as expected."""

    SAMPLE_ITEM = TestCases.get_path("data-files/item/sample-item.json")

    class BasicCustomItem(pystac.Item):
        pass

    def test_from_dict_returns_subclass(self) -> None:
        stac_io = pystac.StacIO.default()
        item_dict = stac_io.read_json(self.SAMPLE_ITEM)
        custom_item = self.BasicCustomItem.from_dict(item_dict)

        assert isinstance(custom_item, self.BasicCustomItem)

    def test_from_file_returns_subclass(self) -> None:
        custom_item = self.BasicCustomItem.from_file(self.SAMPLE_ITEM)

        assert isinstance(custom_item, self.BasicCustomItem)

    def test_clone(self) -> None:
        custom_item = self.BasicCustomItem.from_file(self.SAMPLE_ITEM)
        cloned_item = custom_item.clone()

        assert isinstance(cloned_item, self.BasicCustomItem)


def test_asset_clone() -> None:
    with open(TestCases.get_path("data-files/item/sample-item.json")) as src:
        item_dict = json.load(src)
    asset_dict = item_dict["assets"]["analytic"]
    original_asset = Asset.from_dict(asset_dict)

    cloned_asset = original_asset.clone()

    assert original_asset.to_dict() == asset_dict
    assert cloned_asset.to_dict() == asset_dict

    # Changes to original asset should not affect cloned Asset
    original_asset.description = "Some new description"
    original_asset.href = "/path/to/new/href"
    original_asset.title = "New Title"
    original_asset.roles = ["new role"]
    original_asset.roles.append("new role")
    original_asset.extra_fields["new_field"] = "new_value"
    assert cloned_asset.to_dict() == asset_dict


class TestAssetSubClass:
    class CustomAsset(Asset):
        pass

    AssetDict = dict[str, str | list[str]]

    @pytest.fixture
    def asset_dict(self) -> AssetDict:
        with open(TestCases.get_path("data-files/item/sample-item.json")) as src:
            item_dict = json.load(src)
        return cast(TestAssetSubClass.AssetDict, item_dict["assets"]["analytic"])

    def test_from_dict(self, asset_dict: AssetDict) -> None:
        asset = self.CustomAsset.from_dict(asset_dict)
        assert isinstance(asset, self.CustomAsset)

    def test_clone(self, asset_dict: AssetDict) -> None:
        asset = self.CustomAsset.from_dict(asset_dict)
        cloned_asset = asset.clone()
        assert isinstance(cloned_asset, self.CustomAsset)


def test_custom_item_from_dict(item: Item) -> None:
    # https://github.com/stac-utils/pystac/issues/862
    class CustomItem(Item):
        @classmethod
        def from_dict(
            cls,
            d: dict[str, Any],
            href: str | None = None,
            root: Catalog | None = None,
            migrate: bool = True,
            preserve_dict: bool = True,
        ) -> CustomItem:
            return super().from_dict(d)

    _ = CustomItem.from_dict(item.to_dict())


def test_item_from_dict_raises_useful_error() -> None:
    item_dict = {"type": "Feature", "stac_version": "1.1.0", "id": "lalalalala"}
    with pytest.raises(pystac.STACError, match="Invalid Item: "):
        Item.from_dict(item_dict)


def test_item_from_dict_with_missing_stac_version_raises_useful_error() -> None:
    item_dict = {"type": "Feature", "id": "lalalalala"}
    with pytest.raises(pystac.STACTypeError, match="'stac_version' is missing"):
        Item.from_dict(item_dict, migrate=False)


def test_item_from_dict_with_missing_type_raises_useful_error() -> None:
    item_dict = {"stac_version": "0.8.0", "id": "lalalalala"}
    with pytest.raises(pystac.STACTypeError, match="'type' is missing"):
        Item.from_dict(item_dict, migrate=False)


@pytest.mark.parametrize("add_canonical", (True, False))
def test_remove_hierarchical_links(
    test_case_1_catalog: Catalog, add_canonical: bool
) -> None:
    item = next(test_case_1_catalog.get_items(recursive=True))
    item.remove_hierarchical_links(add_canonical=add_canonical)
    for link in item.links:
        assert not link.is_hierarchical()
    assert bool(item.get_single_link("canonical")) == add_canonical


def test_geo_interface() -> None:
    item = pystac.Item.from_file(TestCases.get_path("data-files/item/sample-item.json"))
    assert (
        item.to_dict(include_self_link=False, transform_hrefs=False)
        == item.__geo_interface__
    )


def test_duplicate_self_links(tmp_path: Path, sample_item: pystac.Item) -> None:
    # https://github.com/stac-utils/pystac/issues/1102
    assert len(sample_item.get_links(rel="self")) == 1
    path = tmp_path / "item.json"
    sample_item.save_object(include_self_link=True, dest_href=str(path))
    sample_item = Item.from_file(path)
    assert len(sample_item.get_links(rel="self")) == 1


def test_get_derived_from_when_none_exists(test_case_1_catalog: Catalog) -> None:
    item = next(test_case_1_catalog.get_items(recursive=True))
    assert item.get_derived_from() == []
    for link in item.links:
        assert link.rel != pystac.RelType.DERIVED_FROM
    assert item.get_single_link(pystac.RelType.DERIVED_FROM) is None


def test_add_derived_from(test_case_1_catalog: Catalog) -> None:
    items = list(test_case_1_catalog.get_items(recursive=True))
    item_0 = items[0]
    item_1 = items[1]
    item_2 = items[2]
    item_0.add_derived_from(item_1, item_2.self_href)
    derived_from = item_0.get_derived_from()
    assert len(derived_from) == 2
    assert derived_from[0].id == item_1.id
    assert derived_from[1].id == item_2.id
    filtered = [
        link for link in item_0.links if link.rel == pystac.RelType.DERIVED_FROM
    ]
    assert len(filtered) == 2
    assert filtered[0].to_dict(transform_href=False)["href"] == item_1.self_href
    assert filtered[1].to_dict(transform_href=False)["href"] == item_2.self_href


def test_get_unresolvable_derived_from(test_case_1_catalog: Catalog) -> None:
    item = next(test_case_1_catalog.get_items(recursive=True))
    item.add_derived_from("foo")
    with pytest.raises(
        pystac.STACError, match="Link failed to resolve. Use get_links instead"
    ):
        item.get_derived_from()

    links = item.get_links(pystac.RelType.DERIVED_FROM)
    assert len(links) == 1


def test_remove_unresolvable_derived_from(test_case_1_catalog: Catalog) -> None:
    item = next(test_case_1_catalog.get_items(recursive=True))
    item.add_derived_from("foo")
    with pytest.raises(
        pystac.STACError, match="Link failed to resolve. Use remove_links instead"
    ):
        item.remove_derived_from("foo")

    item.remove_links(pystac.RelType.DERIVED_FROM)
    assert item.get_derived_from() == []


def test_remove_derived_from(test_case_1_catalog: Catalog) -> None:
    items = list(test_case_1_catalog.get_items(recursive=True))
    item_0 = items[0]
    item_1 = items[1]
    item_0.add_derived_from(item_1)
    item_0.remove_derived_from(item_1.id)
    assert item_0.get_derived_from() == []
    for link in item_0.links:
        assert link.rel != pystac.RelType.DERIVED_FROM
    assert item_0.get_single_link(pystac.RelType.DERIVED_FROM) is None


def test_delete_asset(tmp_asset: Asset) -> None:
    asset = tmp_asset
    href = asset.get_absolute_href()
    item = asset.owner

    assert href is not None
    assert item is not None

    name = next(k for k in item.assets.keys() if item.assets[k] == asset)
    item.delete_asset(name)

    assert name not in item.assets
    assert not os.path.exists(href)


def test_delete_asset_relative_no_self_link_fails(tmp_asset: pystac.Asset) -> None:
    asset = tmp_asset
    href = asset.get_absolute_href()
    item = asset.owner

    assert href is not None
    assert item is not None
    assert isinstance(item, pystac.Item)

    item.set_self_href(None)

    name = next(k for k in item.assets.keys() if item.assets[k] == asset)
    with pytest.raises(ValueError, match="Cannot delete file") as e:
        item.delete_asset(name)

    assert asset.href in str(e.value)
    assert name in item.assets
    assert os.path.exists(href)


def test_resolve_collection_with_root(
    tmp_path: Path, item: Item, collection: Collection
) -> None:
    # Motivated by https://github.com/stac-utils/pystac-client/issues/548
    catalog = Catalog("root", "the description")
    item.set_root(catalog)

    collection_path = str(tmp_path / "collection.json")
    collection.save_object(
        include_self_link=False,
        dest_href=collection_path,
    )
    item.add_link(Link(rel="collection", target=collection_path))

    read_collection = item.get_collection()
    assert read_collection
    root = read_collection.get_root()
    assert root
    assert root.id == "root"


@pytest.mark.vcr()
def test_non_hierarchical_relative_link() -> None:
    root = pystac.Catalog("root", "root")
    a = pystac.Catalog("a", "a")
    b = pystac.Catalog("b", "b")

    root.add_child(a)
    root.add_child(b)
    a.add_link(pystac.Link("related", b))
    b.add_link(
        pystac.Link("item", TestCases.get_path("data-files/item/sample-item.json"))
    )

    root.catalog_type = pystac.catalog.CatalogType.SELF_CONTAINED
    root.normalize_hrefs("test_output")
    related_href = [link for link in a.links if link.rel == "related"][0].get_href()

    assert related_href is not None and not is_absolute_href(related_href)
    assert a.target_in_hierarchy(b)
    assert root.target_in_hierarchy(next(b.get_items()))
    assert root.target_in_hierarchy(root)


def test_pathlib() -> None:
    # This works, but breaks mypy until we fix
    # https://github.com/stac-utils/pystac/issues/1216
    Item.from_file(Path(TestCases.get_path("data-files/item/sample-item.json")))


def test_invalid_error_message(item: Item) -> None:
    item.extra_fields["collection"] = "can't have a collection"
    with pytest.raises(STACValidationError) as error:
        item.validate()
    assert "can't have a collection" in str(error.value)


def test_pickle_with_no_links(item: Item) -> None:
    roundtripped = pickle.loads(pickle.dumps(item))
    for attr in ["id", "geometry", "bbox", "datetime", "links"]:
        assert getattr(roundtripped, attr) == getattr(item, attr)


def test_pickle_with_hrefless_links(item: Item) -> None:
    root = pystac.Catalog("root", "root")
    a = pystac.Catalog("a", "a")

    item.add_link(pystac.Link("related", a))
    item.add_link(
        pystac.Link("item", TestCases.get_path("data-files/item/sample-item.json"))
    )
    item.set_root(root)

    roundtripped = pickle.loads(pickle.dumps(item))
    for original, new in zip(item.links, roundtripped.links):
        assert original.rel == new.rel
        assert original.media_type == new.media_type
        assert str(original.owner) == str(new.owner)
        assert str(original.target) == str(new.target)


def test_pickle_with_only_href_links(item: Item) -> None:
    item.add_link(
        pystac.Link("item", TestCases.get_path("data-files/item/sample-item.json"))
    )

    roundtripped = pickle.loads(pickle.dumps(item))
    for original, new in zip(item.links, roundtripped.links):
        assert original.rel == new.rel
        assert original.media_type == new.media_type
        assert str(original.owner) == str(new.owner)
        assert str(original.target) == str(new.target)


def test_copy_with_unresolveable_root(item: Item) -> None:
    item.add_link(
        pystac.Link(
            "root", "s3://naip-visualization/this-is-a-non-existent-catalog.json"
        )
    )
    copy.deepcopy(item)


def test_no_collection(item: Item) -> None:
    # https://github.com/stac-utils/stac-api-validator/issues/527
    assert item.collection is None


def test_migrate_by_default() -> None:
    with open(
        TestCases.get_path("data-files/projection/example-with-version-1.1.json")
    ) as f:
        data = json.load(f)
    item = pystac.Item.from_dict(data)  # default used to be migrate=False
    assert item.ext.proj.code == "EPSG:32614"


def test_clone_extra_fields(item: Item) -> None:
    item.extra_fields["foo"] = "bar"
    cloned = item.clone()
    assert cloned.extra_fields["foo"] == "bar"
