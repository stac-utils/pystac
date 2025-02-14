from typing import Sequence

DEFAULT_STAC_VERSION = "1.1.0"
"""The default STAC version for this library."""

DEFAULT_BBOX: Sequence[int | float] = [-180, -90, 180, 90]
"""The default bounding box."""
DEFAULT_INTERVAL: Sequence[str | None] = [None, None]
"""The default temporal interval."""
DEFAULT_LICENSE = "other"
"""The default license."""

CATALOG_TYPE = "Catalog"
"""The type field of a JSON STAC Catalog."""
COLLECTION_TYPE = "Collection"
"""The type field of a JSON STAC Collection."""
ITEM_TYPE = "Feature"
"""The type field of a JSON STAC Item."""

CHILD = "child"
"""The child relation type, for links."""
ITEM = "item"
"""The item relation type, for links."""
PARENT = "parent"
"""The parent relation type, for links."""
ROOT = "root"
"""The root relation type, for links."""
SELF = "self"
"""The self relation type, for links."""
