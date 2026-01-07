from pathlib import Path
from typing import Any, cast

import pytest
from pytest import FixtureRequest

from pystac import Catalog, Item


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
