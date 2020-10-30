import unittest
import os
import json
from tempfile import TemporaryDirectory
from datetime import datetime
from dateutil import tz

import pystac
from pystac.validation import validate_dict
from pystac.serialization.identify import STACObjectType
from pystac import (Collection, Item, Extent, SpatialExtent, TemporalExtent, CatalogType)
from pystac.extensions.eo import Band
from pystac.utils import datetime_to_str
from tests.utils import (TestCases, RANDOM_GEOM, RANDOM_BBOX)

TEST_DATETIME = datetime(2020, 3, 14, 16, 32)


class CollectionTest(unittest.TestCase):
    def test_spatial_extent_from_coordinates(self):
        extent = SpatialExtent.from_coordinates(RANDOM_GEOM['coordinates'])

        self.assertEqual(len(extent.bboxes), 1)
        bbox = extent.bboxes[0]
        self.assertEqual(len(bbox), 4)
        for x in bbox:
            self.assertTrue(type(x) is float)

    def test_eo_items_are_heritable(self):
        item1 = Item(id='test-item-1',
                     geometry=RANDOM_GEOM,
                     bbox=RANDOM_BBOX,
                     datetime=TEST_DATETIME,
                     properties={'key': 'one'},
                     stac_extensions=['eo', 'commons'])

        item2 = Item(id='test-item-2',
                     geometry=RANDOM_GEOM,
                     bbox=RANDOM_BBOX,
                     datetime=TEST_DATETIME,
                     properties={'key': 'two'},
                     stac_extensions=['eo', 'commons'])

        wv3_bands = [
            Band.create(name='Coastal', description='Coastal: 400 - 450 nm', common_name='coastal'),
            Band.create(name='Blue', description='Blue: 450 - 510 nm', common_name='blue'),
            Band.create(name='Green', description='Green: 510 - 580 nm', common_name='green'),
            Band.create(name='Yellow', description='Yellow: 585 - 625 nm', common_name='yellow'),
            Band.create(name='Red', description='Red: 630 - 690 nm', common_name='red'),
            Band.create(name='Red Edge',
                        description='Red Edge: 705 - 745 nm',
                        common_name='rededge'),
            Band.create(name='Near-IR1', description='Near-IR1: 770 - 895 nm', common_name='nir08'),
            Band.create(name='Near-IR2', description='Near-IR2: 860 - 1040 nm', common_name='nir09')
        ]

        spatial_extent = SpatialExtent(bboxes=[RANDOM_BBOX])
        temporal_extent = TemporalExtent(intervals=[[item1.datetime, None]])

        collection_extent = Extent(spatial=spatial_extent, temporal=temporal_extent)

        common_properties = {
            'eo:bands': [b.to_dict() for b in wv3_bands],
            'gsd': 0.3,
            'eo:platform': 'Maxar',
            'eo:instrument': 'WorldView3'
        }

        collection = Collection(id='test',
                                description='test',
                                extent=collection_extent,
                                properties=common_properties,
                                stac_extensions=['commons'],
                                license='CC-BY-SA-4.0')

        collection.add_items([item1, item2])

        with TemporaryDirectory() as tmp_dir:
            collection.normalize_hrefs(tmp_dir)
            collection.save(catalog_type=CatalogType.SELF_CONTAINED)

            read_col = Collection.from_file('{}/collection.json'.format(tmp_dir))
            items = list(read_col.get_all_items())

            self.assertEqual(len(items), 2)
            self.assertTrue(items[0].ext.implements('eo'))
            self.assertTrue(items[1].ext.implements('eo'))

    def test_read_eo_items_are_heritable(self):
        cat = TestCases.test_case_5()
        item = next(cat.get_all_items())

        self.assertTrue(item.ext.implements('eo'))

    def test_save_uses_previous_catalog_type(self):
        collection = TestCases.test_case_8()
        assert collection.STAC_OBJECT_TYPE == pystac.STACObjectType.COLLECTION
        self.assertEqual(collection.catalog_type, CatalogType.SELF_CONTAINED)
        with TemporaryDirectory() as tmp_dir:
            collection.normalize_hrefs(tmp_dir)
            href = collection.get_self_href()
            collection.save()

            collection2 = pystac.read_file(href)
            self.assertEqual(collection2.catalog_type, CatalogType.SELF_CONTAINED)

    def test_clone_uses_previous_catalog_type(self):
        catalog = TestCases.test_case_8()
        assert catalog.catalog_type == CatalogType.SELF_CONTAINED
        clone = catalog.clone()
        self.assertEqual(clone.catalog_type, CatalogType.SELF_CONTAINED)

    def test_multiple_extents(self):
        cat1 = TestCases.test_case_1()
        col1 = cat1.get_child('country-1').get_child('area-1-1')
        col1.validate()
        self.assertIsInstance(col1, Collection)
        validate_dict(col1.to_dict(), STACObjectType.COLLECTION)

        multi_ext_uri = TestCases.get_path('data-files/collections/multi-extent.json')
        with open(multi_ext_uri) as f:
            multi_ext_dict = json.load(f)
        validate_dict(multi_ext_dict, STACObjectType.COLLECTION)
        self.assertIsInstance(Collection.from_dict(multi_ext_dict), Collection)

        multi_ext_col = Collection.from_file(multi_ext_uri)
        multi_ext_col.validate()
        ext = multi_ext_col.extent
        extent_dict = multi_ext_dict['extent']
        self.assertIsInstance(ext, Extent)
        self.assertIsInstance(ext.spatial.bboxes[0], list)
        self.assertEqual(len(ext.spatial.bboxes), 2)
        self.assertDictEqual(ext.to_dict(), extent_dict)

        cloned_ext = ext.clone()
        self.assertDictEqual(cloned_ext.to_dict(), multi_ext_dict['extent'])

    def test_extra_fields(self):
        catalog = TestCases.test_case_2()
        collection = catalog.get_child('1a8c1632-fa91-4a62-b33e-3a87c2ebdf16')

        collection.extra_fields['test'] = 'extra'

        with TemporaryDirectory() as tmp_dir:
            p = os.path.join(tmp_dir, 'collection.json')
            collection.save_object(include_self_link=False, dest_href=p)
            with open(p) as f:
                col_json = json.load(f)
            self.assertTrue('test' in col_json)
            self.assertEqual(col_json['test'], 'extra')

            read_col = pystac.read_file(p)
            self.assertTrue('test' in read_col.extra_fields)
            self.assertEqual(read_col.extra_fields['test'], 'extra')

    def test_update_extents(self):

        catalog = TestCases.test_case_2()
        base_collection = catalog.get_child('1a8c1632-fa91-4a62-b33e-3a87c2ebdf16')
        base_extent = base_collection.extent
        collection = base_collection.clone()

        item1 = Item(id='test-item-1',
                     geometry=RANDOM_GEOM,
                     bbox=[-180, -90, 180, 90],
                     datetime=TEST_DATETIME,
                     properties={'key': 'one'},
                     stac_extensions=['eo', 'commons'])

        item2 = Item(id='test-item-1',
                     geometry=RANDOM_GEOM,
                     bbox=[-180, -90, 180, 90],
                     datetime=None,
                     properties={
                         'start_datetime': datetime_to_str(datetime(2000, 1, 1, 12, 0, 0, 0)),
                         'end_datetime': datetime_to_str(datetime(2000, 2, 1, 12, 0, 0, 0))
                     },
                     stac_extensions=['eo', 'commons'])

        collection.add_item(item1)

        collection.update_extent_from_items()
        self.assertEqual([[-180, -90, 180, 90]], collection.extent.spatial.bboxes)
        self.assertEqual(len(base_extent.spatial.bboxes[0]),
                         len(collection.extent.spatial.bboxes[0]))

        self.assertNotEqual(base_extent.temporal.intervals, collection.extent.temporal.intervals)
        collection.remove_item('test-item-1')
        collection.update_extent_from_items()
        self.assertNotEqual([[-180, -90, 180, 90]], collection.extent.spatial.bboxes)
        collection.add_item(item2)

        collection.update_extent_from_items()

        self.assertEqual(
            [[item2.common_metadata.start_datetime, base_extent.temporal.intervals[0][1]]],
            collection.extent.temporal.intervals)

    def test_supplying_href_in_init_does_not_fail(self):
        test_href = "http://example.com/collection.json"
        spatial_extent = SpatialExtent(bboxes=[RANDOM_BBOX])
        temporal_extent = TemporalExtent(intervals=[[TEST_DATETIME, None]])

        collection_extent = Extent(spatial=spatial_extent, temporal=temporal_extent)
        collection = Collection(id='test',
                                description='test desc',
                                extent=collection_extent,
                                properties={},
                                href=test_href)

        self.assertEqual(collection.get_self_href(), test_href)

    def test_reading_0_8_1_collection_as_catalog_throws_correct_exception(self):
        cat = pystac.Catalog.from_file(
            TestCases.get_path('data-files/examples/hand-0.8.1/collection.json'))
        with self.assertRaises(ValueError):
            list(cat.get_all_items())

    def test_collection_with_href_caches_by_href(self):
        collection = pystac.read_file(
            TestCases.get_path('data-files/examples/hand-0.8.1/collection.json'))
        cache = collection._resolved_objects

        # Since all of our STAC objects have HREFs, everything should be
        # cached only by HREF
        self.assertEqual(len(cache.id_keys_to_objects), 0)


class ExtentTest(unittest.TestCase):
    def test_spatial_allows_single_bbox(self):
        temporal_extent = TemporalExtent(intervals=[[TEST_DATETIME, None]])

        # Pass in a single BBOX
        spatial_extent = SpatialExtent(bboxes=RANDOM_BBOX)

        collection_extent = Extent(spatial=spatial_extent, temporal=temporal_extent)

        collection = Collection(id='test', description='test desc', extent=collection_extent)

        # HREF required by validation
        collection.set_self_href('https://example.com/collection.json')

        collection.validate()

    def test_from_items(self):
        item1 = Item(id='test-item-1',
                     geometry=RANDOM_GEOM,
                     bbox=[-10, -20, 0, -10],
                     datetime=datetime(2000, 2, 1, 12, 0, 0, 0, tzinfo=tz.UTC),
                     properties={})

        item2 = Item(id='test-item-2',
                     geometry=RANDOM_GEOM,
                     bbox=[0, -9, 10, 1],
                     datetime=None,
                     properties={
                         'start_datetime':
                         datetime_to_str(datetime(2000, 1, 1, 12, 0, 0, 0, tzinfo=tz.UTC)),
                         'end_datetime':
                         datetime_to_str(datetime(2000, 7, 1, 12, 0, 0, 0, tzinfo=tz.UTC))
                     })

        item3 = Item(id='test-item-2',
                     geometry=RANDOM_GEOM,
                     bbox=[-5, -20, 5, 0],
                     datetime=None,
                     properties={
                         'start_datetime':
                         datetime_to_str(datetime(2000, 12, 1, 12, 0, 0, 0, tzinfo=tz.UTC)),
                         'end_datetime':
                         datetime_to_str(datetime(2001, 1, 1, 12, 0, 0, 0, tzinfo=tz.UTC), )
                     })

        extent = Extent.from_items([item1, item2, item3])

        self.assertEqual(len(extent.spatial.bboxes), 1)
        self.assertEqual(extent.spatial.bboxes[0], [-10, -20, 10, 1])

        self.assertEqual(len(extent.temporal.intervals), 1)
        interval = extent.temporal.intervals[0]

        self.assertEqual(interval[0], datetime(2000, 1, 1, 12, 0, 0, 0, tzinfo=tz.UTC))
        self.assertEqual(interval[1], datetime(2001, 1, 1, 12, 0, 0, 0, tzinfo=tz.UTC))
