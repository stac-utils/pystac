# isort: skip_file
"""
PySTAC is a library for working with SpatioTemporal Asset Catalogs (STACs)
"""

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

__all__ = [
    "__version__",
    "TemplateError",
    "STACError",
    "STACTypeError",
    "DuplicateObjectKeyError",
    "ExtensionAlreadyExistsError",
    "ExtensionNotImplemented",
    "ExtensionTypeError",
    "RequiredPropertyMissing",
    "STACValidationError",
    "DeprecatedWarning",
    "MediaType",
    "RelType",
    "StacIO",
    "STACObject",
    "STACObjectType",
    "Link",
    "HIERARCHICAL_LINKS",
    "Catalog",
    "CatalogType",
    "Collection",
    "Extent",
    "SpatialExtent",
    "TemporalExtent",
    "Summaries",
    "CommonMetadata",
    "NoDataStrings",
    "DataType",
    "RangeSummary",
    "Item",
    "Asset",
    "ItemAssetDefinition",
    "ItemCollection",
    "Provider",
    "ProviderRole",
    "read_file",
    "read_dict",
    "write_file",
    "get_stac_version",
    "set_stac_version",
]

from typing import Any

from pystac.errors import (
    TemplateError,
    STACError,
    STACTypeError,
    DuplicateObjectKeyError,
    ExtensionAlreadyExistsError,
    ExtensionNotImplemented,
    ExtensionTypeError,
    RequiredPropertyMissing,
    STACValidationError,
    DeprecatedWarning,
)

from pystac.version import (
    __version__,
    get_stac_version,
    set_stac_version,
)
from pystac.media_type import MediaType
from pystac.rel_type import RelType
from pystac.stac_io import StacIO
from pystac.stac_object import STACObject, STACObjectType
from pystac.link import Link, HIERARCHICAL_LINKS
from pystac.catalog import Catalog, CatalogType
from pystac.collection import (
    Collection,
    Extent,
    SpatialExtent,
    TemporalExtent,
)
from pystac.common_metadata import CommonMetadata, NoDataStrings, DataType
from pystac.summaries import RangeSummary, Summaries
from pystac.asset import Asset
from pystac.item import Item
from pystac.item_assets import ItemAssetDefinition
from pystac.item_collection import ItemCollection
from pystac.provider import ProviderRole, Provider
from pystac.utils import HREF

import pystac.extensions.hooks

#: Extension migration/link hooks, discovered lazily from installed extension
#: packages via the ``pystac.extensions`` entry point group. ``pystac-core``
#: intentionally has no compile-time knowledge of any extension.
EXTENSION_HOOKS = pystac.extensions.hooks.RegisteredExtensionHooks()


def read_file(href: HREF, stac_io: StacIO | None = None) -> STACObject:
    """Reads a STAC object from a file.

    This method will return either a Catalog, a Collection, or an Item based on what
    the file contains.

    This is a convenience method for :meth:`StacIO.read_stac_object
    <pystac.StacIO.read_stac_object>`

    Args:
        href : The HREF to read the object from.
        stac_io: Optional :class:`~StacIO` instance to use for I/O operations. If not
            provided, will use :meth:`StacIO.default` to create an instance.

    Returns:
        The specific STACObject implementation class that is represented
        by the JSON read from the file located at HREF.

    Raises:
        STACTypeError : If the file at ``href`` does not represent a valid
            :class:`~pystac.STACObject`. Note that an :class:`~pystac.ItemCollection`
            is not a :class:`~pystac.STACObject` and must be read using
            :meth:`ItemCollection.from_file <pystac.ItemCollection.from_file>`
    """
    if stac_io is None:
        stac_io = StacIO.default()
    return stac_io.read_stac_object(href)


def write_file(
    obj: STACObject,
    include_self_link: bool = True,
    dest_href: HREF | None = None,
    stac_io: StacIO | None = None,
) -> None:
    """Writes a STACObject to a file.

    This will write only the Catalog, Collection or Item ``obj``. It will not attempt
    to write any other objects that are linked to ``obj``; if you'd like functionality
    to save off catalogs recursively see :meth:`Catalog.save <pystac.Catalog.save>`.

    This method will write the JSON of the object to the object's assigned "self" link
    or to the dest_href if provided. To set the self link, see
    :meth:`STACObject.set_self_href <pystac.STACObject.set_self_href>`.

    Convenience method for :meth:`STACObject.from_file <pystac.STACObject.from_file>`

    Args:
        obj : The STACObject to save.
        include_self_link : If ``True``, include the ``"self"`` link with this object.
            Otherwise, leave out the self link.
        dest_href : Optional HREF to save the file to. If ``None``, the object will be
            saved to the object's ``"self"`` href.
        stac_io: Optional :class:`~StacIO` instance to use for I/O operations. If not
            provided, will use :meth:`StacIO.default` to create an instance.
    """
    if stac_io is None:
        stac_io = StacIO.default()
    import os

    dest_href = None if dest_href is None else str(os.fspath(dest_href))
    obj.save_object(
        include_self_link=include_self_link, dest_href=dest_href, stac_io=stac_io
    )


def read_dict(
    d: dict[str, Any],
    href: str | None = None,
    root: Catalog | None = None,
    stac_io: StacIO | None = None,
) -> STACObject:
    """Reads a :class:`~STACObject` or :class:`~ItemCollection` from a JSON-like dict
    representing a serialized STAC object.

    This method will return either a :class:`~Catalog`, :class:`~Collection`,
    or :class`~Item` based on the contents of the dict.

    This is a convenience method for either
    :meth:`StacIO.stac_object_from_dict <pystac.StacIO.stac_object_from_dict>`.

    Args:
        d : The dict to parse.
        href : Optional href that is the file location of the object being
            parsed.
        root : Optional root of the catalog for this object.
            If provided, the root's resolved object cache can be used to search for
            previously resolved instances of the STAC object.
        stac_io: Optional :class:`~StacIO` instance to use for reading. If ``None``,
            the default instance will be used.

    Raises:
        STACTypeError : If the ``d`` dictionary does not represent a valid
            :class:`~pystac.STACObject`. Note that an :class:`~pystac.ItemCollection`
            is not a :class:`~pystac.STACObject` and must be read using
            :meth:`ItemCollection.from_dict <pystac.ItemCollection.from_dict>`
    """
    if stac_io is None:
        stac_io = StacIO.default()
    return stac_io.stac_object_from_dict(d, href, root)


def __getattr__(name: str) -> Any:
    if name == "validation":
        import warnings
        import pystac.validation

        warnings.warn(
            "pystac.validation will not be automatically imported to the package in "
            "pystac v2.0. Instead, import it directly: `import pystac.validation`",
            DeprecationWarning,
            stacklevel=2,
        )
        return pystac.validation
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
