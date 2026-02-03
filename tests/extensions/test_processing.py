# tests/extensions/test_processing.py
from __future__ import annotations

from datetime import datetime, timezone

import pytest

import pystac

# Terradue branch: expects pystac/extensions/processing.py
# If the names differ in your branch, adjust these imports accordingly.
from pystac.extensions.processing import (  # type: ignore
    ProcessingExtension,
    ProcessingProviderExtension,
)


def _utc_rfc3339(dt: datetime) -> str:
    """Stable UTC RFC3339 string for processing:datetime."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def test_processing_ext_item_apply_sets_fields_and_schema(item: pystac.Item) -> None:
    processing_dt = datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    software = {"IPF-S2L1C": "02.06", "my-lib": "1.2.3"}

    ext = ProcessingExtension.ext(item, add_if_missing=True)
    ext.apply(
        level="L1C",
        facility="Copernicus S2 Processing and Archiving Facility",
        lineage="Generation of Level-1C User Product",
        datetime=_utc_rfc3339(processing_dt),
        version="02.06",
        software=software,
    )

    # extension schema should be enabled on the item
    assert any("processing" in uri for uri in item.stac_extensions)

    # raw properties written
    assert item.properties["processing:level"] == "L1C"
    assert item.properties["processing:facility"] == "Copernicus S2 Processing and Archiving Facility"
    assert item.properties["processing:lineage"] == "Generation of Level-1C User Product"
    assert item.properties["processing:datetime"] == _utc_rfc3339(processing_dt)
    assert item.properties["processing:version"] == "02.06"
    assert item.properties["processing:software"] == software

    # typed getters (common PySTAC pattern)
    assert ext.level == "L1C"
    assert ext.facility == "Copernicus S2 Processing and Archiving Facility"
    assert ext.lineage == "Generation of Level-1C User Product"
    assert ext.datetime == _utc_rfc3339(processing_dt)
    assert ext.version == "02.06"
    assert ext.software == software


def test_processing_ext_item_unset_optional_fields_are_absent(item: pystac.Item) -> None:
    ext = ProcessingExtension.ext(item, add_if_missing=True)
    ext.apply(level="L2A")  # minimal, required-by-your-impl (if any)

    # Ensure unspecified optional keys are not forced into properties
    for k in (
        "processing:facility",
        "processing:lineage",
        "processing:datetime",
        "processing:version",
        "processing:software",
    ):
        assert k not in item.properties or item.properties[k] is None


def test_processing_provider_ext_writes_into_provider_extra_fields(collection: pystac.Collection) -> None:
    """
    Spec recommends placing processing fields in Collection Provider Objects for producer/processor.
    This test checks provider.extra_fields (or equivalent) gets the processing:* keys. :contentReference[oaicite:1]{index=1}
    """
    provider = pystac.Provider(
        name="European Union/ESA/Copernicus",
        roles=["producer"],
        url="https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi",
    )
    collection.providers = [provider]

    pext = ProcessingProviderExtension.ext(provider, add_if_missing=True)
    pext.apply(
        level="L1C",
        facility="Copernicus S2 Processing and Archiving Facility",
        software={"IPF-S2L1C": "02.06"},
    )

    # Provider objects in PySTAC store unknown fields in extra_fields
    extra = getattr(provider, "extra_fields", {})
    assert extra["processing:level"] == "L1C"
    assert extra["processing:facility"] == "Copernicus S2 Processing and Archiving Facility"
    assert extra["processing:software"] == {"IPF-S2L1C": "02.06"}

    # Typed getters round-trip
    assert pext.level == "L1C"
    assert pext.facility == "Copernicus S2 Processing and Archiving Facility"
    assert pext.software == {"IPF-S2L1C": "02.06"}


def test_processing_ext_type_error_on_wrong_object() -> None:
    cat = pystac.Catalog(id="c", description="d")

    with pytest.raises(pystac.ExtensionTypeError):
        ProcessingExtension.ext(cat, add_if_missing=False)  # type: ignore[arg-type]


def test_processing_provider_ext_type_error_on_wrong_object(item: pystac.Item) -> None:
    with pytest.raises(pystac.ExtensionTypeError):
        ProcessingProviderExtension.ext(item, add_if_missing=False)  # type: ignore[arg-type]
