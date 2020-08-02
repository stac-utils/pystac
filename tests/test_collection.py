import unittest
import os
import json
from tempfile import TemporaryDirectory
from datetime import datetime

import pystac
from pystac.serialization.identify import STACObjectType
from pystac import (Collection, Item, Extent, SpatialExtent, TemporalExtent, CatalogType)
from pystac.extensions.eo import Band
from tests.utils import (TestCases, RANDOM_GEOM, RANDOM_BBOX, SchemaValidator, STACValidationError)


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
                     datetime=datetime.utcnow(),
                     properties={'key': 'one'},
                     stac_extensions=['eo', 'commons'])

        item2 = Item(id='test-item-2',
                     geometry=RANDOM_GEOM,
                     bbox=RANDOM_BBOX,
                     datetime=datetime.utcnow(),
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

    def test_multiple_extents(self):
        self.validator = SchemaValidator()

        cat1 = TestCases.test_case_1()
        col1 = cat1.get_child('country-1').get_child('area-1-1')
        self.validator.validate_object(col1)
        self.assertIsInstance(col1, Collection)
        self.validator.validate_dict(col1.to_dict(), STACObjectType.COLLECTION)

        multi_ext_uri = TestCases.get_path('data-files/collections/multi-extent.json')
        with open(multi_ext_uri) as f:
            multi_ext_dict = json.load(f)
        self.validator.validate_dict(multi_ext_dict, STACObjectType.COLLECTION)
        self.assertIsInstance(Collection.from_dict(multi_ext_dict), Collection)

        multi_ext_col = Collection.from_file(multi_ext_uri)
        self.validator.validate_object(multi_ext_col)
        ext = multi_ext_col.extent
        extent_dict = multi_ext_dict['extent']
        self.assertIsInstance(ext, Extent)
        self.assertIsInstance(ext.spatial.bboxes[0], list)
        self.assertEqual(len(ext.spatial.bboxes), 2)
        self.assertDictEqual(ext.to_dict(), extent_dict)

        cloned_ext = ext.clone()
        self.assertDictEqual(cloned_ext.to_dict(), multi_ext_dict['extent'])

        multi_ext_dict['extent']['spatial']['bbox'] = multi_ext_dict['extent']['spatial']['bbox'][0]
        invalid_col = Collection.from_dict(multi_ext_dict)
        with self.assertRaises(STACValidationError):
            self.validator.validate_object(invalid_col)

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
