import unittest
from tempfile import TemporaryDirectory
from datetime import datetime

from pystac import (Collection, Item, Extent, SpatialExtent, TemporalExtent,
                    CatalogType, EOItem, Band)
from tests.utils import (RANDOM_GEOM, RANDOM_BBOX)


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
                     stac_extensions=['eo'])

        item2 = Item(id='test-item-2',
                     geometry=RANDOM_GEOM,
                     bbox=RANDOM_BBOX,
                     datetime=datetime.utcnow(),
                     properties={'key': 'two'},
                     stac_extensions=['eo'])

        wv3_bands = [
            Band(name='Coastal',
                 description='Coastal: 400 - 450 nm',
                 common_name='coastal'),
            Band(name='Blue',
                 description='Blue: 450 - 510 nm',
                 common_name='blue'),
            Band(name='Green',
                 description='Green: 510 - 580 nm',
                 common_name='green'),
            Band(name='Yellow',
                 description='Yellow: 585 - 625 nm',
                 common_name='yellow'),
            Band(name='Red',
                 description='Red: 630 - 690 nm',
                 common_name='red'),
            Band(name='Red Edge',
                 description='Red Edge: 705 - 745 nm',
                 common_name='rededge'),
            Band(name='Near-IR1',
                 description='Near-IR1: 770 - 895 nm',
                 common_name='nir08'),
            Band(name='Near-IR2',
                 description='Near-IR2: 860 - 1040 nm',
                 common_name='nir09')
        ]

        spatial_extent = SpatialExtent(bboxes=[RANDOM_BBOX])
        temporal_extent = TemporalExtent(intervals=[[item1.datetime, None]])

        collection_extent = Extent(spatial=spatial_extent,
                                   temporal=temporal_extent)

        common_properties = {
            'eo:bands': [b.to_dict() for b in wv3_bands],
            'eo:gsd': 0.3,
            'eo:platform': 'Maxar',
            'eo:instrument': 'WorldView3'
        }

        collection = Collection(id='test',
                                description='test',
                                extent=collection_extent,
                                properties=common_properties,
                                license='CC-BY-SA-4.0')

        collection.add_items([item1, item2])

        with TemporaryDirectory() as tmp_dir:
            collection.normalize_hrefs(tmp_dir)
            collection.save(catalog_type=CatalogType.SELF_CONTAINED)

            read_col = Collection.from_file(
                '{}/collection.json'.format(tmp_dir))
            items = list(read_col.get_all_items())

            self.assertEqual(len(items), 2)
            self.assertIsInstance(items[0], EOItem)
            self.assertIsInstance(items[1], EOItem)
