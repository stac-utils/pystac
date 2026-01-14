import pytest

from pystac import Asset, Band, Collection, Item


@pytest.mark.parametrize(
    "data", [{"name": "B01"}, {}, {"name": "B01", "eo:common_name": "blue"}]
)
def test_roundtrip_to_dict(data: dict[str, str]) -> None:
    band = Band(**data)
    assert band.to_dict() == data


def test_get_band_fields() -> None:
    band = Band(name="foo", field="one")
    assert band["name"] == "foo"
    assert band["field"] == "one"
    assert "field" in band
    assert band.extra_fields["field"] == "one"


def test_set_band_fields() -> None:
    band = Band()
    band["field"] = "two"
    assert "field" in band
    assert band["field"] == "two"
    assert band.extra_fields["field"] == "two"


def test_set_band_name() -> None:
    band = Band()
    band.name = "B01"
    assert band.name == "B01"
    assert band["name"] == "B01"

    band["name"] = "B02"
    assert band.name == "B02"
    assert band["name"] == "B02"


def test_set_bands_on_asset() -> None:
    asset = Asset(href="foo", bands=[Band(name="B01")])
    assert asset.bands == [Band(name="B01")]


def test_set_bands_on_asset_as_dict() -> None:
    asset = Asset(href="foo", bands=[{"name": "B01"}])
    assert asset.bands == [Band(name="B01")]


def test_asset_to_dict_includes_bands() -> None:
    asset = Asset(href="foo", bands=[Band("B01")])
    asset_dict = asset.to_dict()
    assert "bands" in asset_dict
    assert asset_dict["bands"] == [{"name": "B01"}]


def test_set_bands_on_item() -> None:
    item = Item(id="foo", properties={"bands": [Band("B01")]})
    assert item.properties.bands == [Band("B01")]


def test_set_bands_on_item_as_dict() -> None:
    item = Item(id="foo", properties={"bands": [{"name": "B01"}]})
    assert item.properties.bands == [Band("B01")]


def test_item_to_dict_includes_bands() -> None:
    item = Item(id="foo", properties={"bands": [Band("B01")]})
    properties_dict = item.to_dict()["properties"]
    assert "bands" in properties_dict
    assert properties_dict["bands"] == [{"name": "B01"}]


def test_set_bands_on_collection() -> None:
    collection = Collection(id="foo", description="foo", bands=[Band("B01")])
    assert collection.bands == [Band("B01")]


def test_set_bands_on_collection_as_dict() -> None:
    collection = Collection(id="foo", description="foo", bands=[{"name": "B01"}])
    assert collection.bands == [Band("B01")]


def test_collection_to_dict_includes_bands() -> None:
    collection = Collection(id="foo", description="foo", bands=[Band("B01")])
    collection_dict = collection.to_dict()
    assert "bands" in collection_dict
    assert collection_dict["bands"] == [{"name": "B01"}]
