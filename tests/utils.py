import os
import json
from datetime import datetime
from copy import deepcopy
from dateutil.parser import parse
import jsonschema
from jsonschema.validators import RefResolver

from pystac import (Catalog, Item, Asset, LabelItem, LabelCount, LabelOverview,
                    LabelClasses, Collection, Extent, TemporalExtent,
                    SpatialExtent, STAC_VERSION, STAC_IO, EOItem, MediaType,
                    ItemCollection, SingleFileSTAC)

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
        return os.path.join(os.path.dirname(__file__), rel_path)

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


class SchemaValidator:
    REPO = 'https://raw.githubusercontent.com/radiantearth/stac-spec'
    TAG = 'v{}'.format(STAC_VERSION)
    # SCHEMA_BASE_URI = '{}/{}'.format(REPO, TAG)
    # Temporarily set to point to a fork if stac-spec with updated
    # schemas for Label and EO
    # Pending this issue being resolved: https://github.com/radiantearth/stac-spec/issues/618
    SCHEMA_BASE_URI = ('https://raw.githubusercontent.com/lossyrob/stac-spec/'
                       '0.8.1/refactor-extension-schemas')

    schemas = {
        Catalog: 'catalog-spec/json-schema/catalog.json',
        Collection: 'collection-spec/json-schema/collection.json',
        Item: 'item-spec/json-schema/item.json',
        ItemCollection: 'item-spec/json-schema/itemcollection.json',
        LabelItem: 'extensions/label/json-schema/label-item.json',
        EOItem: 'extensions/eo/json-schema/eo-item.json',
        SingleFileSTAC:
        'extensions/single-file-stac/json-schema/single-file.json'
    }

    for c in schemas:
        schemas[c] = '{}/{}'.format(SCHEMA_BASE_URI, schemas[c])

    def __init__(self):
        self.schema_cache = {}

    def get_schema(self, obj_type):
        schema_uri = SchemaValidator.schemas.get(obj_type)

        if schema_uri is None:
            raise Exception('No schema for type {}'.format(obj_type))
        schema = self.schema_cache.get(obj_type)
        if schema is None:
            schema = json.loads(STAC_IO.read_text(schema_uri))
            self.schema_cache[obj_type] = schema

        resolver = RefResolver(base_uri=schema_uri, referrer=schema)

        return (schema, resolver)

    def validate_object(self, obj):
        return self.validate_dict(obj.to_dict(), type(obj))

    def validate_dict(self, d, obj_type):
        schema, resolver = self.get_schema(obj_type)

        try:
            return jsonschema.validate(instance=d,
                                       schema=schema,
                                       resolver=resolver)
        except jsonschema.exceptions.ValidationError as e:
            print('Validation error in {}'.format(obj_type))
            raise e


def test_to_from_dict(test_class, stac_object_class, d):
    def _parse_times(a_dict):
        for k, v in a_dict.items():
            if isinstance(v, dict):
                _parse_times(v)
            elif isinstance(v, (tuple, list, set)):
                for vv in v:
                    if isinstance(vv, dict):
                        _parse_times(vv)
            else:
                if k == 'datetime':
                    if not isinstance(v, datetime):
                        a_dict[k] = parse(v)
                        a_dict[k] = a_dict[k].replace(microsecond=0)

    d1 = deepcopy(d)
    d2 = stac_object_class.from_dict(d).to_dict()
    _parse_times(d1)
    _parse_times(d2)
    test_class.assertDictEqual(d1, d2)
