from copy import deepcopy
import unittest
import os
import json
from datetime import datetime
from dateutil import tz
import tempfile

import pystac
from pystac.extensions.eo import EOExtension
from pystac.validation import validate_dict
from pystac import (
    Collection,
    Item,
    Extent,
    SpatialExtent,
    TemporalExtent,
    CatalogType,
    Provider,
)
from pystac.utils import datetime_to_str, get_required
from tests.utils import TestCases, ARBITRARY_GEOM, ARBITRARY_BBOX

TEST_DATETIME = datetime(2020, 3, 14, 16, 32)


class ProviderTest(unittest.TestCase):
    def test_to_from_dict(self) -> None:
        provider_dict = {
            "name": "Remote Data, Inc",
            "description": "Producers of awesome spatiotemporal assets",
            "roles": ["producer", "processor"],
            "url": "http://remotedata.io",
            "extension:field": "some value",
        }
        expected_extra_fields = {"extension:field": provider_dict["extension:field"]}

        provider = Provider.from_dict(provider_dict)

        self.assertEqual(provider_dict["name"], provider.name)
        self.assertEqual(provider_dict["description"], provider.description)
        self.assertEqual(provider_dict["roles"], provider.roles)
        self.assertEqual(provider_dict["url"], provider.url)
        self.assertDictEqual(expected_extra_fields, provider.extra_fields)

        self.assertDictEqual(provider_dict, provider.to_dict())


class CollectionTest(unittest.TestCase):
    def test_spatial_extent_from_coordinates(self) -> None:
        extent = SpatialExtent.from_coordinates(ARBITRARY_GEOM["coordinates"])

        self.assertEqual(len(extent.bboxes), 1)
        bbox = extent.bboxes[0]
        self.assertEqual(len(bbox), 4)
        for x in bbox:
            self.assertTrue(type(x) is float)

    def test_read_eo_items_are_heritable(self) -> None:
        cat = TestCases.test_case_5()
        item = next(iter(cat.get_all_items()))

        self.assertTrue(EOExtension.has_extension(item))

    def test_save_uses_previous_catalog_type(self) -> None:
        collection = TestCases.test_case_8()
        assert collection.STAC_OBJECT_TYPE == pystac.STACObjectType.COLLECTION
        self.assertEqual(collection.catalog_type, CatalogType.SELF_CONTAINED)
        with tempfile.TemporaryDirectory() as tmp_dir:
            collection.normalize_hrefs(tmp_dir)
            href = collection.self_href
            collection.save()

            collection2 = pystac.Collection.from_file(href)
            self.assertEqual(collection2.catalog_type, CatalogType.SELF_CONTAINED)

    def test_clone_uses_previous_catalog_type(self) -> None:
        catalog = TestCases.test_case_8()
        assert catalog.catalog_type == CatalogType.SELF_CONTAINED
        clone = catalog.clone()
        self.assertEqual(clone.catalog_type, CatalogType.SELF_CONTAINED)

    def test_multiple_extents(self) -> None:
        cat1 = TestCases.test_case_1()
        country = cat1.get_child("country-1")
        assert country is not None
        col1 = country.get_child("area-1-1")
        assert col1 is not None
        col1.validate()
        self.assertIsInstance(col1, Collection)
        validate_dict(col1.to_dict(), pystac.STACObjectType.COLLECTION)

        multi_ext_uri = TestCases.get_path("data-files/collections/multi-extent.json")
        with open(multi_ext_uri) as f:
            multi_ext_dict = json.load(f)
        validate_dict(multi_ext_dict, pystac.STACObjectType.COLLECTION)
        self.assertIsInstance(Collection.from_dict(multi_ext_dict), Collection)

        multi_ext_col = Collection.from_file(multi_ext_uri)
        multi_ext_col.validate()
        ext = multi_ext_col.extent
        extent_dict = multi_ext_dict["extent"]
        self.assertIsInstance(ext, Extent)
        self.assertIsInstance(ext.spatial.bboxes[0], list)
        self.assertEqual(len(ext.spatial.bboxes), 2)
        self.assertDictEqual(ext.to_dict(), extent_dict)

        cloned_ext = ext.clone()
        self.assertDictEqual(cloned_ext.to_dict(), multi_ext_dict["extent"])

    def test_extra_fields(self) -> None:
        catalog = TestCases.test_case_2()
        collection = catalog.get_child("1a8c1632-fa91-4a62-b33e-3a87c2ebdf16")
        assert collection is not None

        collection.extra_fields["test"] = "extra"

        with tempfile.TemporaryDirectory() as tmp_dir:
            p = os.path.join(tmp_dir, "collection.json")
            collection.save_object(include_self_link=False, dest_href=p)
            with open(p) as f:
                col_json = json.load(f)
            self.assertTrue("test" in col_json)
            self.assertEqual(col_json["test"], "extra")

            read_col = pystac.Collection.from_file(p)
            self.assertTrue("test" in read_col.extra_fields)
            self.assertEqual(read_col.extra_fields["test"], "extra")

    def test_update_extents(self) -> None:

        catalog = TestCases.test_case_2()
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
        self.assertEqual([[-180, -90, 180, 90]], collection.extent.spatial.bboxes)
        self.assertEqual(
            len(base_extent.spatial.bboxes[0]), len(collection.extent.spatial.bboxes[0])
        )

        self.assertNotEqual(
            base_extent.temporal.intervals, collection.extent.temporal.intervals
        )
        collection.remove_item("test-item-1")
        collection.update_extent_from_items()
        self.assertNotEqual([[-180, -90, 180, 90]], collection.extent.spatial.bboxes)
        collection.add_item(item2)

        collection.update_extent_from_items()

        self.assertEqual(
            [
                [
                    item2.common_metadata.start_datetime,
                    base_extent.temporal.intervals[0][1],
                ]
            ],
            collection.extent.temporal.intervals,
        )

    def test_supplying_href_in_init_does_not_fail(self) -> None:
        test_href = "http://example.com/collection.json"
        spatial_extent = SpatialExtent(bboxes=[ARBITRARY_BBOX])
        temporal_extent = TemporalExtent(intervals=[[TEST_DATETIME, None]])

        collection_extent = Extent(spatial=spatial_extent, temporal=temporal_extent)
        collection = Collection(
            id="test", description="test desc", extent=collection_extent, href=test_href
        )

        self.assertEqual(collection.get_self_href(), test_href)

    def test_collection_with_href_caches_by_href(self) -> None:
        collection = pystac.Collection.from_file(
            TestCases.get_path("data-files/examples/hand-0.8.1/collection.json")
        )
        cache = collection._resolved_objects

        # Since all of our STAC objects have HREFs, everything should be
        # cached only by HREF
        self.assertEqual(len(cache.id_keys_to_objects), 0)

    def test_assets(self) -> None:
        path = TestCases.get_path("data-files/collections/with-assets.json")
        with open(path) as f:
            data = json.load(f)
        collection = pystac.Collection.from_dict(data)
        collection.validate()

    def test_from_dict_preserves_dict(self) -> None:
        path = TestCases.get_path("data-files/collections/with-assets.json")
        with open(path) as f:
            collection_dict = json.load(f)
        param_dict = deepcopy(collection_dict)

        # test that the parameter is preserved
        _ = Collection.from_dict(param_dict)
        self.assertEqual(param_dict, collection_dict)

        # assert that the parameter is not preserved with
        # non-default parameter
        _ = Collection.from_dict(param_dict, preserve_dict=False)
        self.assertNotEqual(param_dict, collection_dict)

    def test_schema_summary(self) -> None:
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

        self.assertIsInstance(instruments_schema, dict)

    def test_from_invalid_dict_raises_exception(self) -> None:
        stac_io = pystac.StacIO.default()
        catalog_dict = stac_io.read_json(
            TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
        )
        with self.assertRaises(pystac.STACTypeError):
            _ = pystac.Collection.from_dict(catalog_dict)


class ExtentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    def test_spatial_allows_single_bbox(self) -> None:
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

    def test_from_items(self) -> None:
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

        self.assertEqual(len(extent.spatial.bboxes), 1)
        self.assertEqual(extent.spatial.bboxes[0], [-10, -20, 10, 1])

        self.assertEqual(len(extent.temporal.intervals), 1)
        interval = extent.temporal.intervals[0]

        self.assertEqual(interval[0], datetime(2000, 1, 1, 12, 0, 0, 0, tzinfo=tz.UTC))
        self.assertEqual(interval[1], datetime(2001, 1, 1, 12, 0, 0, 0, tzinfo=tz.UTC))

    def test_to_from_dict(self) -> None:
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

        self.assertDictEqual(expected_extent_extra_fields, extent.extra_fields)
        self.assertDictEqual(expected_spatial_extra_fields, extent.spatial.extra_fields)
        self.assertDictEqual(
            expected_temporal_extra_fields, extent.temporal.extra_fields
        )

        self.assertDictEqual(extent_dict, extent.to_dict())


class CollectionSubClassTest(unittest.TestCase):
    """This tests cases related to creating classes inheriting from pystac.Catalog to
    ensure that inheritance, class methods, etc. function as expected."""

    MULTI_EXTENT = TestCases.get_path("data-files/collections/multi-extent.json")

    class BasicCustomCollection(pystac.Collection):
        pass

    def setUp(self) -> None:
        self.stac_io = pystac.StacIO.default()

    def test_from_dict_returns_subclass(self) -> None:
        collection_dict = self.stac_io.read_json(self.MULTI_EXTENT)
        custom_collection = self.BasicCustomCollection.from_dict(collection_dict)

        self.assertIsInstance(custom_collection, self.BasicCustomCollection)

    def test_from_file_returns_subclass(self) -> None:
        custom_collection = self.BasicCustomCollection.from_file(self.MULTI_EXTENT)

        self.assertIsInstance(custom_collection, self.BasicCustomCollection)

    def test_clone(self) -> None:
        custom_collection = self.BasicCustomCollection.from_file(self.MULTI_EXTENT)
        cloned_collection = custom_collection.clone()

        self.assertIsInstance(cloned_collection, self.BasicCustomCollection)
