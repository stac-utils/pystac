import json
from typing import Any

import pytest

from pystac import (
    Asset,
    Catalog,
    Collection,
    ExtensionNotImplemented,
    ExtensionTypeError,
    Item,
)
from pystac.extensions.file import ByteOrder, FileExtension, MappingObject
from tests.utils import TestCases, assert_to_from_dict

FILE_ITEM_EXAMPLE_URI = TestCases.get_path("data-files/file/item.json")
FILE_COLLECTION_EXAMPLE_URI = TestCases.get_path("data-files/file/collection.json")
FILE_CATALOG_EXAMPLE_URI = TestCases.get_path("data-files/file/catalog.json")


@pytest.fixture
def ext_item() -> Item:
    return Item.from_file(FILE_ITEM_EXAMPLE_URI)


@pytest.fixture
def ext_collection() -> Collection:
    return Collection.from_file(FILE_COLLECTION_EXAMPLE_URI)


@pytest.fixture
def ext_catalog() -> Catalog:
    return Catalog.from_file(FILE_CATALOG_EXAMPLE_URI)


def test_byte_order_to_str() -> None:
    assert ByteOrder.LITTLE_ENDIAN.value == "little-endian"
    assert ByteOrder.BIG_ENDIAN.value == "big-endian"


def test_mapping_object_create() -> None:
    values = [0, 1]
    summary = "clouds"
    m = MappingObject.create(values, summary)

    assert m.values == values
    assert m.summary == summary


def test_mapping_object_set_properties() -> None:
    values = [0, 1]
    summary = "clouds"
    m = MappingObject.create(values, summary)

    new_values = [3, 4]
    new_summary = "cloud shadow"
    m.summary = new_summary
    m.values = new_values

    assert m.values == new_values
    assert m.summary == new_summary


def test_mapping_object_apply() -> None:
    values = [0, 1]
    summary = "clouds"
    m = MappingObject.create(values, summary)

    new_values = [3, 4]
    new_summary = "cloud shadow"
    m.apply(new_values, new_summary)

    assert m.values == new_values
    assert m.summary == new_summary


def test_to_from_dict() -> None:
    with open(FILE_ITEM_EXAMPLE_URI) as f:
        item_dict = json.load(f)
    assert_to_from_dict(Item, item_dict)


@pytest.mark.vcr()
def test_validate_item(ext_item: Item) -> None:
    ext_item.validate()


@pytest.mark.vcr()
def test_validate_collection(ext_collection: Collection) -> None:
    ext_collection.validate()


@pytest.mark.vcr()
def test_validate_catalog(ext_catalog: Catalog) -> None:
    ext_catalog.validate()


@pytest.mark.parametrize(
    "asset_name,field,value",
    [
        ("thumbnail", "size", 146484),
        ("measurement", "header_size", 4096),
        ("thumbnail", "checksum", "90e40210f52acd32b09769d3b1871b420789456c"),
        ("thumbnail", "byte_order", ByteOrder.BIG_ENDIAN),
        (
            "calibrations",
            "local_path",
            (
                "S1A_EW_GRDM_1SSH_20181103T235855_20181103T235955_024430_02AD5D_5616.SAFE"
                "/annotation/calibration/calibration-s1a-ew-grd-hh-20181103t235855-201811"
                "03t235955-024430-02ad5d-001.xml"
            ),
        ),
    ],
)
def test_get_field_on_asset(
    ext_item: Item, asset_name: str, field: str, value: Any
) -> None:
    asset = ext_item.assets[asset_name]

    prop = asset.extra_fields[f"file:{field}"]
    attr = getattr(FileExtension.ext(asset), field)

    assert attr is not None
    assert attr == prop == value


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "asset_name,field,value",
    [
        ("thumbnail", "size", 1),
        ("measurement", "header_size", 8192),
        ("thumbnail", "checksum", "90e40210163700a8a6501eccd00b6d3b44ddaed0"),
        ("thumbnail", "byte_order", ByteOrder.LITTLE_ENDIAN),
        ("calibrations", "local_path", "different-file.xml"),
    ],
)
def test_set_field_on_asset(
    ext_item: Item, asset_name: str, field: str, value: Any
) -> None:
    asset = ext_item.assets[asset_name]

    original = asset.extra_fields[f"file:{field}"]
    setattr(FileExtension.ext(asset), field, value)
    new = asset.extra_fields[f"file:{field}"]

    assert new != original
    assert new == value
    assert ext_item.validate()


@pytest.mark.parametrize(
    "link_rel,field,value",
    [
        ("item", "size", 8675309),
    ],
)
def test_get_field_on_link(
    ext_catalog: Catalog, link_rel: str, field: str, value: Any
) -> None:
    link = ext_catalog.get_links(rel=link_rel)[0]

    prop = link.extra_fields[f"file:{field}"]
    attr = getattr(link.ext.file, field)

    assert attr is not None
    assert attr == prop == value


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "link_rel,field,value",
    [
        ("about", "size", 129302),
        ("about", "header_size", 4092),
        ("about", "checksum", "90e40210163700a8a6501eccd00b6d3b44ddaedb"),
        ("about", "byte_order", ByteOrder.BIG_ENDIAN),
        ("about", "local_path", "a/path"),
    ],
)
def test_set_field_on_link(
    ext_collection: Collection, link_rel: str, field: str, value: Any
) -> None:
    link = ext_collection.get_links(rel=link_rel)[0]

    setattr(link.ext.file, field, value)
    new = link.extra_fields[f"file:{field}"]

    assert new == value
    assert ext_collection.validate()


def test_item_asset_values(ext_item: Item) -> None:
    # Set/get
    asset = ext_item.assets["thumbnail"]
    file_ext = FileExtension.ext(asset)
    mapping_obj = {"values": [0], "summary": "clouds"}

    file_ext.apply(values=[MappingObject.from_dict(mapping_obj)])

    assert asset.extra_fields["file:values"] == [mapping_obj]

    values_field = asset.extra_fields["file:values"]
    assert isinstance(values_field, list)
    assert all(isinstance(mapping_obj, dict) for mapping_obj in values_field)


def test_item_asset_apply(ext_item: Item) -> None:
    asset = ext_item.assets["thumbnail"]

    new_checksum = "90e40210163700a8a6501eccd00b6d3b44ddaed0"
    new_size = 1
    new_header_size = 8192
    new_mapping_obj = {"values": [0], "summary": "clouds"}
    new_values = [MappingObject.from_dict(new_mapping_obj)]
    new_byte_order = ByteOrder.LITTLE_ENDIAN
    new_local_path = "./my/thumbnail.png"

    assert asset.ext.file.checksum != new_checksum
    assert asset.ext.file.size != new_size
    assert asset.ext.file.header_size != new_header_size
    assert asset.ext.file.values != new_values
    assert asset.ext.file.byte_order != new_byte_order
    assert asset.ext.file.local_path != new_local_path

    asset.ext.file.apply(
        byte_order=new_byte_order,
        checksum=new_checksum,
        size=new_size,
        header_size=new_header_size,
        values=new_values,
        local_path=new_local_path,
    )

    assert asset.extra_fields["file:checksum"] == new_checksum
    assert asset.extra_fields["file:size"] == new_size
    assert asset.extra_fields["file:header_size"] == new_header_size
    assert asset.extra_fields["file:values"] == [new_mapping_obj]
    assert asset.extra_fields["file:byte_order"] == new_byte_order
    assert asset.extra_fields["file:local_path"] == new_local_path


def test_repr(ext_item: Item) -> None:
    asset = ext_item.assets["thumbnail"]
    file_ext = FileExtension.ext(asset)

    assert str(file_ext) == f"<AssetFileExtension Asset href={asset.href}>"


def test_migrates_old_checksum() -> None:
    example_path = TestCases.get_path(
        "data-files/examples/1.0.0-beta.2/extensions/checksum/examples/sentinel1.json"
    )
    item = Item.from_file(example_path)

    assert FileExtension.has_extension(item)
    assert (
        FileExtension.ext(item.assets["noises"]).checksum
        == "90e40210a30d1711e81a4b11ef67b28744321659"
    )


def test_extension_not_implemented(sample_item: Item) -> None:
    # Should raise exception if Item does not include extension URI
    asset = sample_item.assets["thumbnail"]

    with pytest.raises(ExtensionNotImplemented):
        FileExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = Asset.from_dict(asset.to_dict())
    FileExtension.ext(ownerless_asset)


def test_ext_add_to(sample_item: Item) -> None:
    asset = sample_item.assets["thumbnail"]
    assert FileExtension.get_schema_uri() not in sample_item.stac_extensions

    FileExtension.ext(asset, add_if_missing=True)
    assert FileExtension.get_schema_uri() in sample_item.stac_extensions


def test_should_raise_exception_when_passing_invalid_extension_object(
    sample_item: Item,
) -> None:
    with pytest.raises(
        ExtensionTypeError, match="FileExtension does not apply to type 'Item'"
    ):
        FileExtension.ext(sample_item, add_if_missing=True)  # type: ignore


@pytest.mark.vcr()
def test_migrate_from_v2_0_0() -> None:
    item = Item.from_file(
        "https://raw.githubusercontent.com/stac-extensions/file/v2.0.0/examples/item.json"
    )
    asset = item.assets["thumbnail"]
    assert FileExtension.get_schema_uri() in item.stac_extensions
    assert asset.ext.file.local_path is None
