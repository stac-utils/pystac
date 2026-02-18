from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.request import Request

import pytest
from dateutil.parser import parse
from pystac import (
    Asset,
    Catalog,
    Collection,
    Extent,
    Item,
    Link,
    SpatialExtent,
    TemporalExtent,
)

ARBITRARY_GEOM: dict[str, Any] = {
    "type": "Polygon",
    "coordinates": [
        [
            [-2.5048828125, 3.8916575492899987],
            [-1.9610595703125, 3.8916575492899987],
            [-1.9610595703125, 4.275202171119132],
            [-2.5048828125, 4.275202171119132],
            [-2.5048828125, 3.8916575492899987],
        ]
    ],
}

ARBITRARY_BBOX: list[float] = [
    ARBITRARY_GEOM["coordinates"][0][0][0],
    ARBITRARY_GEOM["coordinates"][0][0][1],
    ARBITRARY_GEOM["coordinates"][0][1][0],
    ARBITRARY_GEOM["coordinates"][0][1][1],
]

ARBITRARY_EXTENT = Extent(
    spatial=SpatialExtent.from_coordinates(ARBITRARY_GEOM["coordinates"]),
    temporal=TemporalExtent.from_now(),
)


def assert_to_from_dict(
    stac_object_class: type[Item | Catalog | Collection],
    d: dict[str, Any],
) -> None:
    def _parse_times(a_dict: dict[str, Any]) -> None:
        for k, v in a_dict.items():
            if isinstance(v, dict):
                _parse_times(v)
            elif isinstance(v, (tuple, list, set)):
                for vv in v:
                    if isinstance(vv, dict):
                        _parse_times(vv)
            else:
                if k == "datetime":
                    if not isinstance(v, datetime):
                        a_dict[k] = parse(v)
                        a_dict[k] = a_dict[k].replace(microsecond=0)

    d1 = deepcopy(d)
    d2 = stac_object_class.from_dict(d, migrate=False).to_dict()
    _parse_times(d1)
    _parse_times(d2)
    assert d1 == d2


@pytest.fixture(scope="module")
def vcr_config() -> dict[str, Any]:
    def scrub_response_headers(response: dict[str, Any]) -> dict[str, Any]:
        retain = ["location"]
        response["headers"] = {
            key: value
            for (key, value) in response["headers"].items()
            if key.lower() in retain
        }
        return response

    def scrub_request_headers(request: Request) -> Request:
        drop = ["User-Agent"]
        for header in drop:
            request.headers.pop(header, None)
        return request

    return {
        "before_record_response": scrub_response_headers,
        "before_record_request": scrub_request_headers,
    }


@pytest.fixture
def catalog() -> Catalog:
    return Catalog("test-catalog", "A test catalog")


@pytest.fixture
def collection() -> Collection:
    return Collection("test-collection", "A test collection", ARBITRARY_EXTENT)


@pytest.fixture
def item() -> Item:
    return Item("test-item", ARBITRARY_GEOM, ARBITRARY_BBOX, datetime.now(), {})


@pytest.fixture
def asset(item: Item) -> Asset:
    item.add_asset("foo", Asset("https://example.tif"))
    return item.assets["foo"]


@pytest.fixture
def link(item: Item) -> Link:
    item.add_link(Link(rel="child", target="https://example.tif"))
    return item.links[0]


_DATA_FILES = Path(__file__).resolve().parent / "data-files"


@pytest.fixture
def sample_item() -> Item:
    return Item.from_file(str(_DATA_FILES / "item" / "sample-item.json"))


@pytest.fixture(autouse=True)
def clear_validator() -> None:
    from pystac.validation import RegisteredValidator

    RegisteredValidator._validator = None
