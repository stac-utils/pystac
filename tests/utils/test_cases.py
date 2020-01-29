import os
from datetime import datetime

from pystac import (Catalog, Item, Asset, LabelItem, LabelCount, LabelOverview,
                    LabelClasses, Extent, TemporalExtent, SpatialExtent,
                    MediaType)

TEST_LABEL_CATALOG = {
    'country-1': {
        'area-1-1': {
            'dsm': 'area-1-1_dsm.tif',
            'ortho': 'area-1-1_ortho.tif',
            'labels': 'area-1-1_labels.geojson'
        },
        'area-1-2': {
            'dsm': 'area-1-2_dsm.tif',
            'ortho': 'area-1-2_ortho.tif',
            'labels': 'area-1-2_labels.geojson'
        }
    },
    'country-2': {
        'area-2-1': {
            'dsm': 'area-2-1_dsm.tif',
            'ortho': 'area-2-1_ortho.tif',
            'labels': 'area-2-1_labels.geojson'
        },
        'area-2-2': {
            'dsm': 'area-2-2_dsm.tif',
            'ortho': 'area-2-2_ortho.tif',
            'labels': 'area-2-2_labels.geojson'
        }
    }
}

RANDOM_GEOM = {
    "type":
    "Polygon",
    "coordinates": [[[-2.5048828125, 3.8916575492899987],
                     [-1.9610595703125, 3.8916575492899987],
                     [-1.9610595703125, 4.275202171119132],
                     [-2.5048828125, 4.275202171119132],
                     [-2.5048828125, 3.8916575492899987]]]
}

RANDOM_BBOX = [
    RANDOM_GEOM['coordinates'][0][0][0], RANDOM_GEOM['coordinates'][0][0][1],
    RANDOM_GEOM['coordinates'][0][1][0], RANDOM_GEOM['coordinates'][0][1][1]
]

RANDOM_EXTENT = Extent(spatial=SpatialExtent.from_coordinates(
    RANDOM_GEOM['coordinates']),
                       temporal=TemporalExtent.from_now())  # noqa: E126


class TestCases:
    @staticmethod
    def get_path(rel_path):
        return os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', rel_path))

    @staticmethod
    def test_case_1():
        return Catalog.from_file(
            TestCases.get_path('data-files/catalogs/test-case-1/catalog.json'))

    @staticmethod
    def test_case_2():
        return Catalog.from_file(
            TestCases.get_path('data-files/catalogs/test-case-2/catalog.json'))

    @staticmethod
    def test_case_3():
        root_cat = Catalog(id='test3',
                           description='test case 3 catalog',
                           title='test case 3 title')

        image_item = Item(id='imagery-item',
                          geometry=RANDOM_GEOM,
                          bbox=RANDOM_BBOX,
                          datetime=datetime.utcnow(),
                          properties={})

        image_item.add_asset(
            'ortho',
            Asset(href='some/geotiff.tiff', media_type=MediaType.GEOTIFF))

        overviews = [
            LabelOverview('label',
                          counts=[LabelCount('one', 1),
                                  LabelCount('two', 2)])
        ]

        label_item = LabelItem(
            id='label-items',
            geometry=RANDOM_GEOM,
            bbox=RANDOM_BBOX,
            datetime=datetime.utcnow(),
            properties={},
            label_description='ML Labels',
            label_type='vector',
            label_properties=['label'],
            label_classes=[LabelClasses(classes=['one', 'two'], name='label')],
            label_tasks=['classification'],
            label_methods=['manual'],
            label_overviews=overviews)
        label_item.add_source(image_item, assets=['ortho'])

        root_cat.add_item(image_item)
        root_cat.add_item(label_item)

        return root_cat
