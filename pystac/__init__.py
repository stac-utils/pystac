"""
PySTAC is a library for working with SpatioTemporal Asset Catalogs (STACs)
"""

# flake8: noqa
from pystac.errors import (
    STACError,  # type:ignore
    STACTypeError,  # type:ignore
    ExtensionAlreadyExistsError,  # type:ignore
    ExtensionTypeError,  # type:ignore
    RequiredPropertyMissing,  # type:ignore
    STACValidationError,  #  type:ignore
)

from typing import Any, Dict, Optional
from pystac.version import (
    __version__,
    get_stac_version,  # type:ignore
    set_stac_version,  # type:ignore
)
from pystac.stac_io import StacIO  # type:ignore
from pystac.stac_object import STACObject, STACObjectType  # type:ignore
from pystac.media_type import MediaType  # type:ignore
from pystac.link import Link, HIERARCHICAL_LINKS  # type:ignore
from pystac.catalog import Catalog, CatalogType  # type:ignore
from pystac.collection import (
    Collection,  # type:ignore
    Extent,  # type:ignore
    SpatialExtent,  # type:ignore
    TemporalExtent,  # type:ignore
    Provider,  # type:ignore
    Summaries,  # type:ignore
    RangeSummary,  # type:ignore
)
from pystac.item import Item, Asset, CommonMetadata  # type:ignore

import pystac.validation

import pystac.extensions.hooks
import pystac.extensions.datacube
import pystac.extensions.eo
import pystac.extensions.file
import pystac.extensions.item_assets
import pystac.extensions.label
import pystac.extensions.pointcloud
import pystac.extensions.projection
import pystac.extensions.sar
import pystac.extensions.sat
import pystac.extensions.scientific
import pystac.extensions.timestamps
import pystac.extensions.version
import pystac.extensions.view

EXTENSION_HOOKS = pystac.extensions.hooks.RegisteredExtensionHooks(
    [
        pystac.extensions.datacube.DATACUBE_EXTENSION_HOOKS,
        pystac.extensions.eo.EO_EXTENSION_HOOKS,
        pystac.extensions.file.FILE_EXTENSION_HOOKS,
        pystac.extensions.item_assets.ITEM_ASSETS_EXTENSION_HOOKS,
        pystac.extensions.label.LABEL_EXTENSION_HOOKS,
        pystac.extensions.pointcloud.POINTCLOUD_EXTENSION_HOOKS,
        pystac.extensions.projection.PROJECTION_EXTENSION_HOOKS,
        pystac.extensions.sar.SAR_EXTENSION_HOOKS,
        pystac.extensions.sat.SAT_EXTENSION_HOOKS,
        pystac.extensions.scientific.SCIENTIFIC_EXTENSION_HOOKS,
        pystac.extensions.timestamps.TIMESTAMPS_EXTENSION_HOOKS,
        pystac.extensions.version.VERSION_EXTENSION_HOOKS,
        pystac.extensions.view.VIEW_EXTENSION_HOOKS,
    ]
)


def read_file(href: str) -> STACObject:
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


def write_file(
    obj: STACObject, include_self_link: bool = True, dest_href: Optional[str] = None
) -> None:
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


def read_dict(
    d: Dict[str, Any],
    href: Optional[str] = None,
    root: Optional[Catalog] = None,
    stac_io: Optional[StacIO] = None,
) -> STACObject:
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
        stac_io: Optional StacIO instance to use for reading. If None, the
            default instance will be used.
    """
    if stac_io is None:
        stac_io = StacIO.default()
    return stac_io.stac_object_from_dict(d, href, root)
