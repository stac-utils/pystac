from typing import Any

from typing_extensions import deprecated

from .asset import Asset
from .catalog import Catalog
from .collection import (
    Collection,
    Extent,
    Provider,
    ProviderRole,
    SpatialExtent,
    TemporalExtent,
)
from .common_metadata import CommonMetadata
from .constants import DEFAULT_STAC_VERSION
from .deserialize import from_dict
from .errors import (
    ExtensionNotImplemented,
    ExtensionTypeError,
    STACError,
    STACTypeError,
    STACValidationError,
)
from .io import read_file
from .item import Item
from .item_assets import ItemAssetDefinition
from .item_collection import ItemCollection
from .link import HIERARCHICAL_LINKS, Link
from .media_type import MediaType
from .stac_object import STACObject


def __getattr__(name: str) -> Any:
    match name:
        case "StacIO":
            from .stac_io import StacIO

            return StacIO

        case "STACObjectType":
            from .stac_object import STACObjectType

            return STACObjectType
        case "CatalogType":
            from .catalog import CatalogType

            return CatalogType
        case "get_stac_version":

            @deprecated("get_stac_version is deprecated")
            def get_stac_version() -> str:
                return DEFAULT_STAC_VERSION

            return get_stac_version  # pyright: ignore[reportDeprecated]
        case _:
            raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = [
    "Asset",
    "Catalog",
    "Collection",
    "CommonMetadata",
    "ExtensionNotImplemented",
    "ExtensionTypeError",
    "Extent",
    "HIERARCHICAL_LINKS",
    "DEFAULT_STAC_VERSION",
    "Item",
    "ItemAssetDefinition",
    "ItemCollection",
    "Link",
    "MediaType",
    "Provider",
    "from_dict",
    "ProviderRole",
    "STACError",
    "STACObject",
    "STACTypeError",
    "STACValidationError",
    "SpatialExtent",
    "TemporalExtent",
    "read_file",
]
