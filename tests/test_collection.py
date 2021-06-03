import unittest
import os
import json
from tempfile import TemporaryDirectory
from datetime import datetime
from dateutil import tz

import pystac
from pystac.extensions.eo import EOExtension
from pystac.validation import validate_dict
from pystac import Collection, Item, Extent, SpatialExtent, TemporalExtent, CatalogType
from pystac.utils import datetime_to_str
from tests.utils import TestCases, ARBITRARY_GEOM, ARBITRARY_BBOX

TEST_DATETIME = datetime(2020, 3, 14, 16, 32)


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
        with TemporaryDirectory() as tmp_dir:
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

        with TemporaryDirectory() as tmp_dir:
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
        collection = pystac.read_dict(data)
        collection.validate()


class ExtentTest(unittest.TestCase):
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
