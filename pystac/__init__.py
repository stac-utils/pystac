"""
PySTAC is a library for working with SpatioTemporal Asset Catalogs (STACs)
"""

# flake8: noqa


class STACError(Exception):
    """A STACError is raised for errors relating to STAC, e.g. for
    invalid formats or trying to operate on a STAC that does not have
    the required information available.
    """
    pass


from pystac.version import (__version__, STAC_VERSION)
from pystac.stac_io import STAC_IO
from pystac.stac_object import STACObject
from pystac.media_type import MediaType
from pystac.link import (Link, LinkType)
from pystac.catalog import (Catalog, CatalogType)
from pystac.collection import (Collection, Extent, SpatialExtent,
                               TemporalExtent, Provider)
from pystac.item import (Item, Asset)
from pystac.item_collection import ItemCollection
from pystac.single_file_stac import SingleFileSTAC
from pystac.eo import *
from pystac.label import *

from pystac.serialization import (identify_stac_object, STACObjectType)


def _stac_object_from_dict(d, href=None, root=None):
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
    info = identify_stac_object(d)

    # TODO: Transorm older versions to newest version (pystac.serialization.migrate)

    if info.object_type == STACObjectType.CATALOG:
        return Catalog.from_dict(d, href=href, root=root)
    if info.object_type == STACObjectType.COLLECTION:
        return Collection.from_dict(d, href=href, root=root)
    if info.object_type == STACObjectType.ITEMCOLLECTION:
        if 'single-file-stac' in info.common_extensions:
            return SingleFileSTAC.from_dict(d, href=href, root=root)
        return ItemCollection.from_dict(d, href=href, root=root)
    if info.object_type == STACObjectType.ITEM:
        if 'eo' in info.common_extensions:
            return EOItem.from_dict(d, href=href, root=root)
        if 'label' in info.common_extensions:
            return LabelItem.from_dict(d, href=href, root=root)
        return Item.from_dict(d, href=href, root=root)


STAC_IO.stac_object_from_dict = _stac_object_from_dict
