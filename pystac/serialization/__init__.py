# flake8: noqa
from typing import Any, Dict, Optional, TYPE_CHECKING

import pystac
from pystac.serialization.identify import (
    STACVersionRange,  # type:ignore
    identify_stac_object,
    identify_stac_object_type,
)
from pystac.serialization.common_properties import merge_common_properties
from pystac.serialization.migrate import migrate_to_latest

if TYPE_CHECKING:
    from pystac.stac_object import STACObject
    from pystac.catalog import Catalog


def stac_object_from_dict(
    d: Dict[str, Any], href: Optional[str] = None, root: Optional["Catalog"] = None
) -> "STACObject":
    """Determines how to deserialize a dictionary into a STAC object.

    Args:
        d (dict): The dict to parse.
        href (str): Optional href that is the file location of the object being
            parsed.
        root (Catalog or Collection): Optional root of the catalog for this object.
            If provided, the root's resolved object cache can be used to search for
            previously resolved instances of the STAC object.

    Note: This is used internally in StacIO instances to deserialize STAC Objects.
    """
    if identify_stac_object_type(d) == pystac.STACObjectType.ITEM:
        collection_cache = None
        if root is not None:
            collection_cache = root._resolved_objects.as_collection_cache()

        # Merge common properties in case this is an older STAC object.
        merge_common_properties(d, json_href=href, collection_cache=collection_cache)

    info = identify_stac_object(d)

    d = migrate_to_latest(d, info)

    if info.object_type == pystac.STACObjectType.CATALOG:
        return pystac.Catalog.from_dict(d, href=href, root=root, migrate=False)

    if info.object_type == pystac.STACObjectType.COLLECTION:
        return pystac.Collection.from_dict(d, href=href, root=root, migrate=False)

    if info.object_type == pystac.STACObjectType.ITEM:
        return pystac.Item.from_dict(d, href=href, root=root, migrate=False)

    raise ValueError(f"Unknown STAC object type {info.object_type}")
