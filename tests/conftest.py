from pathlib import Path
from typing import Any, cast

import pytest
from pytest import Config, FixtureRequest, Parser

import pystac.jsonschema
from pystac import Catalog, Item
from pystac.jsonschema import JSONSchemaValidator

V1_DIR = Path(__file__).parent / "v1"


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--v1",
        action="store_true",
        default=False,
        help="Run v1 tests (skipped by default)",
    )


def pytest_ignore_collect(collection_path: Path, config: Config) -> bool | None:
    if collection_path.is_relative_to(V1_DIR) and not config.getoption("--v1"):
        return True
    return None


@pytest.fixture(scope="module")
def vcr_config() -> dict[str, Any]:
    def scrub_headers(response: dict[str, Any]) -> dict[str, Any]:
        retain = ["location"]
        response["headers"] = {
            key: value
            for (key, value) in response["headers"].items()
            if key.lower() in retain
        }
        return response

    return {"before_record_response": scrub_headers}


@pytest.fixture(autouse=True)
def reset_json_schema_validator() -> None:
    # Needed to make sure each test records a cassette for validation requests
    pystac.jsonschema.set_default_json_schema_validator(JSONSchemaValidator())


@pytest.fixture
def data_files_path() -> Path:
    return Path(__file__).parent / "data-files"


@pytest.fixture(params=["v1.0.0", "v1.1.0"])
def examples_path(request: FixtureRequest, data_files_path: Path) -> Path:
    return data_files_path / "examples" / cast(str, request.param)


@pytest.fixture
def catalog(examples_path: Path) -> Catalog:
    return Catalog.from_file(examples_path / "catalog.json")


@pytest.fixture
def item(examples_path: Path) -> Item:
    return Item.from_file(examples_path / "simple-item.json")


@pytest.fixture
def proj_example(examples_path: Path) -> Item:
    return Item.from_file(
        examples_path / "extensions-collection" / "proj-example" / "proj-example.json"
    )
