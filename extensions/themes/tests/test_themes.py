from __future__ import annotations

from datetime import datetime
from typing import TypeAlias

import pytest

import pystac
from pystac.extensions.themes import (
    SCHEMA_URI,
    THEMES_EXTENSION_HOOKS,
    THEMES_PROP,
    Theme,
    ThemeConcept,
    ThemesExtension,
)

TemporalIntervals: TypeAlias = list[list[datetime | None]]


def make_theme() -> Theme:
    return Theme(
        scheme="https://example.com/themes",
        concepts=[
            ThemeConcept(
                id="climate",
                title="Climate",
                description="Climate-related resources",
                url="https://example.com/concepts/climate",
            )
        ],
    )


def make_item() -> pystac.Item:
    return pystac.Item(
        id="item-1",
        geometry={"type": "Point", "coordinates": [0.0, 0.0]},
        bbox=[0.0, 0.0, 0.0, 0.0],
        datetime=pystac.utils.str_to_datetime("2026-01-01T00:00:00Z"),
        properties={},
    )


def make_collection() -> pystac.Collection:
    temporal_intervals: TemporalIntervals = [[None, None]]
    return pystac.Collection(
        id="collection-1",
        description="Test collection",
        extent=pystac.Extent(
            pystac.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
            pystac.TemporalExtent(temporal_intervals),
        ),
        license="proprietary",
    )


def test_theme_concept_to_dict_omits_unset_optional_fields() -> None:
    assert ThemeConcept(id="oceans").to_dict() == {"id": "oceans"}


def test_theme_roundtrip_from_dict() -> None:
    theme_dict = {
        "scheme": "https://example.com/themes",
        "concepts": [
            {
                "id": "climate",
                "title": "Climate",
                "description": "Climate-related resources",
                "url": "https://example.com/concepts/climate",
            }
        ],
    }

    assert Theme.from_dict(theme_dict).to_dict() == theme_dict


def test_item_themes_roundtrip_and_accessor() -> None:
    item = make_item()
    ext = ThemesExtension.ext(item, add_if_missing=True)
    ext.apply([make_theme()])

    assert SCHEMA_URI in item.stac_extensions
    assert item.properties[THEMES_PROP][0]["scheme"] == "https://example.com/themes"
    assert ext.themes is not None
    assert ext.themes[0].concepts[0].id == "climate"
    assert item.ext.themes.themes is not None


def test_item_themes_can_be_cleared() -> None:
    item = make_item()
    ext = ThemesExtension.ext(item, add_if_missing=True)
    ext.themes = [make_theme()]
    ext.themes = None

    assert THEMES_PROP not in item.properties
    assert ext.themes is None


def test_collection_themes_summaries_roundtrip() -> None:
    collection = make_collection()
    summaries = ThemesExtension.summaries(collection, add_if_missing=True)
    summaries.themes = [make_theme()]

    assert SCHEMA_URI in collection.stac_extensions
    assert collection.summaries.lists[THEMES_PROP][0]["concepts"][0]["id"] == (
        "climate"
    )
    assert summaries.themes is not None
    assert summaries.themes[0].scheme == "https://example.com/themes"


def test_collection_themes_summaries_can_be_cleared() -> None:
    collection = make_collection()
    summaries = ThemesExtension.summaries(collection, add_if_missing=True)
    summaries.themes = [make_theme()]
    summaries.themes = None

    assert THEMES_PROP not in collection.summaries.lists
    assert summaries.themes is None


def test_catalog_themes_roundtrip_and_accessor() -> None:
    catalog = pystac.Catalog(id="catalog-1", description="Test catalog")
    ext = ThemesExtension.ext(catalog, add_if_missing=True)
    ext.themes = [make_theme()]

    assert SCHEMA_URI in catalog.stac_extensions
    assert catalog.extra_fields[THEMES_PROP][0]["concepts"][0]["title"] == "Climate"
    assert ext.themes is not None
    assert ext.themes[0].concepts[0].url == "https://example.com/concepts/climate"
    assert catalog.ext.themes.themes is not None


def test_ext_requires_existing_extension_when_not_adding() -> None:
    with pytest.raises(pystac.ExtensionNotImplemented):
        ThemesExtension.ext(make_item())


def test_ext_rejects_unsupported_type() -> None:
    with pytest.raises(pystac.ExtensionTypeError):
        ThemesExtension.ext("not-a-stac-object")  # type: ignore[type-var]


def test_extension_hooks_are_declared() -> None:
    assert THEMES_EXTENSION_HOOKS.schema_uri == ThemesExtension.get_schema_uri()
    assert THEMES_EXTENSION_HOOKS.prev_extension_ids == set()
    assert pystac.STACObjectType.CATALOG in THEMES_EXTENSION_HOOKS.stac_object_types
    assert pystac.STACObjectType.COLLECTION in THEMES_EXTENSION_HOOKS.stac_object_types
    assert pystac.STACObjectType.ITEM in THEMES_EXTENSION_HOOKS.stac_object_types
