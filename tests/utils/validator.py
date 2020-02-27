import json

import jsonschema
from jsonschema.validators import RefResolver

from pystac import (Catalog, Collection, Item, ItemCollection, LabelItem, STAC_VERSION, STAC_IO,
                    EOItem, SingleFileSTAC)


class SchemaValidator:
    REPO = 'https://raw.githubusercontent.com/radiantearth/stac-spec'
    TAG = 'v{}'.format(STAC_VERSION)
    SCHEMA_BASE_URI = '{}/{}'.format(REPO, TAG)

    schemas = {
        Catalog:
        'catalog-spec/json-schema/catalog.json',
        Collection:
        'collection-spec/json-schema/collection.json',
        Item:
        'item-spec/json-schema/item.json',
        ItemCollection:
        'item-spec/json-schema/itemcollection.json',
        LabelItem:
        'extensions/label/json-schema/schema.json',
        EOItem:
        'extensions/eo/json-schema/schema.json',

        # TODO: Move off of custom schema once schema in spec is fixed.
        SingleFileSTAC: ('https://raw.githubusercontent.com/lossyrob/stac-spec/'
                         '0.9.0/fix-single-file-stac-schema/extensions/'
                         'single-file-stac/json-schema/schema.json')
    }
    """
    Schemas that need to be downloaded for caching that are not tied directly to STAC objects.
    """
    aux_schemas = [
        'item-spec/json-schema/basics.json', 'item-spec/json-schema/datetimerange.json',
        'item-spec/json-schema/instrument.json', 'item-spec/json-schema/licensing.json',
        'item-spec/json-schema/metadata.json', 'item-spec/json-schema/provider.json',
        'https://geojson.org/schema/Feature.json',
        'https://geojson.org/schema/FeatureCollection.json'
    ]

    _schema_cache = {}

    @staticmethod
    def _abs_schema(uri):
        return ('{}/{}'.format(SchemaValidator.SCHEMA_BASE_URI, uri)
                if not uri.startswith('https') else uri)

    _is_setup = False

    @staticmethod
    def _setup():
        if not SchemaValidator._is_setup:
            for c in SchemaValidator.schemas:
                uri = SchemaValidator._abs_schema(SchemaValidator.schemas[c])
                SchemaValidator.schemas[c] = uri
                SchemaValidator._schema_cache[uri] = json.loads(STAC_IO.read_text(uri))

            for uri in SchemaValidator.aux_schemas:
                abs_uri = SchemaValidator._abs_schema(uri)
                SchemaValidator._schema_cache[abs_uri] = json.loads(STAC_IO.read_text(abs_uri))

            SchemaValidator._is_setup = True

    def __init__(self):
        SchemaValidator._setup()

    def get_schema(self, obj_type):
        schema_uri = SchemaValidator.schemas.get(obj_type)

        if schema_uri is None:
            raise Exception('No schema for type {}'.format(obj_type))
        schema = SchemaValidator._schema_cache.get(schema_uri)
        if schema is None:
            raise Exception('Could not read schema from {}'.format(schema_uri))

        resolver = RefResolver(base_uri=schema_uri,
                               referrer=schema,
                               store=SchemaValidator._schema_cache)

        return (schema, resolver)

    def validate_object(self, obj):
        return self.validate_dict(obj.to_dict(), type(obj))

    def validate_dict(self, d, obj_type):
        schema, resolver = self.get_schema(obj_type)

        try:
            return jsonschema.validate(instance=d, schema=schema, resolver=resolver)
        except jsonschema.exceptions.ValidationError as e:
            print('Validation error in {}'.format(obj_type))
            raise e
