import json
import sys
import warnings
from typing import Any, Dict, List, cast

from jsonschema import Draft7Validator, ValidationError
from referencing import Registry, Resource

from pystac.errors import STACLocalValidationError
from pystac.version import STACVersion

if sys.version_info[:2] < (3, 9):
    from importlib_resources import files as importlib_resources_files
else:
    from importlib.resources import files as importlib_resources_files

VERSION = STACVersion.DEFAULT_STAC_VERSION


def _read_schema(file_name: str) -> Dict[str, Any]:
    with importlib_resources_files("pystac.validation.jsonschemas").joinpath(
        file_name
    ).open("r") as f:
        return cast(Dict[str, Any], json.load(f))


def get_local_schema_cache() -> Dict[str, Dict[str, Any]]:
    return {
        **{
            (
                f"https://schemas.stacspec.org/v{VERSION}/"
                f"{name}-spec/json-schema/{name}.json"
            ): _read_schema(f"stac-spec/v{VERSION}/{name}.json")
            for name in ("item", "catalog", "collection")
        },
        **{
            f"https://geojson.org/schema/{name}.json": _read_schema(
                f"geojson/{name}.json"
            )
            for name in ("Feature", "Geometry")
        },
        **{
            (
                f"https://schemas.stacspec.org/v{VERSION}/"
                f"item-spec/json-schema/{name}.json"
            ): _read_schema(f"stac-spec/v{VERSION}/{name}.json")
            for name in (
                "basics",
                "datetime",
                "instrument",
                "licensing",
                "provider",
            )
        },
    }


############################### DEPRECATED #################################

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
    def __init__(self) -> None:
        """DEPRECATED"""
        warnings.warn(
            "``LocalValidator`` is deprecated and will be removed in v2.",
            DeprecationWarning,
        )
        self.schema_cache = get_local_schema_cache()

    def registry(self) -> Any:
        return Registry().with_resources(
            [
                (k, Resource.from_contents(v)) for k, v in self.schema_cache.items()
            ]  # type: ignore
        )

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
        return Draft7Validator(schema, registry=self.registry)

    def catalog_validator(self, version: str = VERSION) -> Draft7Validator:
        return self._validator("catalog", version)

    def collection_validator(self, version: str = VERSION) -> Draft7Validator:
        return self._validator("collection", version)

    def item_validator(self, version: str = VERSION) -> Draft7Validator:
        return self._validator("item", version)
