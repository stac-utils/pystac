from collections.abc import Sequence

DEFAULT_STAC_VERSION = "1.1.0"

DEFAULT_BBOX: Sequence[int | float] = [-180, -90, 180, 90]
DEFAULT_INTERVAL: list[str | None] = [None, None]
DEFAULT_LICENSE = "other"

CATALOG_TYPE = "Catalog"
COLLECTION_TYPE = "Collection"
ITEM_TYPE = "Feature"

CHILD = "child"
ITEM = "item"
PARENT = "parent"
ROOT = "root"
SELF = "self"
COLLECTION = "collection"
