from enum import Enum


class RelType(str, Enum):
    """A list of common rel types that can be used in STAC Link metadata."""

    def __str__(self) -> str:
        return str(self.value)

    # Core + best practices
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

    # Label Extension
    SOURCE = "source"

    # Version Extension
    LATEST = "latest-version"
    PREDECESSOR = "predecessor-version"
    SUCCESSOR = "successor-version"
