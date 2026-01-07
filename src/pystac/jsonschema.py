import importlib.resources
import json
import urllib.parse
import urllib.request
import warnings
from collections.abc import Iterator
from typing import Any
from urllib.request import Request

import referencing.retrieval
from jsonschema.protocols import Validator
from jsonschema.validators import Draft7Validator
from referencing import Registry

from .constants import STAC_OBJECT_TYPE
from .utils import get_stac_type, get_user_agent


class JSONSchemaValidator:
    def __init__(self) -> None:
        self.registry: Registry = Registry(retrieve=cached_retrieve).with_contents(
            registry_contents()
        )
        self.cache: dict[str, Validator] = {}

    def get_validator(self, type: STAC_OBJECT_TYPE, version: str) -> Any:
        stac_type = get_stac_type(type).lower()
        path = f"stac/v{version}/{stac_type}.json"
        if path not in self.cache:
            try:
                schema_data = read_schema(path)
            except FileNotFoundError:
                warnings.warn(f"Local schema not found for {stac_type} v{version}")
                url = f"https://schemas.stacspec.org/v{version}/{stac_type}-spec/json-schema/{stac_type}.json"
                schema_data = json.loads(get_text(url))
            self.cache[path] = Draft7Validator(schema_data, registry=self.registry)
        return self.cache[path]

    def validate_core(
        self, type: STAC_OBJECT_TYPE, version: str, data: dict[str, Any]
    ) -> None:
        validator = self.get_validator(type, version)
        validator.validate(data)

    def validate_extension(self, extension: str, data: dict[str, Any]) -> None:
        if extension not in self.cache:
            schema_data = json.loads(get_text(extension))
            self.cache[extension] = Draft7Validator(schema_data, registry=self.registry)
        validator = self.cache[extension]
        validator.validate(data)


@referencing.retrieval.to_cached_resource()
def cached_retrieve(uri: str) -> str:
    return get_text(uri)


def get_text(uri: str) -> str:
    if urllib.parse.urlparse(uri).scheme:
        request = Request(uri, headers={"User-Agent": get_user_agent()})
        with urllib.request.urlopen(request) as response:
            return str(response.read(), encoding="utf-8")
    else:
        with open(uri) as f:
            return f.read()


def registry_contents() -> Iterator[tuple[str, dict[str, Any]]]:
    for name in (
        "bands",
        "basics",
        "common",
        "data-values",
        "item",
        "datetime",
        "instrument",
        "licensing",
        "provider",
    ):
        uri = f"https://schemas.stacspec.org/v1.1.0/item-spec/json-schema/{name}.json"
        path = f"stac/v1.1.0/{name}.json"
        yield uri, read_schema(path)

    for name in (
        "basics",
        "datetime",
        "instrument",
        "item",
        "licensing",
        "provider",
    ):
        uri = f"https://schemas.stacspec.org/v1.0.0/item-spec/json-schema/{name}.json"
        path = f"stac/v1.0.0/{name}.json"
        yield uri, read_schema(path)

    for name in (
        "Feature",
        "Geometry",
    ):
        uri = f"https://geojson.org/schema/{name}.json"
        path = f"geojson/{name}.json"
        yield uri, read_schema(path)


def read_schema(path: str) -> dict[str, Any]:
    with importlib.resources.files("pystac.schemas").joinpath(path).open("r") as f:
        return json.load(f)


DEFAULT_JSON_SCHEMA_VALIDATOR = JSONSchemaValidator()
