from typing import Any

from .asset import Asset
from .catalog import Catalog
from .collection import Collection
from .constants import DEFAULT_STAC_VERSION
from .errors import PySTACError, STACError, STACWarning
from .extent import SpatialExtent, TemporalExtent
from .functions import get_stac_version, read_dict, set_stac_version
from .io import read_file, write_file
from .item import Item
from .link import Link
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
    "Link",
    "PySTACError",
    "STACError",
    "STACWarning",
    "SpatialExtent",
    "TemporalExtent",
    "get_stac_version",
    "read_dict",
    "read_file",
    "STACObject",
    "set_stac_version",
    "write_file",
]
