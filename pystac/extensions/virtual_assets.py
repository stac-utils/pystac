from __future__ import annotations

from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    TypeVar,
    Union,
)
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension
)
import pystac
S = TypeVar("S", bound=pystac.STACObject)

PREFIX = "virtual:"
HREFS_PROP = PREFIX + "hrefs"
SCHEMA_URI = "https://github.com/stac-extensions/virtual-assets/blob/main/json-schema/schema.json"

class VirtualAssetsExtension(
    PropertiesExtension, ExtensionManagementMixin[Union[pystac.Item, pystac.Collection]]
):
    """A class that can be used to extend the properties of a :class:`~pystac.Asset`
    with properties from the :stac-ext:`Virtual Assets Extension <virtual-assets>`.

    To create an instance of :class:`VirtualAssetsExtension`, use the
    :meth:`VirtualAssetsExtension.ext` method. For example:

    .. code-block:: python

       >>> asset: pystac.Asset = ...
       >>> virtual_assets_ext = VirtualAssetsExtension.ext(asset)
    """
    asset_href: str
    """The ``href`` value of the :class:`~pystac.Asset` being extended."""

    properties: Dict[str, Any]
    """The :class:`~pystac.Asset` fields, including extension properties."""

    additional_read_properties: Optional[Iterable[Dict[str, Any]]] = None
    """If present, this will be a list containing 1 dictionary representing the
    properties of the owning :class:`~pystac.Item`."""

    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return "<AssetVirtualAssetsExtension Asset href={}>".format(self.asset_href)
    
    def apply(
        self,
        hrefs: List[str]
    ) -> None:
        """Applies virtual assets extension properties to the extended Item.

        Args:
            hrefs : List of hrefs to virtual assets.
        """
        self.hrefs = hrefs

    @property
    def hrefs(self) -> List[str]:
        """Get or sets the hrefs of the virtual asset."""
        return self._get_property(HREFS_PROP, int)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    # TODO: remove this once extension is released.
    def has_extension(cls, obj: S) -> bool:
        """Check if the given object implements this extension by checking
        :attr:`pystac.STACObject.stac_extensions` for this extension's schema URI."""
        schema_uri = cls.get_schema_uri()

        return obj.stac_extensions is not None and any(
            uri == schema_uri for uri in obj.stac_extensions
        )    

    @classmethod
    def ext(cls, obj: pystac.Asset, add_if_missing: bool = False) -> VirtualAssetsExtension:
        """Extends the given STAC Object with properties from the :stac-ext:`Virtual Asset
        Extension <virtual-assets>`.

        This extension can be applied to instances of :class:`~pystac.Asset`.
        """
        if isinstance(obj, pystac.Asset):
            cls.validate_owner_has_extension(obj, add_if_missing)
            return cls(obj)
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))    