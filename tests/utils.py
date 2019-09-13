import os
import json
from datetime import datetime

import jsonschema
from jsonschema.validators import RefResolver

from pystac import *

TEST_LABEL_CATALOG = {
    'country-1': {
        'area-1-1': {
            'dsm': 'area-1-1_dsm.tif',
            'ortho': 'area-1-1_ortho.tif',
            'labels': 'area-1-1_labels.geojson' },
        'area-1-2': {
            'dsm': 'area-1-2_dsm.tif',
            'ortho': 'area-1-2_ortho.tif',
            'labels': 'area-1-2_labels.geojson' } },
    'country-2': {
        'area-2-1': {
            'dsm': 'area-2-1_dsm.tif',
            'ortho': 'area-2-1_ortho.tif',
            'labels': 'area-2-1_labels.geojson' },
        'area-2-2': {
            'dsm': 'area-2-2_dsm.tif',
            'ortho': 'area-2-2_ortho.tif',
            'labels': 'area-2-2_labels.geojson' } }
}



RANDOM_GEOM = {
    "type": "Polygon",
    "coordinates": [
        [
            [
                -2.5048828125,
                3.8916575492899987
            ],
            [
                -1.9610595703125,
                3.8916575492899987
            ],
            [
                -1.9610595703125,
                4.275202171119132
            ],
            [
                -2.5048828125,
                4.275202171119132
            ],
            [
                -2.5048828125,
                3.8916575492899987
            ]
        ]
    ]
}

RANDOM_BBOX = [RANDOM_GEOM['coordinates'][0][0][0],
               RANDOM_GEOM['coordinates'][0][0][1],
               RANDOM_GEOM['coordinates'][0][1][0],
               RANDOM_GEOM['coordinates'][0][1][1]]

RANDOM_EXTENT = Extent(spatial=SpatialExtent.from_coordinates(RANDOM_GEOM['coordinates']),
                       temporal=TemporalExtent.from_now())

class TestCases:
    @staticmethod
    def get_path(rel_path):
        return os.path.join(os.path.dirname(__file__), rel_path)

    @staticmethod
    def test_case_1():
        root_cat = Catalog(id='test', description='test catalog')
        for country in TEST_LABEL_CATALOG:
            country_cat = Catalog(id=country, description='test catalog {}'.format(country))
            for area in TEST_LABEL_CATALOG[country]:
                area_collection = Collection(id=area,
                                             description='test collection {}'.format(country),
                                             extent=RANDOM_EXTENT)
                image_item = Item(id='{}-imagery'.format(area),
                                  geometry=RANDOM_GEOM,
                                  bbox=RANDOM_BBOX,
                                  datetime=datetime.utcnow(),
                                  properties={})
                for key in ['ortho', 'dsm']:
                    image_item.add_asset(key,
                                         href=TEST_LABEL_CATALOG[country][area][key],
                                         media_type=Asset.MEDIA_TYPE.GEOTIFF)

                label_item = LabelItem(id='{}-labels'.format(area),
                                       geometry=RANDOM_GEOM,
                                       bbox=RANDOM_BBOX,
                                       datetime=datetime.utcnow(),
                                       properties={},
                                       label_description='labels for {}'.format(area),
                                       label_type='vector',
                                       label_property=['label'],
                                       label_classes=[LabelClasses(classes=['one', 'two'],
                                                                   name='label')],
                                       label_task=['classification'],
                                       label_method=['manual'])
                label_item.add_source(image_item, assets=['ortho'])

                area_collection.add_item(image_item)
                area_collection.add_item(label_item)
                country_cat.add_child(area_collection)
            root_cat.add_child(country_cat)

        return root_cat

class SchemaValidator:
    REPO = 'https://raw.githubusercontent.com/radiantearth/stac-spec'

    # TODO: Replace once 0.8 release is out.
    # TAG = 'v{}'.format(STAC_VERSION)
    TAG = 'v0.8.0-rc1'

    # TODO: Switch back once schema fix PR is merged.
    # SCHEMA_BASE_URI = '{}/{}'.format(REPO, TAG)
    SCHEMA_BASE_URI = 'https://raw.githubusercontent.com/lossyrob/stac-spec/fix/label-classes/'

    schemas = {
        Catalog: 'catalog-spec/json-schema/catalog.json',
        Collection: 'collection-spec/json-schema/collection.json',
        Item: 'item-spec/json-schema/item.json',
        LabelItem: 'extensions/label/schema.json',
    }

    for c in schemas:
        schemas[c] = '{}/{}'.format(SCHEMA_BASE_URI, schemas[c])

    def __init__(self):
        self.schema_cache = {}

    def get_schema(self, obj):
        schema_uri = SchemaValidator.schemas.get(type(obj))

        if schema_uri is None:
            raise Exception('No schema for type {}'.format(type(obj)))
        schema = self.schema_cache.get(obj)
        if schema is None:
            schema = json.loads(STAC_IO.read_text(schema_uri))
            self.schema_cache[type(obj)] = schema

        resolver = RefResolver(base_uri=schema_uri,
                               referrer=schema)

        return (schema, resolver)

    def validate(self, obj):
        schema, resolver = self.get_schema(obj)
        seralized = obj.to_dict()

        try:
            jsonschema.validate(instance=seralized, schema=schema, resolver=resolver)
        except jsonschema.exceptions.ValidationError as e:
            print('Validation error in {}'.format(obj))
            raise e
