# tests/extensions/test_product.py
from __future__ import annotations

import pytest
import pystac

# Terradue branch should provide these in pystac/extensions/product.py
# If names differ in your branch, adjust imports accordingly.
from pystac.extensions.product import (  # type: ignore
    ProductExtension,
    ProductProviderExtension,
)


def test_product_ext_item_apply_sets_fields_and_schema(item: pystac.Item) -> None:
    """
    Basic "apply + schema + raw properties + getters" test.
    """
    ext = ProductExtension.ext(item, add_if_missing=True)

    # The Product extension is "generic product-related properties for STAC".
    # Adjust the apply(...) signature to your implementation if needed.
    ext.apply(
        name="S2MSI2A",
        version="05.10",
        type="OPTICAL",  # e.g. a product family / category if your impl supports it
    )

    # schema should be enabled on the item
    assert any("product" in uri for uri in item.stac_extensions), (
        "Expected Product extension schema URI to be present in item.stac_extensions"
    )

    # raw properties (canonical keys)
    assert item.properties["product:name"] == "S2MSI2A"
    assert item.properties["product:version"] == "05.10"
    assert item.properties["product:type"] == "OPTICAL"

    # typed getters round-trip
    assert ext.name == "S2MSI2A"
    assert ext.version == "05.10"
    assert ext.type == "OPTICAL"


def test_product_ext_unset_optional_fields_are_absent(item: pystac.Item) -> None:
    """
    Ensure optional keys are not force-written when not supplied.
    """
    ext = ProductExtension.ext(item, add_if_missing=True)
    ext.apply(name="S2MSI2A")  # minimal

    # If your implementation requires additional fields, change the call above
    # and keep the "optional keys" list aligned with product.py.
    for k in (
        "product:type",
        "product:version",
        "product:uri",
        "product:timeliness",
        "product:processing_level",
    ):
        assert k not in item.properties or item.properties[k] is None


def test_product_ext_required_name_on_read(item: pystac.Item) -> None:
    """
    If your extension marks product:name as required (common), accessing should error
    when missing. Keep this if product.py uses get_required(...).
    """
    ext = ProductExtension.ext(item, add_if_missing=True)

    item.properties.pop("product:name", None)

    with pytest.raises(Exception):
        _ = ext.name


def test_product_provider_ext_writes_into_provider_extra_fields(collection: pystac.Collection) -> None:
    """
    Many PySTAC extensions support Provider objects via extra_fields.
    This follows the same pattern used by other extension tests.
    """
    provider = pystac.Provider(
        name="ACME Processing Center",
        roles=["producer", "processor"],
        url="https://example.invalid",
    )
    collection.providers = [provider]

    pext = ProductProviderExtension.ext(provider, add_if_missing=True)
    pext.apply(
        name="S2MSI2A",
        version="05.10",
    )

    extra = getattr(provider, "extra_fields", {})
    assert extra["product:name"] == "S2MSI2A"
    assert extra["product:version"] == "05.10"

    assert pext.name == "S2MSI2A"
    assert pext.version == "05.10"


def test_product_ext_type_error_on_wrong_object() -> None:
    cat = pystac.Catalog(id="c", description="d")

    with pytest.raises(pystac.ExtensionTypeError):
        ProductExtension.ext(cat, add_if_missing=False)  # type: ignore[arg-type]


def test_product_provider_ext_type_error_on_wrong_object(item: pystac.Item) -> None:
    with pytest.raises(pystac.ExtensionTypeError):
        ProductProviderExtension.ext(item, add_if_missing=False)  # type: ignore[arg-type]
