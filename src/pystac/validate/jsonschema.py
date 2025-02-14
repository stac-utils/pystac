import importlib.resources
import json
import urllib.parse
import urllib.request
import warnings
from typing import Any, Iterator, cast

import referencing.retrieval
from jsonschema.validators import Draft7Validator
from referencing import Registry

from ..catalog import Catalog
from ..collection import Collection
from ..errors import PySTACWarning
from ..item import Item
from ..stac_object import STACObject
from .base import Validator


class JsonschemaValidator(Validator):
    """A validator using [json-schema](https://json-schema.org/)."""

    def __init__(self) -> None:
        """Creates a new json-schmea validator.

        This fetches many of the common schemas from local storage, so we don't
        have to hit the network for them.
        """

        self._registry = Registry(retrieve=cached_retrieve).with_contents(  # type: ignore
            registry_contents()
        )
        self._schemas: dict[str, dict[str, Any]] = {}

    def validate(self, stac_object: STACObject) -> None:
        if isinstance(stac_object, Item):
            slug = "item"
        elif isinstance(stac_object, Catalog):
            slug = "catalog"
        elif isinstance(stac_object, Collection):
            slug = "collection"
        else:
            raise Exception("unreachable")
        validator = self._get_validator(stac_object.stac_version, slug)
        validator.validate(stac_object.to_dict())

    def _get_validator(self, version: str, slug: str) -> Draft7Validator:
        path = f"stac/v{version}/{slug}.json"
        if path not in self._schemas:
            try:
                self._schemas[path] = read_schema(path)
            except FileNotFoundError:
                uri = f"https://schemas.stacspec.org/v{version}/{slug}-spec/json-schema/{slug}.json"
                warnings.warn(f"Fetching core schema from {uri}", PySTACWarning)
                self._schemas[path] = json.loads(get_text(uri))
        schema = self._schemas[path]
        return Draft7Validator(schema, registry=self._registry)


@referencing.retrieval.to_cached_resource()
def cached_retrieve(uri: str) -> str:
    return get_text(uri)


def read_schema(path: str) -> dict[str, Any]:
    with (
        importlib.resources.files("pystac.validate.schemas")
        .joinpath(path)
        .open("r") as f
    ):
        return cast(dict[str, Any], json.load(f))


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


def get_text(uri: str) -> str:
    try:
        import obstore

        parsed_url = urllib.parse.urlparse(uri)
        store = obstore.store.from_url(
            urllib.parse.urlunparse(parsed_url._replace(path=""))
        )
        result = obstore.get(store, parsed_url.path)
        return str(result.bytes(), encoding="utf-8")
    except ImportError:
        with urllib.request.urlopen(uri) as response:
            return str(response.read(), encoding="utf-8")
