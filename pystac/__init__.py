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


from pystac.version import (__version__, get_stac_version, set_stac_version)
from pystac.stac_io import STAC_IO
from pystac.extensions import Extensions
from pystac.stac_object import (STACObject, STACObjectType)
from pystac.media_type import MediaType
from pystac.link import (Link, LinkType)
from pystac.catalog import (Catalog, CatalogType)
from pystac.collection import (Collection, Extent, SpatialExtent, TemporalExtent, Provider)
from pystac.item import (Item, Asset, CommonMetadata)

from pystac.serialization import stac_object_from_dict

import pystac.validation

STAC_IO.stac_object_from_dict = stac_object_from_dict

from pystac import extensions
import pystac.extensions.eo
import pystac.extensions.label
import pystac.extensions.pointcloud
import pystac.extensions.projection
import pystac.extensions.sar
import pystac.extensions.sat
import pystac.extensions.scientific
import pystac.extensions.single_file_stac
import pystac.extensions.timestamps
import pystac.extensions.version
import pystac.extensions.view

STAC_EXTENSIONS = extensions.base.RegisteredSTACExtensions([
    extensions.eo.EO_EXTENSION_DEFINITION, extensions.label.LABEL_EXTENSION_DEFINITION,
    extensions.pointcloud.POINTCLOUD_EXTENSION_DEFINITION,
    extensions.projection.PROJECTION_EXTENSION_DEFINITION, extensions.sar.SAR_EXTENSION_DEFINITION,
    extensions.sat.SAT_EXTENSION_DEFINITION, extensions.scientific.SCIENTIFIC_EXTENSION_DEFINITION,
    extensions.single_file_stac.SFS_EXTENSION_DEFINITION,
    extensions.timestamps.TIMESTAMPS_EXTENSION_DEFINITION,
    extensions.version.VERSION_EXTENSION_DEFINITION, extensions.view.VIEW_EXTENSION_DEFINITION
])


def read_file(href):
    """Reads a STAC object from a file.

    This method will return either a Catalog, a Collection, or an Item based on what the
    file contains.

    This is a convenience method for :meth:`STACObject.from_file <pystac.STACObject.from_file>`

    Args:
        href (str): The HREF to read the object from.

    Returns:
        The specific STACObject implementation class that is represented
        by the JSON read from the file located at HREF.
    """
    return STACObject.from_file(href)


def write_file(obj, include_self_link=True, dest_href=None):
    """Writes a STACObject to a file.

    This will write only the Catalog, Collection or Item ``obj``. It will not attempt
    to write any other objects that are linked to ``obj``; if you'd like functionality to
    save off catalogs recursively see :meth:`Catalog.save <pystac.Catalog.save>`.

    This method will write the JSON of the object to the object's assigned "self" link or
    to the dest_href if provided. To set the self link, see :meth:`STACObject.set_self_href
    <pystac.STACObject.set_self_href>`.

    Convenience method for :meth:`STACObject.from_file <pystac.STACObject.from_file>`

    Args:
        obj (STACObject): The STACObject to save.
        include_self_link (bool): If this is true, include the 'self' link with this object.
            Otherwise, leave out the self link.
        dest_href (str): Optional HREF to save the file to. If None, the object will be saved
            to the object's self href.
    """
    obj.save_object(include_self_link=include_self_link, dest_href=dest_href)


def read_dict(d, href=None, root=None):
    """Reads a STAC object from a dict representing the serialized JSON version of the
    STAC object.

    This method will return either a Catalog, a Collection, or an Item based on what the
    dict contains.

    This is a convenience method for :meth:`pystac.serialization.stac_object_from_dict`

    Args:
        d (dict): The dict to parse.
        href (str): Optional href that is the file location of the object being
            parsed.
        root (Catalog or Collection): Optional root of the catalog for this object.
            If provided, the root's resolved object cache can be used to search for
            previously resolved instances of the STAC object.
    """
    return stac_object_from_dict(d, href, root)
