from typing import Any

from .asset import Asset, ItemAsset
from .catalog import Catalog
from .collection import Collection
from .constants import DEFAULT_STAC_VERSION
from .container import Container
from .errors import (
    PystacError,
    PystacWarning,
    StacError,
    StacWarning,
)
from .extent import Extent, SpatialExtent, TemporalExtent
from .functions import get_stac_version, read_dict, set_stac_version
from .io import DefaultReader, DefaultWriter, read_file, write_file
from .item import Item
from .link import Link
from .media_type import MediaType
from .render import Render
from .stac_object import STACObject


def __getattr__(name: str) -> Any:
    if name == "StacIO":
        # We defer loading so we don't trigger a `FutureWarning`
        from .stac_io import StacIO

        return StacIO
    else:
        raise AttributeError(name)
