import json
import sys
from typing import Any, Dict, List, cast

from jsonschema import Draft7Validator, RefResolver, ValidationError

from pystac.errors import STACLocalValidationError
from pystac.version import STACVersion

if sys.version_info[:2] < (3, 9):
    from importlib_resources import files as importlib_resources_files
else:
    from importlib.resources import files as importlib_resources_files

VERSION = STACVersion.DEFAULT_STAC_VERSION
ITEM_SCHEMA_URI = (
    f"https://schemas.stacspec.org/v{VERSION}/item-spec/json-schema/item.json"
)
COLLECTION_SCHEMA_URI = (
    f"https://schemas.stacspec.org/v{VERSION}/"
    "collection-spec/json-schema/collection.json"
)
CATALOG_SCHEMA_URI = (
    f"https://schemas.stacspec.org/v{VERSION}/catalog-spec/json-schema/catalog.json"
)


class LocalValidator:
    def _validate_from_local(
        self, schema_uri: str, stac_dict: Dict[str, Any]
    ) -> List[ValidationError]:
        if schema_uri == ITEM_SCHEMA_URI:
            validator = self.item_validator(VERSION)
        elif schema_uri == COLLECTION_SCHEMA_URI:
            validator = self.collection_validator(VERSION)
        elif schema_uri == CATALOG_SCHEMA_URI:
            validator = self.catalog_validator(VERSION)
        else:
            raise STACLocalValidationError(
                f"Schema not available locally: {schema_uri}"
            )
        return list(validator.iter_errors(stac_dict))

    def _validator(self, stac_type: str, version: str) -> Draft7Validator:
        schema = _read_schema(f"stac-spec/v{version}/{stac_type}.json")
        resolver = RefResolver.from_schema(schema)
        resolver.store[
            f"https://schemas.stacspec.org/v{version}/collection-spec/json-schema/collection.json"
        ] = _read_schema(f"stac-spec/v{version}/collection.json")
        resolver.store[
            f"https://schemas.stacspec.org/v{version}/item-spec/json-schema/item.json"
        ] = _read_schema(f"stac-spec/v{version}/item.json")
        for name in ("Feature", "Geometry"):
            resolver.store[f"https://geojson.org/schema/{name}.json"] = _read_schema(
                f"geojson/{name}.json"
            )
        for name in ("basics", "datetime", "instrument", "licensing", "provider"):
            resolver.store[
                f"https://schemas.stacspec.org/v{version}/item-spec/json-schema/{name}.json"
            ] = _read_schema(f"stac-spec/v{version}/{name}.json")
        return Draft7Validator(schema, resolver=resolver)

    def catalog_validator(self, version: str = VERSION) -> Draft7Validator:
        return self._validator("catalog", version)

    def collection_validator(self, version: str = VERSION) -> Draft7Validator:
        return self._validator("collection", version)

    def item_validator(self, version: str = VERSION) -> Draft7Validator:
        return self._validator("item", version)


def _read_schema(file_name: str) -> Dict[str, Any]:
    with importlib_resources_files("pystac.validation.jsonschemas").joinpath(
        file_name
    ).open("r") as f:
        return cast(Dict[str, Any], json.load(f))
