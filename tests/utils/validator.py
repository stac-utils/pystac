import json

import jsonschema
from jsonschema.validators import RefResolver

from pystac import (STAC_VERSION, STAC_IO, Catalog, Collection, Item, ItemCollection, Extensions)
from pystac.serialization import STACObjectType


class STACValidationError(Exception):
    pass


class SchemaValidator:
    REPO = 'https://raw.githubusercontent.com/radiantearth/stac-spec'
    TAG = 'v{}'.format(STAC_VERSION)
    SCHEMA_BASE_URI = '{}/{}'.format(REPO, TAG)

    core_schemas = {
        STACObjectType.CATALOG: 'catalog-spec/json-schema/catalog.json',
        STACObjectType.COLLECTION: 'collection-spec/json-schema/collection.json',
        STACObjectType.ITEM: 'item-spec/json-schema/item.json',
        STACObjectType.ITEMCOLLECTION: 'item-spec/json-schema/itemcollection.json'
    }

    extension_schemas = {
        Extensions.LABEL: {
            STACObjectType.ITEM: 'extensions/label/json-schema/schema.json'
        },
        Extensions.EO: {
            STACObjectType.ITEM: 'extensions/eo/json-schema/schema.json'
        },
        Extensions.SINGLE_FILE_STAC: {
            # TODO: Move off of custom schema if schema in spec was fixed
            # before this extension got removed.
            STACObjectType.ITEMCOLLECTION: ('https://raw.githubusercontent.com/lossyrob/stac-spec/'
                                            '0.9.0/fix-single-file-stac-schema/extensions/'
                                            'single-file-stac/json-schema/schema.json')
        }
    }

    # Schemas that need to be downloaded for caching that are not tied directly to STAC objects.
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
            for c in SchemaValidator.core_schemas:
                uri = SchemaValidator._abs_schema(SchemaValidator.core_schemas[c])
                SchemaValidator.core_schemas[c] = uri
                SchemaValidator._schema_cache[uri] = json.loads(STAC_IO.read_text(uri))

            for ext in SchemaValidator.extension_schemas:
                for stac_object_type in SchemaValidator.extension_schemas[ext]:
                    uri = SchemaValidator._abs_schema(
                        SchemaValidator.extension_schemas[ext][stac_object_type])
                    SchemaValidator.extension_schemas[ext][stac_object_type] = uri
                    SchemaValidator._schema_cache[uri] = json.loads(STAC_IO.read_text(uri))

            for uri in SchemaValidator.aux_schemas:
                abs_uri = SchemaValidator._abs_schema(uri)
                SchemaValidator._schema_cache[abs_uri] = json.loads(STAC_IO.read_text(abs_uri))

            SchemaValidator._is_setup = True

    def __init__(self):
        SchemaValidator._setup()

    @classmethod
    def get_schema_from_uri(cls, schema_uri):
        schema = cls._schema_cache.get(schema_uri)
        if schema is None:
            raise Exception('Could not read schema from {}'.format(schema_uri))

        resolver = RefResolver(base_uri=schema_uri,
                               referrer=schema,
                               store=SchemaValidator._schema_cache)

        return (schema, resolver)

    @classmethod
    def get_core_schema(cls, obj_class):
        schema_uri = cls.core_schemas.get(obj_class)

        if schema_uri is None:
            raise Exception('No schema for type {}'.format(obj_class))

        return cls.get_schema_from_uri(schema_uri)

    @classmethod
    def get_extension_schema(cls, obj_class, extension_id):
        schemas_by_class = cls.extension_schemas.get(extension_id)
        if schemas_by_class is None:
            return None

        schema_uri = schemas_by_class.get(obj_class)

        if schema_uri is None:
            return None

        return cls.get_schema_from_uri(schema_uri)

    # Validate methods are instance methods to ensure initialization

    def validate_object(self, obj, print_on_error=False):
        obj_type = type(obj)
        if issubclass(obj_type, Collection):
            stac_object_type = STACObjectType.COLLECTION
        elif issubclass(obj_type, Catalog):
            stac_object_type = STACObjectType.CATALOG
        elif issubclass(obj_type, Item):
            stac_object_type = STACObjectType.ITEM
        elif issubclass(obj_type, ItemCollection):
            stac_object_type = STACObjectType.ITEMCOLLECTION
        else:
            raise Exception("Unknown STAC Object type: {}".format(obj_type))

        return self.validate_dict(obj.to_dict(), stac_object_type, print_on_error=print_on_error)

    def validate_dict(self, d, stac_object_type, print_on_error=False):
        schema, resolver = SchemaValidator.get_core_schema(stac_object_type)

        try:
            jsonschema.validate(instance=d, schema=schema, resolver=resolver)
        except jsonschema.exceptions.ValidationError as e:
            if print_on_error:
                print(json.dumps(d, indent=2))
            raise STACValidationError(
                'Validation failed for STAC {}'.format(stac_object_type)) from e

        if 'stac_extensions' in d:
            for extension_id in d['stac_extensions']:
                ext_schema_result = SchemaValidator.get_extension_schema(
                    stac_object_type, extension_id)
                if ext_schema_result is not None:
                    ext_schema, ext_resolver = ext_schema_result
                    try:
                        jsonschema.validate(instance=d, schema=ext_schema, resolver=ext_resolver)
                    except jsonschema.exceptions.ValidationError as e:
                        if print_on_error:
                            print(json.dumps(d, indent=2))
                        raise STACValidationError(
                            'Validation failed for STAC {} extension {}'.format(
                                stac_object_type, extension_id)) from e
