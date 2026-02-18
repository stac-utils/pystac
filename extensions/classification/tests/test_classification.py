import json
import logging
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pystac
import pytest
from dateutil.parser import parse
from pystac import Collection, Item
from pystac.extensions.classification import (
    CLASSES_PROP,
    DEFAULT_VERSION,
    SCHEMA_URI_PATTERN,
    SUPPORTED_VERSIONS,
    Bitfield,
    Classification,
    ClassificationExtension,
)
from pystac.extensions.raster import RasterBand, RasterExtension

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

DATA_FILES = Path(__file__).resolve().parent / "data-files"

LANDSAT_EXAMPLE_URI = str(DATA_FILES / "classification_landsat_example.json")
CLASSIFICATION_COLLECTION_RASTER_URI = str(
    DATA_FILES / "collection-item-assets-raster-bands.json"
)
PLAIN_ITEM = str(DATA_FILES / "item/sample-item.json")


@pytest.fixture
def item_dict() -> dict[str, Any]:
    with open(LANDSAT_EXAMPLE_URI) as f:
        return cast(dict[str, Any], json.load(f))


@pytest.fixture
def landsat_item() -> Item:
    return Item.from_file(LANDSAT_EXAMPLE_URI)


@pytest.fixture
def plain_item() -> Item:
    return Item.from_file(PLAIN_ITEM)


@pytest.fixture
def classification_collection() -> Collection:
    return Collection.from_file(CLASSIFICATION_COLLECTION_RASTER_URI)


def test_stac_extensions(landsat_item: Item) -> None:
    assert ClassificationExtension.has_extension(landsat_item)


def test_classification_object() -> None:
    c = Classification.create(
        name="dummy",
        description="empty class",
        value=0,
        title="dummy title",
        color_hint="FF00AB",
        nodata=True,
        percentage=20.3,
        count=2,
    )
    assert c.name == "dummy"
    assert c.description == "empty class"
    assert c.color_hint == "FF00AB"
    assert c.value == 0
    assert c.title == "dummy title"
    assert c.nodata is True
    assert c.percentage == 20.3
    assert c.count == 2

    assert Classification(c.to_dict()) == c
    with pytest.raises(NotImplementedError):
        c == "blah"


def test_bitfield_object() -> None:
    b = Bitfield.create(
        offset=0,
        length=1,
        classes=[
            Classification.create(name="no", value=0),
            Classification.create(name="yes", value=1),
        ],
        roles=["data"],
        description="dummy description",
        name="dummy",
    )
    assert b.offset == 0
    assert b.length == 1
    assert len(b.classes) == 2
    assert b.roles == ["data"]
    assert b.description == "dummy description"
    assert b.name == "dummy"


def test_get_schema_uri(landsat_item: Item) -> None:
    with pytest.raises(DeprecationWarning):
        assert any(
            [
                uri in landsat_item.stac_extensions
                for uri in ClassificationExtension.get_schema_uris()
            ]
        )


def test_ext_raises_if_item_does_not_conform(plain_item: Item) -> None:
    with pytest.raises(pystac.errors.ExtensionNotImplemented):
        ClassificationExtension.ext(plain_item)


def test_ext_raises_on_collection(classification_collection: Collection) -> None:
    with pytest.raises(
        pystac.errors.ExtensionTypeError,
        match="ClassificationExtension does not apply to type 'Collection'",
    ) as e:
        ClassificationExtension.ext(classification_collection)  # type:ignore
    assert "Hint" in str(e.value)


@pytest.mark.vcr()
def test_apply_bitfields(plain_item: Item) -> None:
    ClassificationExtension.add_to(plain_item)
    ClassificationExtension.ext(plain_item).apply(
        bitfields=[
            Bitfield.create(
                offset=0,
                length=1,
                classes=[
                    Classification.create(name="no", value=0),
                    Classification.create(name="yes", value=1),
                ],
            )
        ]
    )

    plain_item.validate()
    assert (
        ClassificationExtension.ext(plain_item).bitfields is not None
        and len(cast(list[Bitfield], ClassificationExtension.ext(plain_item).bitfields))
        == 1
    )
    assert (
        cast(list[Bitfield], ClassificationExtension.ext(plain_item).bitfields)[
            0
        ].offset
        == 0
    )
    assert (
        cast(list[Bitfield], ClassificationExtension.ext(plain_item).bitfields)[
            0
        ].length
        == 1
    )
    assert (
        ClassificationExtension.ext(plain_item).bitfields is not None
        and len(
            cast(list[Bitfield], ClassificationExtension.ext(plain_item).bitfields)[
                0
            ].classes
        )
        == 2
    )


@pytest.mark.vcr()
def test_apply_classes(plain_item: Item) -> None:
    ClassificationExtension.add_to(plain_item)
    ClassificationExtension.ext(plain_item).apply(
        classes=[
            Classification.create(name="no", value=0),
            Classification.create(name="yes", value=1),
        ]
    )
    plain_item.validate()
    assert (
        ClassificationExtension.ext(plain_item).classes is not None
        and len(
            cast(list[Classification], ClassificationExtension.ext(plain_item).classes)
        )
        == 2
    )


def test_create_classes(plain_item: Item) -> None:
    ClassificationExtension.add_to(plain_item)
    ext = ClassificationExtension.ext(plain_item)
    ext.apply(
        bitfields=[
            Bitfield.create(
                offset=0,
                length=1,
                classes=[
                    Classification.create(name="no", value=0),
                    Classification.create(name="yes", value=1),
                ],
            )
        ]
    )
    ext.classes = [
        Classification.create(name="no", value=0),
        Classification.create(name="yes", value=1),
    ]
    assert ext.bitfields is None
    ext.bitfields = [
        Bitfield.create(
            offset=0,
            length=1,
            classes=[
                Classification.create(name="no", value=0),
                Classification.create(name="yes", value=1),
            ],
        )
    ]
    assert ext.classes is None


def test_create() -> None:
    field = Bitfield.create(
        name="cloud_confidence",
        description="Cloud confidence levels",
        offset=8,
        length=2,
        classes=[
            Classification.create(
                name="not_set", description="No confidence level set", value=0
            ),
            Classification.create(
                name="low", description="Low confidence cloud", value=1
            ),
            Classification.create(
                name="medium", description="Medium confidence cloud", value=2
            ),
            Classification.create(
                name="high", description="High confidence cloud", value=3
            ),
        ],
    )

    logger.info(field)


def test_color_hint_formatting() -> None:
    with pytest.raises(Exception):
        Classification.create(value=0, name="water", color_hint="#0000ff")
    Classification.create(value=0, name="water", color_hint="0000FF")


def test_to_from_dict(item_dict: dict[str, Any]) -> None:
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

    d1 = deepcopy(item_dict)
    d2 = Item.from_dict(item_dict, migrate=False).to_dict()
    _parse_times(d1)
    _parse_times(d2)
    assert d1 == d2, f"Mismatch between dictionaries: \n{d1}\n{d2}"


def test_add_to(plain_item: Item) -> None:
    assert ClassificationExtension.get_schema_uri() not in plain_item.stac_extensions

    # Check that the URI gets added to stac_extensions
    ClassificationExtension.add_to(plain_item)
    assert ClassificationExtension.get_schema_uri() in plain_item.stac_extensions

    # Check that the URI only gets added once, regardless of how many times add_to
    # is called.
    ClassificationExtension.add_to(plain_item)
    ClassificationExtension.add_to(plain_item)

    classification_uris = [
        uri
        for uri in plain_item.stac_extensions
        if uri == ClassificationExtension.get_schema_uri()
    ]
    assert len(classification_uris) == 1


@pytest.mark.vcr()
def test_validate_classification(landsat_item: Item) -> None:
    landsat_item.validate()


def test_add_item_classes(plain_item: Item) -> None:
    item_ext = ClassificationExtension.ext(plain_item, add_if_missing=True)
    item_ext.__repr__()
    assert item_ext.classes is None
    item_ext.classes = [Classification.create(name="dummy", value=0)]
    assert item_ext.properties[CLASSES_PROP] == [{"value": 0, "name": "dummy"}]


def test_add_asset_classes(plain_item: Item) -> None:
    ClassificationExtension.ext(plain_item, add_if_missing=True)
    asset = plain_item.assets["analytic"]
    assert CLASSES_PROP not in asset.extra_fields.keys()
    asset_ext = ClassificationExtension.ext(asset)
    asset_ext.__repr__()
    asset_ext.classes = [Classification.create(value=0, name="dummy")]
    assert CLASSES_PROP in asset.extra_fields.keys()
    assert asset.extra_fields[CLASSES_PROP] == [{"value": 0, "name": "dummy"}]


def test_item_asset_raster_classes(classification_collection: Collection) -> None:
    assert classification_collection.item_assets
    item_asset = classification_collection.item_assets["cloud-mask-raster"]
    raster_bands = cast(list[RasterBand], RasterExtension.ext(item_asset).bands)
    raster_bands_ext = ClassificationExtension.ext(raster_bands[0])
    raster_bands_ext.__repr__()
    assert raster_bands_ext.classes is not None


def test_item_assets_extension(classification_collection: Collection) -> None:
    assert classification_collection.item_assets
    item_asset = classification_collection.item_assets["cloud-mask-raster"]
    ext = ClassificationExtension.ext(item_asset)
    ext.__repr__()
    assert (
        ClassificationExtension.get_schema_uri()
        in classification_collection.stac_extensions
    )
    assert classification_collection.item_assets["cloud-mask-raster"].ext.has(
        "classification"
    )


def test_older_extension_version(landsat_item: Item) -> None:
    OLD_VERSION = list(set(SUPPORTED_VERSIONS) - {DEFAULT_VERSION})[0]
    new = SCHEMA_URI_PATTERN.format(version=DEFAULT_VERSION)
    old = SCHEMA_URI_PATTERN.format(version=OLD_VERSION)

    stac_extensions = set(landsat_item.stac_extensions)
    stac_extensions.remove(new)
    stac_extensions.add(old)
    item_as_dict = landsat_item.to_dict(include_self_link=False, transform_hrefs=False)
    item_as_dict["stac_extensions"] = list(stac_extensions)
    item = Item.from_dict(item_as_dict, migrate=False)
    assert ClassificationExtension.has_extension(item)
    assert old in item.stac_extensions

    migrated_item = pystac.Item.from_dict(item_as_dict, migrate=True)
    assert ClassificationExtension.has_extension(migrated_item)
    assert new in migrated_item.stac_extensions


def test_migrate_color_hint(plain_item: Item) -> None:
    item_dict = plain_item.to_dict(include_self_link=False, transform_hrefs=False)
    item_dict["stac_extensions"] = [
        "https://stac-extensions.github.io/classification/v1.0.0/schema.json"
    ]
    item_dict["assets"]["analytic"]["classification:classes"] = [
        {"value": 42, "color-hint": "#ffffff"}
    ]
    item = Item.from_dict(item_dict, migrate=True)
    classification = ClassificationExtension.ext(item.assets["analytic"])
    assert classification.classes
    assert classification.classes[0].color_hint == "#ffffff"
