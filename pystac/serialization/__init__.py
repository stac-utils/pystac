# flake8: noqa
from pystac import (Catalog, Collection, ItemCollection, Item, Extensions)

from pystac.serialization.identify import (STACObjectType, STACJSONDescription, STACVersionRange,
                                           identify_stac_object, identify_stac_object_type)

from pystac.serialization.common_properties import merge_common_properties
from pystac.serialization.migrate import migrate_to_latest
from pystac.extensions.single_file_stac import SingleFileSTAC


def stac_object_from_dict(d, href=None, root=None):
    """Determines how to deserialize a dictionary into a STAC object.

    Args:
        d (dict): The dict to parse.
        href (str): Optional href that is the file location of the object being
            parsed.
        root (Catalog or Collection): Optional root of the catalog for this object.
            If provided, the root's resolved object cache can be used to search for
            previously resolved instances of the STAC object.

    Note: This is used internally in STAC_IO to deserialize STAC Objects.
    It is in the top level __init__ in order to avoid circular dependencies.
    """
    if identify_stac_object_type(d) == STACObjectType.ITEM:
        collection_cache = None
        if root is not None:
            collection_cache = root._resolved_objects.as_collection_cache()

        merge_common_properties(d, json_href=href, collection_cache=collection_cache)

    info = identify_stac_object(d)

    d, info = migrate_to_latest(d, info)

    if info.object_type == STACObjectType.CATALOG:
        return Catalog.from_dict(d, href=href, root=root)

    if info.object_type == STACObjectType.COLLECTION:
        return Collection.from_dict(d, href=href, root=root)

    if info.object_type == STACObjectType.ITEMCOLLECTION:
        if Extensions.SINGLE_FILE_STAC in info.common_extensions:
            return SingleFileSTAC.from_dict(d)

        return ItemCollection.from_dict(d)

    if info.object_type == STACObjectType.ITEM:
        return Item.from_dict(d, href=href, root=root)
