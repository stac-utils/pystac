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
    extensions = d.get('stac_extensions', [])
    if 'type' in d:
        if d['type'] == 'FeatureCollection':
            # Dealing with an Item Collection
            if 'collections' in d:
                return SingleFileSTAC.from_dict(d, href=href, root=root)
            else:
                return ItemCollection.from_dict(d, href=href, root=root)
        else:
            # Dealing with an Item
            if 'eo' in extensions or \
               any([k for k in d['properties'].keys() if k.startswith('eo:')]):
                return EOItem.from_dict(d, href=href, root=root)
            elif 'label' in extensions or \
                 any([k for k in d['properties'].keys() if k.startswith('label:')]):
                return LabelItem.from_dict(d, href=href, root=root)
            else:
                return Item.from_dict(d, href=href, root=root)
    elif 'extent' in d:
        return Collection.from_dict(d, href=href, root=root)
    else:
        return Catalog.from_dict(d, href=href, root=root)


STAC_IO.stac_object_from_dict = _stac_object_from_dict
