import json
from pathlib import Path
from typing import Any, Dict, List, cast

from jsonschema import Draft7Validator, RefResolver, ValidationError

from pystac.errors import STACLocalValidationError
from pystac.extensions.eo import SCHEMA_URI as EO_SCHEMA_URI
from pystac.extensions.label import SCHEMA_URI as LABEL_SCHEMA_URI
from pystac.extensions.view import SCHEMA_URI as VIEW_SCHEMA_URI
from pystac.version import STACVersion

here = Path(__file__).resolve().parent

VERSION = STACVersion.DEFAULT_STAC_VERSION
ITEM_SCHEMA_URI = (
    f"https://schemas.stacspec.org/v{VERSION}/item-spec/json-schema/item.json"
)
COLLECTION_SCHEMA_URI = f"https://schemas.stacspec.org/v{VERSION}/collection-spec/json-schema/collection.json"
CATALOG_SCHEMA_URI = (
    f"https://schemas.stacspec.org/v{VERSION}/catalog-spec/json-schema/catalog.json"
)


class LocalValidator:
    extension_schema_uris: List[str] = [
        EO_SCHEMA_URI,
        LABEL_SCHEMA_URI,
        VIEW_SCHEMA_URI,
    ]

    def _validate_from_local(
        self, schema_uri: str, stac_dict: Dict[str, Any]
    ) -> List[ValidationError]:
        if schema_uri == ITEM_SCHEMA_URI:
            validator = self.item_validator(VERSION)
        elif schema_uri == COLLECTION_SCHEMA_URI:
            validator = self.collection_validator(VERSION)
        elif schema_uri == CATALOG_SCHEMA_URI:
            validator = self.catalog_validator(VERSION)
        elif schema_uri in self.extension_schema_uris:
            validator = self.extension_validator(schema_uri)
        else:
            raise STACLocalValidationError(
                f"Schema not available locally: {schema_uri}"
            )
        return list(validator.iter_errors(stac_dict))

    @staticmethod
    def extension_validator(schema_uri: str) -> Draft7Validator:
        local_path = schema_uri.replace(
            "https://stac-extensions.github.io", "extensions"
        )
        schema = _read_schema(local_path)
        return Draft7Validator(schema)

    @staticmethod
    def catalog_validator(version: str = VERSION) -> Draft7Validator:
        schema = _read_schema(f"stac-spec/v{version}/catalog.json")
        return Draft7Validator(schema)

    @staticmethod
    def collection_validator(version: str = VERSION) -> Draft7Validator:
        schema = _read_schema(f"stac-spec/v{version}/collection.json")
        resolver = RefResolver.from_schema(schema)
        resolver.store[
            f"https://schemas.stacspec.org/v{version}/item-spec/json-schema/item.json"
        ] = _read_schema(f"stac-spec/v{version}/item.json")
        return Draft7Validator(schema, resolver=resolver)

    @staticmethod
    def item_validator(version: str = VERSION) -> Draft7Validator:
        schema = _read_schema(f"stac-spec/v{version}/item.json")
        resolver = RefResolver.from_schema(schema)
        for name in ("Feature", "Geometry"):
            resolver.store[f"https://geojson.org/schema/{name}.json"] = _read_schema(
                f"geojson/{name}.json"
            )
        for name in ("basics", "datetime", "instrument", "licensing", "provider"):
            resolver.store[
                f"https://schemas.stacspec.org/v{version}/item-spec/json-schema/{name}.json"
            ] = _read_schema(f"stac-spec/v{version}/{name}.json")
        return Draft7Validator(schema, resolver=resolver)


def _read_schema(file_name: str) -> Dict[str, Any]:
    with (here / "jsonschemas" / file_name).open("r") as f:
        return cast(Dict[str, Any], json.load(f))
