from typing import Any

from .asset import Asset
from .catalog import Catalog
from .collection import Collection
from .constants import DEFAULT_STAC_VERSION
from .errors import PySTACError, STACError, STACWarning
from .extent import Extent, SpatialExtent, TemporalExtent
from .functions import get_stac_version, read_dict, set_stac_version
from .io import read_file, write_file
from .item import Item
from .item_collection import ItemCollection
from .link import Link
from .media_type import MediaType
from .stac_object import STACObject


def __getattr__(name: str) -> Any:
    if name == "StacIO":
        # We defer loading so we don't trigger a `FutureWarning`
        from .stac_io import StacIO

        return StacIO
    else:
        raise AttributeError(name)


__all__ = [
    "Asset",
    "Catalog",
    "Collection",
    "DEFAULT_STAC_VERSION",
    "Item",
    "ItemCollection",
    "Link",
    "PySTACError",
    "MediaType",
    "Extent",
    "STACError",
    "STACObject",
    "STACWarning",
    "SpatialExtent",
    "TemporalExtent",
    "get_stac_version",
    "read_dict",
    "read_file",
    "set_stac_version",
    "write_file",
]
