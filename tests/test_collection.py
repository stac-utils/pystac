from __future__ import annotations

import json
import os
import tempfile
import unittest
from collections.abc import Iterator
from copy import deepcopy
from datetime import datetime
from typing import Any

import pytest
from dateutil import tz

import pystac
from pystac import (
    Asset,
    Catalog,
    CatalogType,
    Collection,
    Extent,
    Item,
    Provider,
    SpatialExtent,
    TemporalExtent,
)
from pystac.extensions.eo import EOExtension
from pystac.utils import datetime_to_str, get_required, str_to_datetime
from pystac.validation import validate_dict
from tests.utils import ARBITRARY_BBOX, ARBITRARY_GEOM, TestCases

TEST_DATETIME = datetime(2020, 3, 14, 16, 32)


def test_provider_to_from_dict() -> None:
    provider_dict = {
        "name": "Remote Data, Inc",
        "description": "Producers of awesome spatiotemporal assets",
        "roles": ["producer", "processor"],
        "url": "http://remotedata.io",
        "extension:field": "some value",
    }
    expected_extra_fields = {"extension:field": provider_dict["extension:field"]}

    provider = Provider.from_dict(provider_dict)

    assert (
        provider_dict["name"],
        provider_dict["description"],
        provider_dict["roles"],
        provider_dict["url"],
        expected_extra_fields,
        provider_dict,
    ) == (
        provider.name,
        provider.description,
        provider.roles,
        provider.url,
        provider.extra_fields,
        provider.to_dict(),
    )


def test_spatial_extent_from_coordinates() -> None:
    extent = SpatialExtent.from_coordinates(ARBITRARY_GEOM["coordinates"])

    assert len(extent.bboxes) == 1
    bbox = extent.bboxes[0]
    assert len(bbox) == 4
    for x in bbox:
        assert isinstance(x, float)

def test_read_eo_items_are_heritable() -> None:
    cat = TestCases.case_5()
    item = next(cat.get_items(recursive=True))

    assert EOExtension.has_extension(item)

def test_save_uses_previous_catalog_type() -> None:
    collection = TestCases.case_8()
    assert collection.STAC_OBJECT_TYPE == pystac.STACObjectType.COLLECTION
    assert collection.catalog_type == CatalogType.SELF_CONTAINED
    with tempfile.TemporaryDirectory() as tmp_dir:
        collection.normalize_hrefs(tmp_dir)
        href = collection.self_href
        collection.save()

        collection2 = pystac.Collection.from_file(href)
        assert collection2.catalog_type == CatalogType.SELF_CONTAINED

def test_clone_uses_previous_catalog_type() -> None:
    catalog = TestCases.case_8()
    assert catalog.catalog_type == CatalogType.SELF_CONTAINED
    clone = catalog.clone()
    assert clone.catalog_type == CatalogType.SELF_CONTAINED

def test_clone_cant_mutate_original() -> None:
    collection = TestCases.case_8()
    assert collection.keywords == ["disaster", "open"]
    clone = collection.clone()
    clone.extra_fields["test"] = "extra"
    assert "test" not in collection.extra_fields
    assert clone.keywords is not None
    clone.keywords.append("clone")
    assert clone.keywords == ["disaster", "open", "clone"]
    assert collection.keywords == ["disaster", "open"]
    assert id(collection.summaries) != id(clone.summaries)

def test_multiple_extents() -> None:
    cat1 = TestCases.case_1()
    country = cat1.get_child("country-1")
    assert country is not None
    col1 = country.get_child("area-1-1")
    assert col1 is not None
    col1.validate()
    assert isinstance(col1, Collection)
    validate_dict(col1.to_dict(), pystac.STACObjectType.COLLECTION)

    multi_ext_uri = TestCases.get_path("data-files/collections/multi-extent.json")
    with open(multi_ext_uri) as f:
        multi_ext_dict = json.load(f)
    validate_dict(multi_ext_dict, pystac.STACObjectType.COLLECTION)
    assert isinstance(Collection.from_dict(multi_ext_dict), Collection)

    multi_ext_col = Collection.from_file(multi_ext_uri)
    multi_ext_col.validate()
    ext = multi_ext_col.extent
    extent_dict = multi_ext_dict["extent"]
    assert isinstance(ext, Extent)
    assert isinstance(ext.spatial.bboxes[0], list)
    assert len(ext.spatial.bboxes) == 3
    assert ext.to_dict() == extent_dict

    cloned_ext = ext.clone()
    assert cloned_ext.to_dict() == multi_ext_dict["extent"]

def test_extra_fields() -> None:
    catalog = TestCases.case_2()
    collection = catalog.get_child("1a8c1632-fa91-4a62-b33e-3a87c2ebdf16")
    assert collection is not None

    collection.extra_fields["test"] = "extra"

    with tempfile.TemporaryDirectory() as tmp_dir:
        p = os.path.join(tmp_dir, "collection.json")
        collection.save_object(include_self_link=False, dest_href=p)
        with open(p) as f:
            col_json = json.load(f)
        assert "test" in col_json
        assert col_json["test"] == "extra"

        read_col = pystac.Collection.from_file(p)
        assert "test" in read_col.extra_fields
        assert read_col.extra_fields["test"] == "extra"

def test_update_extents() -> None:
    catalog = TestCases.case_2()
    base_collection = catalog.get_child("1a8c1632-fa91-4a62-b33e-3a87c2ebdf16")
    assert isinstance(base_collection, Collection)
    base_extent = base_collection.extent
    collection = base_collection.clone()

    item1 = Item(
        id="test-item-1",
        geometry=ARBITRARY_GEOM,
        bbox=[-180, -90, 180, 90],
        datetime=TEST_DATETIME,
        properties={"key": "one"},
        stac_extensions=["eo", "commons"],
    )

    item2 = Item(
        id="test-item-1",
        geometry=ARBITRARY_GEOM,
        bbox=[-180, -90, 180, 90],
        datetime=None,
        properties={
            "start_datetime": datetime_to_str(datetime(2000, 1, 1, 12, 0, 0, 0)),
            "end_datetime": datetime_to_str(datetime(2000, 2, 1, 12, 0, 0, 0)),
        },
        stac_extensions=["eo", "commons"],
    )

    collection.add_item(item1)

    collection.update_extent_from_items()
    assert [[-180, -90, 180, 90]] == collection.extent.spatial.bboxes
    assert len(base_extent.spatial.bboxes[0]) == len(collection.extent.spatial.bboxes[0])
    assert base_extent.temporal.intervals != collection.extent.temporal.intervals

    collection.remove_item("test-item-1")
    collection.update_extent_from_items()
    assert [[-180, -90, 180, 90]] != collection.extent.spatial.bboxes
    collection.add_item(item2)

    collection.update_extent_from_items()

    assert ( [ [ item2.common_metadata.start_datetime,
                base_extent.temporal.intervals[0][1],
            ] ] == collection.extent.temporal.intervals )

def test_supplying_href_in_init_does_not_fail() -> None:
    test_href = "http://example.com/collection.json"
    spatial_extent = SpatialExtent(bboxes=[ARBITRARY_BBOX])
    temporal_extent = TemporalExtent(intervals=[[TEST_DATETIME, None]])

    collection_extent = Extent(spatial=spatial_extent, temporal=temporal_extent)
    collection = Collection(
        id="test", description="test desc", extent=collection_extent, href=test_href
    )

    assert collection.get_self_href() == test_href

def test_collection_with_href_caches_by_href() -> None:
    collection = pystac.Collection.from_file(
        TestCases.get_path("data-files/examples/hand-0.8.1/collection.json")
    )
    cache = collection._resolved_objects

    # Since all of our STAC objects have HREFs, everything should be
    # cached only by HREF
    assert len(cache.id_keys_to_objects) == 0

@pytest.mark.block_network
def test_assets() -> None:
    path = TestCases.get_path("data-files/collections/with-assets.json")
    with open(path) as f:
        data = json.load(f)
    collection = pystac.Collection.from_dict(data)
    collection.validate()

def test_get_assets() -> None:
    collection = pystac.Collection.from_file(
        TestCases.get_path("data-files/collections/with-assets.json")
    )

    media_type_filter = collection.get_assets(media_type=pystac.MediaType.PNG)
    assert list(media_type_filter.keys()) == ["thumbnail"]
    role_filter = collection.get_assets(role="thumbnail")
    assert list(role_filter.keys()) == ["thumbnail"]
    multi_filter = collection.get_assets(
        media_type=pystac.MediaType.PNG, role="thumbnail"
    )
    assert list(multi_filter.keys()) == ["thumbnail"]

    no_filter = collection.get_assets()
    assert no_filter is not collection.assets
    assert list(no_filter.keys()) == ["thumbnail"]
    no_filter["thumbnail"].description = "foo"
    assert collection.assets["thumbnail"].description != "foo"

    no_assets = collection.get_assets(media_type=pystac.MediaType.HDF)
    assert no_assets == {}

def test_removing_optional_attributes() -> None:
    path = TestCases.get_path("data-files/collections/with-assets.json")
    with open(path) as file:
        data = json.load(file)
    data["title"] = "dummy title"
    data["stac_extensions"] = ["dummy extension"]
    data["keywords"] = ["key", "word"]
    data["providers"] = [{"name": "pystac"}]
    collection = pystac.Collection.from_dict(data)

    # Assert we have everything set
    assert collection.title
    assert collection.stac_extensions
    assert collection.keywords
    assert collection.providers
    assert collection.summaries
    assert collection.assets

    # Remove all of the optional stuff
    collection.title = None
    collection.stac_extensions = []
    collection.keywords = []
    collection.providers = []
    collection.summaries = pystac.Summaries({})
    collection.assets = {}

    collection_as_dict = collection.to_dict()
    for key in (
        "title",
        "stac_extensions",
        "keywords",
        "providers",
        "summaries",
        "assets",
    ):
        assert key not in collection_as_dict

def test_from_dict_preserves_dict() -> None:
    path = TestCases.get_path("data-files/collections/with-assets.json")
    with open(path) as f:
        collection_dict = json.load(f)
    param_dict = deepcopy(collection_dict)

    # test that the parameter is preserved
    _ = Collection.from_dict(param_dict)
    assert param_dict == collection_dict

    # assert that the parameter is not preserved with
    # non-default parameter
    _ = Collection.from_dict(param_dict, preserve_dict=False, migrate=False)
    assert param_dict != collection_dict

def test_from_dict_set_root() -> None:
    path = TestCases.get_path("data-files/examples/hand-0.8.1/collection.json")
    with open(path) as f:
        collection_dict = json.load(f)
    catalog = pystac.Catalog(id="test", description="test desc")
    collection = Collection.from_dict(collection_dict, root=catalog)
    assert collection.get_root() is catalog

def test_schema_summary() -> None:
    collection = pystac.Collection.from_file(
        TestCases.get_path(
            "data-files/examples/1.0.0/collection-only/collection-with-schemas.json"
        )
    )
    instruments_schema = get_required(
        collection.summaries.get_schema("instruments"),
        collection.summaries,
        "instruments",
    )

    assert isinstance(instruments_schema, dict)

def test_from_invalid_dict_raises_exception() -> None:
    stac_io = pystac.StacIO.default()
    catalog_dict = stac_io.read_json(
        TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
    )
    with pytest.raises(pystac.STACTypeError):
        _ = pystac.Collection.from_dict(catalog_dict)

def test_clone_preserves_assets() -> None:
    path = TestCases.get_path("data-files/collections/with-assets.json")
    original_collection = Collection.from_file(path)
    assert len(original_collection.assets) > 0
    assert all(
        asset.owner is original_collection
        for asset in original_collection.assets.values()
    )

    cloned_collection = original_collection.clone()

    for key in original_collection.assets:
        assert key in cloned_collection.assets, f"Failed to Preserve {key} asset"
        cloned_asset = cloned_collection.assets.get(key)
        if cloned_asset is not None:
            assert cloned_asset.owner is cloned_collection, \
                f"Failed to set owner for {key}"

def test_to_dict_no_self_href() -> None:
    temporal_extent = TemporalExtent(intervals=[[TEST_DATETIME, None]])
    spatial_extent = SpatialExtent(bboxes=ARBITRARY_BBOX)
    extent = Extent(spatial=spatial_extent, temporal=temporal_extent)
    collection = Collection(
        id="an-id", description="A test Collection", extent=extent
    )
    d = collection.to_dict(include_self_link=False)
    Collection.from_dict(d)


class ExtentTest(unittest.TestCase):
    def test_temporal_extent_init_typing() -> None:
        # This test exists purely to test the typing of the intervals argument to
        # TemporalExtent
        start_datetime = str_to_datetime("2022-01-01T00:00:00Z")
        end_datetime = str_to_datetime("2022-01-31T23:59:59Z")

        _ = TemporalExtent([[start_datetime, end_datetime]])

    @pytest.mark.block_network()
    def test_temporal_extent_allows_single_interval() -> None:
        start_datetime = str_to_datetime("2022-01-01T00:00:00Z")
        end_datetime = str_to_datetime("2022-01-31T23:59:59Z")

        interval = [start_datetime, end_datetime]
        temporal_extent = TemporalExtent(intervals=interval)  # type: ignore

        assert temporal_extent.intervals == [interval]

    @pytest.mark.block_network()
    def test_temporal_extent_allows_single_interval_open_start() -> None:
        end_datetime = str_to_datetime("2022-01-31T23:59:59Z")

        interval = [None, end_datetime]
        temporal_extent = TemporalExtent(intervals=interval)

        assert temporal_extent.intervals == [interval]

    @pytest.mark.block_network()
    def test_temporal_extent_non_list_intervals_fails() -> None:
        with pytest.raises(TypeError):
            # Pass in non-list intervals
            _ = TemporalExtent(intervals=1)  # type: ignore

    @pytest.mark.block_network()
    def test_spatial_allows_single_bbox() -> None:
        temporal_extent = TemporalExtent(intervals=[[TEST_DATETIME, None]])

        # Pass in a single BBOX
        spatial_extent = SpatialExtent(bboxes=ARBITRARY_BBOX)

        collection_extent = Extent(spatial=spatial_extent, temporal=temporal_extent)

        collection = Collection(
            id="test", description="test desc", extent=collection_extent
        )

        # HREF required by validation
        collection.set_self_href("https://example.com/collection.json")

        collection.validate()

    @pytest.mark.block_network()
    def test_spatial_extent_non_list_bboxes_fails() -> None:
        with pytest.raises(TypeError):
            # Pass in non-list bboxes
            _ = SpatialExtent(bboxes=1)  # type: ignore

    def test_extent_from_items() -> None:
        item1 = Item(
            id="test-item-1",
            geometry=ARBITRARY_GEOM,
            bbox=[-10, -20, 0, -10],
            datetime=datetime(2000, 2, 1, 12, 0, 0, 0, tzinfo=tz.UTC),
            properties={},
        )

        item2 = Item(
            id="test-item-2",
            geometry=ARBITRARY_GEOM,
            bbox=[0, -9, 10, 1],
            datetime=None,
            properties={
                "start_datetime": datetime_to_str(
                    datetime(2000, 1, 1, 12, 0, 0, 0, tzinfo=tz.UTC)
                ),
                "end_datetime": datetime_to_str(
                    datetime(2000, 7, 1, 12, 0, 0, 0, tzinfo=tz.UTC)
                ),
            },
        )

        item3 = Item(
            id="test-item-2",
            geometry=ARBITRARY_GEOM,
            bbox=[-5, -20, 5, 0],
            datetime=None,
            properties={
                "start_datetime": datetime_to_str(
                    datetime(2000, 12, 1, 12, 0, 0, 0, tzinfo=tz.UTC)
                ),
                "end_datetime": datetime_to_str(
                    datetime(2001, 1, 1, 12, 0, 0, 0, tzinfo=tz.UTC),
                ),
            },
        )

        extent = Extent.from_items([item1, item2, item3])
        assert len(extent.spatial.bboxes) == 1
        assert extent.spatial.bboxes[0] == [-10, -20, 10, 1]
        assert len(extent.temporal.intervals) == 1

        interval = extent.temporal.intervals[0]
        assert interval[0] == datetime(2000, 1, 1, 12, 0, 0, 0, tzinfo=tz.UTC)
        assert interval[1] == datetime(2001, 1, 1, 12, 0, 0, 0, tzinfo=tz.UTC)

    def test_extent_to_from_dict() -> None:
        spatial_dict = {
            "bbox": [
                [
                    172.91173669923782,
                    1.3438851951615003,
                    172.95469614953714,
                    1.3690476620161975,
                ]
            ],
            "extension:field": "spatial value",
        }
        temporal_dict = {
            "interval": [
                ["2020-12-11T22:38:32.125000Z", "2020-12-14T18:02:31.437000Z"]
            ],
            "extension:field": "temporal value",
        }
        extent_dict = {
            "spatial": spatial_dict,
            "temporal": temporal_dict,
            "extension:field": "extent value",
        }
        expected_extent_extra_fields = {
            "extension:field": extent_dict["extension:field"],
        }
        expected_spatial_extra_fields = {
            "extension:field": spatial_dict["extension:field"],
        }
        expected_temporal_extra_fields = {
            "extension:field": temporal_dict["extension:field"],
        }

        extent = Extent.from_dict(extent_dict)

        assert expected_extent_extra_fields == extent.extra_fields
        assert expected_spatial_extra_fields == extent.spatial.extra_fields
        assert expected_temporal_extra_fields == extent.temporal.extra_fields

        assert extent_dict == extent.to_dict()


class CollectionSubClassTest(unittest.TestCase):
    """This tests cases related to creating classes inheriting from pystac.Catalog to
    ensure that inheritance, class methods, etc. function as expected."""

    MULTI_EXTENT = TestCases.get_path("data-files/collections/multi-extent.json")

    class BasicCustomCollection(pystac.Collection):
        def get_items(self) -> Iterator[Item]:  # type: ignore
            # This get_items does not have the `recursive` kwarg. This mimics
            # the current state of pystac-client and is intended to test
            # backwards compatibility of inherited classes
            return super().get_items()

    def setUp(self) -> None:
        self.stac_io = pystac.StacIO.default()

    def test_from_dict_returns_subclass(self) -> None:
        collection_dict = self.stac_io.read_json(self.MULTI_EXTENT)
        custom_collection = self.BasicCustomCollection.from_dict(collection_dict)

        assert isinstance(custom_collection, self.BasicCustomCollection)

    def test_from_file_returns_subclass(self) -> None:
        custom_collection = self.BasicCustomCollection.from_file(self.MULTI_EXTENT)

        assert isinstance(custom_collection, self.BasicCustomCollection)

    def test_clone(self) -> None:
        custom_collection = self.BasicCustomCollection.from_file(self.MULTI_EXTENT)
        cloned_collection = custom_collection.clone()

        assert isinstance(cloned_collection, self.BasicCustomCollection)

    def test_collection_get_item_works(self) -> None:
        path = TestCases.get_path(
            "data-files/catalogs/test-case-1/country-1/area-1-1/collection.json"
        )
        custom_collection = self.BasicCustomCollection.from_file(path)
        collection = custom_collection.clone()
        with pytest.warns(DeprecationWarning):
            collection.get_item("area-1-1-imagery")


class CollectionPartialSubClassTest(unittest.TestCase):
    class BasicCustomCollection(pystac.Collection):
        def get_items(  # type: ignore
            self, *, recursive: bool = False
        ) -> Iterator[Item]:
            # This get_items does not allow ids as args.
            return super().get_items(recursive=recursive)

    def test_collection_get_item_raises_type_error(self) -> None:
        path = TestCases.get_path(
            "data-files/catalogs/test-case-1/country-1/area-1-1/collection.json"
        )
        custom_collection = self.BasicCustomCollection.from_file(path)
        collection = custom_collection.clone()
        with pytest.raises(TypeError, match="takes 1 positional argument"):
            collection.get_item("area-1-1-imagery")


def test_custom_collection_from_dict(collection: Collection) -> None:
    # https://github.com/stac-utils/pystac/issues/862
    class CustomCollection(Collection):
        @classmethod
        def from_dict(
            cls,
            d: dict[str, Any],
            href: str | None = None,
            root: Catalog | None = None,
            migrate: bool = True,
            preserve_dict: bool = True,
        ) -> CustomCollection:
            return super().from_dict(d)

    _ = CustomCollection.from_dict(collection.to_dict())


@pytest.mark.parametrize("add_canonical", (True, False))
def test_remove_hierarchical_links(
    test_case_1_catalog: Catalog, add_canonical: bool
) -> None:
    collection = list(test_case_1_catalog.get_all_collections())[0]
    collection.remove_hierarchical_links(add_canonical=add_canonical)
    for link in collection.links:
        assert not link.is_hierarchical()
    assert bool(collection.get_single_link("canonical")) == add_canonical


@pytest.mark.parametrize("child", ["country-1", "country-2"])
def test_get_child_checks_links_where_hrefs_contains_id_first(
    test_case_1_catalog: Catalog, child: str
) -> None:
    cat1 = test_case_1_catalog
    country = cat1.get_child(child)
    assert country is not None
    child_links = [link for link in cat1.links if link.rel == pystac.RelType.CHILD]
    for link in child_links:
        if country.id not in link.href:
            assert not link.is_resolved()


def test_get_child_sort_links_by_id_is_configurable(
    test_case_1_catalog: Catalog,
) -> None:
    cat1 = test_case_1_catalog
    country = cat1.get_child("country-2", sort_links_by_id=False)
    assert country is not None
    child_links = [link for link in cat1.links if link.rel == pystac.RelType.CHILD]
    for link in child_links:
        assert link.is_resolved()


def test_get_item_returns_none_if_not_found(
    test_case_8_collection: Collection,
) -> None:
    col8 = test_case_8_collection
    item = col8.get_item("notarealitem")
    assert item is None


def test_get_item_is_not_recursive_by_default(
    test_case_8_collection: Collection,
) -> None:
    col8 = test_case_8_collection
    item = col8.get_item("20170831_162740_ssc1d1")
    assert item is None

    item = col8.get_item("20170831_162740_ssc1d1", recursive=True)
    assert item is not None


def test_delete_asset(tmp_asset: Asset, collection: Collection) -> None:
    asset = tmp_asset
    href = asset.get_absolute_href()
    item = asset.owner
    name = "foo"

    assert href is not None
    assert item is not None

    collection.add_asset(name, asset)

    # steal the href from the owner and use it as the collection's
    collection.set_self_href(item.get_self_href())

    collection.delete_asset(name)
    assert name not in collection.assets
    assert not os.path.exists(href)


def test_delete_asset_relative_no_self_link_fails(
    tmp_asset: Asset, collection: Collection
) -> None:
    asset = tmp_asset
    href = asset.get_absolute_href()
    name = "foo"

    assert href is not None

    collection.add_asset(name, asset)

    with pytest.raises(ValueError, match="Cannot delete file") as e:
        collection.delete_asset(name)

    assert asset.href in str(e.value)
    assert name in collection.assets
    assert os.path.exists(href)


def test_permissive_temporal_extent_deserialization(collection: Collection) -> None:
    # https://github.com/stac-utils/pystac/issues/1221
    collection_dict = collection.to_dict(include_self_link=False, transform_hrefs=False)
    collection_dict["extent"]["temporal"]["interval"] = collection_dict["extent"][
        "temporal"
    ]["interval"][0]
    with pytest.warns(UserWarning):
        Collection.from_dict(collection_dict)
