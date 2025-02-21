from pathlib import Path

import pytest

import pystac
from pystac import ExtensionTypeError, Item
from pystac.extensions.table import Column, TableExtension
from tests.utils import TestCases

@pytest.fixture
def example_uri() -> str:
    return TestCases.get_path("data-files/table/item.json")


@pytest.mark.vcr()
def test_validate(self) -> None:
    item = pystac.Item.from_file(self.example_uri)
    item.validate()

def test_extension_not_implemented(self) -> None:
    # Should raise exception if item does not include extension URI
    item = pystac.Item.from_file(self.example_uri)
    item.stac_extensions.remove(TableExtension.get_schema_uri())

    with self.assertRaises(pystac.ExtensionNotImplemented):
        _ = TableExtension.ext(item)

    # Should raise exception if owning item does not include extension URI
    asset = item.assets["data"]

    with self.assertRaises(pystac.ExtensionNotImplemented):
        _ = TableExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = TableExtension.ext(ownerless_asset)

def test_item_ext_add_to(self) -> None:
    item = pystac.Item.from_file(self.example_uri)
    item.stac_extensions.remove(TableExtension.get_schema_uri())

    _ = TableExtension.ext(item, add_if_missing=True)

    self.assertIn(TableExtension.get_schema_uri(), item.stac_extensions)

def test_asset_ext_add_to(self) -> None:
    item = pystac.Item.from_file(self.example_uri)
    item.stac_extensions.remove(TableExtension.get_schema_uri())

    self.assertNotIn(TableExtension.get_schema_uri(), item.stac_extensions)
    asset = item.assets["data"]

    _ = TableExtension.ext(asset, add_if_missing=True)
    self.assertIn(TableExtension.get_schema_uri(), item.stac_extensions)

def test_should_raise_exception_when_passing_invalid_extension_object(
    self,
) -> None:
    self.assertRaisesRegex(
        ExtensionTypeError,
        r"^TableExtension does not apply to type 'object'$",
        TableExtension.ext,
        object(),
    )


def test_item_with_table_extension_is_serilalizable_and_roundtrips(
    tmp_path: Path,
) -> None:
    example_uri = TestCases.get_path("data-files/table/item.json")
    item = pystac.Item.from_file(example_uri)
    # add column metadata
    tab_ext = TableExtension.ext(item, add_if_missing=True)
    columns = [
        Column({"name": "col_1", "type": "str"}),
        Column({"name": "col_2", "type": "byte_array"}),
    ]
    tab_ext.columns = columns
    item.save_object(dest_href=str(tmp_path / "item.json"))
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
def test_migrate(schema_uri: str, item: Item) -> None:
    item_dict = item.to_dict(include_self_link=False, transform_hrefs=False)
    item_dict["stac_extensions"] = [schema_uri]
    item = Item.from_dict(item_dict, migrate=True)
    assert item.stac_extensions == [
        "https://stac-extensions.github.io/table/v1.2.0/schema.json"
    ]
