import functools
import json
from pathlib import Path
from typing import Any, Dict, List, cast

from jsonschema import Draft7Validator, RefResolver, ValidationError

from pystac.extensions.eo import SCHEMA_URI as EO_SCHEMA_URI
from pystac.extensions.label import SCHEMA_URI as LABEL_SCHEMA_URI
from pystac.extensions.view import SCHEMA_URI as VIEW_SCHEMA_URI
from pystac.stac_object import STACObjectType
from pystac.version import STACVersion

here = Path(__file__).resolve().parent


class LocalValidator:
    version: str = STACVersion.DEFAULT_STAC_VERSION
    extension_schema_uris: List[str] = [
        EO_SCHEMA_URI,
        LABEL_SCHEMA_URI,
        VIEW_SCHEMA_URI,
    ]

    def validate_stac_object(
        self, stac_object_type: STACObjectType, stac_dict: Dict[str, Any]
    ) -> List[ValidationError]:
        # TODO support other versions
        if stac_object_type == STACObjectType.ITEM:
            validator = self.item_validator
        elif stac_object_type == STACObjectType.CATALOG:
            validator = self.catalog_validator
        elif stac_object_type == STACObjectType.COLLECTION:
            validator = self.collection_validator
        else:
            raise ValueError(f"unknown STAC object type: {stac_object_type}")
        return list(validator.iter_errors(stac_dict))

    def validate_stac_extension(
        self, schema_uri: str, stac_dict: Dict[str, Any]
    ) -> List[ValidationError]:
        if schema_uri in self.extension_schema_uris:
            validator = _extension_validator(schema_uri)
        else:
            raise ValueError(f"unknown STAC extension type: {schema_uri}")
        return list(validator.iter_errors(stac_dict))

    @functools.cached_property
    def catalog_validator(self) -> Draft7Validator:
        schema = _read_schema(f"stac-spec/v{self.version}/catalog.json")
        return Draft7Validator(schema)

    @functools.cached_property
    def collection_validator(self) -> Draft7Validator:
        schema = _read_schema(f"stac-spec/v{self.version}/collection.json")
        resolver = RefResolver.from_schema(schema)
        resolver.store[
            f"https://schemas.stacspec.org/v{self.version}/item-spec/json-schema/item.json"
        ] = _read_schema(f"stac-spec/v{self.version}/item.json")
        return Draft7Validator(schema, resolver=resolver)

    @functools.cached_property
    def item_validator(self) -> Draft7Validator:
        schema = _read_schema(f"stac-spec/v{self.version}/item.json")
        resolver = RefResolver.from_schema(schema)
        for name in ("Feature", "Geometry"):
            resolver.store[f"https://geojson.org/schema/{name}.json"] = _read_schema(
                f"geojson/{name}.json"
            )
        for name in ("basics", "datetime", "instrument", "licensing", "provider"):
            resolver.store[
                f"https://schemas.stacspec.org/v{self.version}/item-spec/json-schema/{name}.json"
            ] = _read_schema(f"stac-spec/v{self.version}/{name}.json")
        return Draft7Validator(schema, resolver=resolver)


def _read_schema(file_name: str) -> dict[str, Any]:
    with (here / "jsonschemas" / file_name).open("r") as f:
        return cast(dict[str, Any], json.load(f))


def _extension_validator(schema_uri: str) -> Draft7Validator:
    local_path = schema_uri.replace("https://stac-extensions.github.io", "extensions")
    schema = _read_schema(local_path)
    return Draft7Validator(schema)
