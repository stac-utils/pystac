import json

import jsonschema
from jsonschema.validators import RefResolver

from pystac import (Catalog, Collection, Item, ItemCollection, LabelItem,
                    STAC_VERSION, STAC_IO, EOItem, SingleFileSTAC)


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
