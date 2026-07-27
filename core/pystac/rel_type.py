from pystac.utils import StringEnum


class RelType(StringEnum):
    """A list of common rel types that can be used in STAC Link metadata.
    See :stac-spec:`"Using Relation Types <best-practices.md#using-relation-types>`
    in the STAC Best Practices for guidelines on using relation types. You may also want
    to refer to the "Relation type" documentation for
    :stac-spec:`Catalogs <catalog-spec/catalog-spec.md#relation-types>`,
    :stac-spec:`Collections <collection-spec/collection-spec.md#relation-types>`,
    or :stac-spec:`Items <item-spec/item-spec.md#relation-types>` for relation types
    specific to those STAC objects.
    """

    ALTERNATE = "alternate"
    CANONICAL = "canonical"
    CHILD = "child"
    COLLECTION = "collection"
    ITEM = "item"
    ITEMS = "items"
    LICENSE = "license"
    DERIVED_FROM = "derived_from"
    NEXT = "next"
    PARENT = "parent"
    PREV = "prev"
    PREVIEW = "preview"
    ROOT = "root"
    SELF = "self"
    VIA = "via"
