from pathlib import Path

import pytest
from pystac.extensions.table import Column, TableExtension

import pystac
from pystac import ExtensionTypeError, Item
from tests.v1.utils import TestCases


@pytest.fixture
def table_item() -> Item:
    return pystac.Item.from_file(TestCases.get_path("data-files/table/item.json"))


@pytest.mark.vcr()
def test_validate(table_item: Item) -> None:
    table_item.validate()


def test_extension_not_implemented(table_item: Item) -> None:
    # Should raise exception if item does not include extension URI
    table_item.stac_extensions.remove(TableExtension.get_schema_uri())

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = TableExtension.ext(table_item)

    # Should raise exception if owning item does not include extension URI
    asset = table_item.assets["data"]

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = TableExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = TableExtension.ext(ownerless_asset)


def test_item_ext_add_to(table_item: Item) -> None:
    table_item.stac_extensions.remove(TableExtension.get_schema_uri())

    _ = TableExtension.ext(table_item, add_if_missing=True)

    assert TableExtension.get_schema_uri() in table_item.stac_extensions


def test_asset_ext_add_to(table_item: Item) -> None:
    table_item.stac_extensions.remove(TableExtension.get_schema_uri())

    assert TableExtension.get_schema_uri() not in table_item.stac_extensions
    asset = table_item.assets["data"]

    _ = TableExtension.ext(asset, add_if_missing=True)
    assert TableExtension.get_schema_uri() in table_item.stac_extensions


def test_should_raise_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError, match=r"^TableExtension does not apply to type 'object'$"
    ):
        # calling it wrong on purpose so ------v
        TableExtension.ext(object())  # type: ignore


def test_item_with_table_extension_is_serilalizable_and_roundtrips(
    tmp_path: Path,
    table_item: Item,
) -> None:
    # add column metadata
    tab_ext = TableExtension.ext(table_item, add_if_missing=True)
    columns = [
        Column({"name": "col_1", "type": "str"}),
        Column({"name": "col_2", "type": "byte_array"}),
    ]
    tab_ext.columns = columns
    table_item.save_object(dest_href=str(tmp_path / "item.json"))
    assert all(isinstance(c, Column) for c in tab_ext.columns)
    assert all(
        before.properties == after.properties
        for before, after in zip(columns, tab_ext.columns)
    )


@pytest.mark.parametrize(
    "schema_uri",
    (
        "https://stac-extensions.github.io/table/v1.0.0/schema.json",
        "https://stac-extensions.github.io/table/v1.0.1/schema.json",
        "https://stac-extensions.github.io/table/v1.1.0/schema.json",
    ),
)
def test_migrate(schema_uri: str, table_item: Item) -> None:
    item_dict = table_item.to_dict(include_self_link=False, transform_hrefs=False)
    item_dict["stac_extensions"] = [schema_uri]
    assert Item.from_dict(item_dict, migrate=True).stac_extensions == [
        "https://stac-extensions.github.io/table/v1.2.0/schema.json"
    ]
