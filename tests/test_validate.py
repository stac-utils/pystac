from typing import cast

import pytest

pytest.importorskip("jsonschema")

from pytest import FixtureRequest

from pystac import Catalog, Collection, Item


@pytest.fixture(params=["1.0.0", "1.1.0"])
def version(request: FixtureRequest) -> str:
    return cast(str, request.param)


def test_validate_item(version: str) -> None:
    item = Item("an-id")
    item.stac_version = version
    item.validate()


def test_validate_catalog(version: str) -> None:
    catalog = Catalog("an-id", "a description")
    catalog.stac_version = version
    catalog.validate()


def test_validate_collection(version: str) -> None:
    collection = Collection("an-id", "a description")
    collection.stac_version = version
    collection.validate()
