"""
PySTAC is a library for working with SpatioTemporal Asset Catalogs (STACs)
"""

# flake8: noqa

from pystac.version import (__version__, STAC_VERSION)

class STACError(Exception):
    pass

from pystac.io import STAC_IO
from pystac.stac_object import STACObject
from pystac.link import (Link, LinkType)
from pystac.catalog import (Catalog, CatalogType)
from pystac.collection import (Collection, Extent, SpatialExtent, TemporalExtent, Provider)
from pystac.item import (Item, Asset)
from pystac.eo import *
from pystac.label import *

def stac_object_from_dict(d):
    """Determines how to deserialize a dictionary into a STAC object.

    Note: This is used internally in STAC_IO to deserialize STAC Objects.
    It is pl"""
    if 'type' in d:
        if 'label:description' in d['properties']:
            return LabelItem.from_dict(d)
        else:
            return Item.from_dict(d)
    elif 'extent' in d:
        return Collection.from_dict(d)
    else:
        return Catalog.from_dict(d)

STAC_IO.stac_object_from_dict = stac_object_from_dict
