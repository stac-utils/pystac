import json
from datetime import datetime, timezone

import pytest

import pystac
from pystac import ExtensionTypeError, Item
from pystac.errors import ExtensionNotImplemented
from pystac.extensions.insar import (
    InsarExtension,
)

from tests.conftest import get_data_file
from tests.utils import TestCases, assert_to_from_dict


INSAR_ITEM_URI = TestCases.get_path("data-files/insar/insar-item.json")
INSAR_COLLECTION_URI = TestCases.get_path("data-files/insar/insar-collection.json")
PLAIN_ITEM_URI = TestCases.get_path("data-files/item/sample-item.json")


def test_to_from_dict() -> None:
    with open(INSAR_ITEM_URI) as f:
        item_dict = json.load(f)
    assert_to_from_dict(Item, item_dict)


# def test_from_file_to_dict(ext_item_uri: str, ext_item: pystac.Item) -> None:
#     with open(ext_item_uri) as f:
#         d = json.load(f)
#     actual = ext_item.to_dict(include_self_link=False)
#     assert actual == d


def test_add_to() -> None:
    item = Item.from_file(PLAIN_ITEM_URI)
    assert InsarExtension.get_schema_uri() not in item.stac_extensions

    InsarExtension.add_to(item)
    assert InsarExtension.get_schema_uri() in item.stac_extensions

    # idempotent
    InsarExtension.add_to(item)
    InsarExtension.add_to(item)
    insar_uris = [
        uri for uri in item.stac_extensions if uri == InsarExtension.get_schema_uri()
    ]
    assert len(insar_uris) == 1


@pytest.mark.vcr()
def test_validate_insar() -> None:
    item = pystac.Item.from_file(INSAR_ITEM_URI)
    item.validate()


def test_item_getters(ext_item: pystac.Item) -> None:
    insar = InsarExtension.ext(ext_item)

    assert insar.perpendicular_baseline == 123.4
    assert insar.temporal_baseline == 12.0
    assert insar.height_of_ambiguity == 45.6
    assert insar.processing_dem == "COPDEM"
    assert insar.geocoding_dem == "SRTM"

    assert insar.reference_datetime == datetime(2020, 1, 1, tzinfo=timezone.utc)
    assert insar.secondary_datetime == datetime(2020, 1, 13, tzinfo=timezone.utc)


@pytest.mark.vcr()
def test_item_setters(ext_item: pystac.Item) -> None:
    insar = InsarExtension.ext(ext_item)

    insar.perpendicular_baseline = 100
    insar.temporal_baseline = 24.5
    insar.height_of_ambiguity = 30
    insar.processing_dem = "NEWDEM"
    insar.geocoding_dem = "OTHERDEM"

    dt = datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    insar.reference_datetime = dt
    insar.secondary_datetime = dt

    assert ext_item.properties["insar:perpendicular_baseline"] == 100.0
    assert ext_item.properties["insar:temporal_baseline"] == 24.5
    assert ext_item.properties["insar:height_of_ambiguity"] == 30.0
    assert ext_item.properties["insar:processing_dem"] == "NEWDEM"
    assert ext_item.properties["insar:geocoding_dem"] == "OTHERDEM"
    assert ext_item.properties["insar:reference_datetime"] == "2021-01-01T12:00:00Z"
    assert ext_item.properties["insar:secondary_datetime"] == "2021-01-01T12:00:00Z"

    # assert ext_item.validate()


def test_item_apply(ext_item: pystac.Item) -> None:
    insar = InsarExtension.ext(ext_item)

    dt1 = datetime(2020, 2, 1, tzinfo=timezone.utc)
    dt2 = datetime(2020, 2, 13, tzinfo=timezone.utc)

    insar.apply(
        perpendicular_baseline=1,
        temporal_baseline=2,
        height_of_ambiguity=3,
        reference_datetime=dt1,
        secondary_datetime=dt2,
        processing_dem="A",
        geocoding_dem="B",
    )

    assert insar.perpendicular_baseline == 1.0
    assert insar.temporal_baseline == 2.0
    assert insar.height_of_ambiguity == 3.0
    assert insar.reference_datetime == dt1
    assert insar.secondary_datetime == dt2
    assert insar.processing_dem == "A"
    assert insar.geocoding_dem == "B"


def test_set_to_none_pops_from_dict(ext_item: pystac.Item) -> None:
    insar = InsarExtension.ext(ext_item)

    assert "insar:processing_dem" in ext_item.properties
    insar.processing_dem = None
    assert "insar:processing_dem" not in ext_item.properties

    assert "insar:perpendicular_baseline" in ext_item.properties
    insar.perpendicular_baseline = None
    assert "insar:perpendicular_baseline" not in ext_item.properties


def test_number_validation_errors(ext_item: pystac.Item) -> None:
    insar = InsarExtension.ext(ext_item)

    with pytest.raises(ValueError, match="expected a number"):
        insar.perpendicular_baseline = True  # type: ignore

    with pytest.raises(ValueError, match="expected a number"):
        insar.temporal_baseline = "12"  # type: ignore


def test_string_validation_errors(ext_item: pystac.Item) -> None:
    insar = InsarExtension.ext(ext_item)

    with pytest.raises(ValueError, match="expected a string"):
        insar.processing_dem = 1  # type: ignore

    with pytest.raises(ValueError, match="expected a string"):
        insar.geocoding_dem = False  # type: ignore


def test_asset_properties(ext_item: pystac.Item) -> None:
    asset = ext_item.assets["coherence"]

    insar = InsarExtension.ext(asset)

    assert insar.processing_dem == "COPDEM"

    insar.processing_dem = "XDEM"
    assert asset.extra_fields["insar:processing_dem"] == "XDEM"


def test_extension_not_implemented() -> None:
    item = pystac.Item.from_file(PLAIN_ITEM_URI)

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = InsarExtension.ext(item)

    asset = item.assets["thumbnail"]
    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = InsarExtension.ext(asset)

    # ownerless asset should succeed
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = InsarExtension.ext(ownerless_asset)


def test_item_ext_add_to() -> None:
    item = pystac.Item.from_file(PLAIN_ITEM_URI)
    assert InsarExtension.get_schema_uri() not in item.stac_extensions

    _ = InsarExtension.ext(item, add_if_missing=True)
    assert InsarExtension.get_schema_uri() in item.stac_extensions


def test_asset_ext_add_to() -> None:
    item = pystac.Item.from_file(PLAIN_ITEM_URI)
    asset = item.assets["thumbnail"]

    _ = InsarExtension.ext(asset, add_if_missing=True)
    assert InsarExtension.get_schema_uri() in item.stac_extensions


def test_asset_ext_add_to_ownerless_asset() -> None:
    item = pystac.Item.from_file(PLAIN_ITEM_URI)
    asset_dict = item.assets["thumbnail"].to_dict()
    asset = pystac.Asset.from_dict(asset_dict)

    # this mirrors EO behavior: cannot ensure owner has extension
    with pytest.raises(pystac.STACError):
        _ = InsarExtension.ext(asset, add_if_missing=True)


def test_extend_invalid_object() -> None:
    link = pystac.Link("child", "https://some-domain.com/some/path/to.json")
    with pytest.raises(pystac.ExtensionTypeError):
        InsarExtension.ext(link)  # type: ignore


def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError,
        match=r"^InsarExtension does not apply to type 'object'$",
    ):
        InsarExtension.ext(object())  # type: ignore


def test_exception_should_include_hint_if_obj_is_collection(
    collection: pystac.Collection,
) -> None:
    with pytest.raises(
        ExtensionTypeError,
        match="Hint: Did you mean to use `InsarExtension.summaries` instead?",
    ):
        InsarExtension.ext(collection)  # type: ignore


def test_summaries_get_set() -> None:
    col = pystac.Collection.from_file(INSAR_COLLECTION_URI)
    insar_summaries = InsarExtension.summaries(col)

    assert insar_summaries.processing_dem == "COPDEM"
    assert insar_summaries.geocoding_dem == "SRTM"
    assert insar_summaries.reference_datetime == datetime(2020, 1, 1, tzinfo=timezone.utc)

    insar_summaries.processing_dem = "X"
    insar_summaries.geocoding_dem = "Y"
    insar_summaries.reference_datetime = datetime(2020, 3, 1, tzinfo=timezone.utc)

    d = col.to_dict()
    assert d["summaries"]["insar:processing_dem"] == ["X"]
    assert d["summaries"]["insar:geocoding_dem"] == ["Y"]
    assert d["summaries"]["insar:reference_datetime"] == ["2020-03-01T00:00:00Z"]


def test_summaries_set_none_removes_key() -> None:
    col = pystac.Collection.from_file(INSAR_COLLECTION_URI)
    insar_summaries = InsarExtension.summaries(col)

    assert "insar:processing_dem" in col.summaries.to_dict()
    insar_summaries.processing_dem = None
    assert "insar:processing_dem" not in col.summaries.to_dict()


def test_summaries_adds_uri() -> None:
    col = pystac.Collection.from_file(INSAR_COLLECTION_URI)
    col.stac_extensions = []

    with pytest.raises(
        pystac.ExtensionNotImplemented, match="Extension 'insar' is not implemented"
    ):
        InsarExtension.summaries(col, add_if_missing=False)

    InsarExtension.summaries(col, add_if_missing=True)
    assert InsarExtension.get_schema_uri() in col.stac_extensions

    InsarExtension.remove_from(col)
    assert InsarExtension.get_schema_uri() not in col.stac_extensions


def test_ext_syntax(ext_item: pystac.Item) -> None:
    # this assumes you registered the extension in pystac.extensions.ext
    assert ext_item.ext.insar.perpendicular_baseline == 123.4
    assert ext_item.assets["coherence"].ext.insar.processing_dem == "COPDEM"


def test_ext_syntax_remove(ext_item: pystac.Item) -> None:
    ext_item.ext.remove("insar")
    assert ext_item.ext.has("insar") is False
    with pytest.raises(ExtensionNotImplemented):
        ext_item.ext.insar


def test_ext_syntax_add(item: pystac.Item) -> None:
    item.ext.add("insar")
    assert item.ext.has("insar") is True
    assert isinstance(item.ext.insar, InsarExtension)


@pytest.fixture
def ext_item_uri() -> str:
    return get_data_file("insar/insar-item.json")


@pytest.fixture
def ext_item(ext_item_uri: str) -> pystac.Item:
    return pystac.Item.from_file(ext_item_uri)
