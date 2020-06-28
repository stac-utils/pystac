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
from pystac.extensions import Extensions
from pystac.stac_object import STACObject
from pystac.media_type import MediaType
from pystac.link import (Link, LinkType)
from pystac.catalog import (Catalog, CatalogType)
from pystac.collection import (Collection, Extent, SpatialExtent, TemporalExtent, Provider)
from pystac.item import (Item, Asset, CommonMetadata)
from pystac.item_collection import ItemCollection

from pystac.serialization import (STACObjectType, stac_object_from_dict)

STAC_IO.stac_object_from_dict = stac_object_from_dict

from pystac import extensions
import pystac.extensions.eo
import pystac.extensions.label

STAC_EXTENSIONS = extensions.base.EnabledSTACExtensions([
    extensions.eo.EO_EXTENSION_DEFINITION,
    extensions.label.LABEL_EXTENSION_DEFINITION
])
