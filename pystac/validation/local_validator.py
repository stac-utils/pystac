import json
import sys
from typing import Any, Dict, cast

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
