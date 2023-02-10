"""Implements the Storage Extension.

https://github.com/stac-extensions/storage
"""

from __future__ import annotations

from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Set,
    TypeVar,
    Union,
    cast,
)

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import StringEnum

T = TypeVar("T", pystac.Item, pystac.Asset)

SCHEMA_URI: str = "https://stac-extensions.github.io/storage/v1.0.0/schema.json"
PREFIX: str = "storage:"

# Field names
PLATFORM_PROP: str = PREFIX + "platform"
REGION_PROP: str = PREFIX + "region"
REQUESTER_PAYS_PROP: str = PREFIX + "requester_pays"
TIER_PROP: str = PREFIX + "tier"


class CloudPlatform(StringEnum):
    ALIBABA = "ALIBABA"
    AWS = "AWS"
    AZURE = "AZURE"
    GCP = "GCP"
    IBM = "IBM"
    ORACLE = "ORACLE"
    OTHER = "OTHER"


class StorageExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Union[pystac.Item, pystac.Collection]],
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Item` or :class:`~pystac.Asset` with properties from the
    :stac-ext:`Storage Extension <storage>`. This class is generic over the type of
    STAC Object to be extended (e.g. :class:`~pystac.Item`,
    :class:`~pystac.Asset`).

    To create a concrete instance of :class:`StorageExtension`, use the
    :meth:`StorageExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> storage_ext = StorageExtension.ext(item)
    """

    def apply(
        self,
        platform: Optional[CloudPlatform] = None,
        region: Optional[str] = None,
        requester_pays: Optional[bool] = None,
        tier: Optional[str] = None,
    ) -> None:
        """Applies Storage Extension properties to the extended :class:`~pystac.Item` or
        :class:`~pystac.Asset`.

        Args:
            platform (str, CloudProvider) : The cloud provider where data is stored.
            region (str) : The region where the data is stored. Relevant to speed of
                access and inter-region egress costs (as defined by PaaS provider).
            requester_pays (bool) : Is the data requester pays or is it data
                manager/cloud provider pays.
            tier (str) : The title for the tier type (as defined by PaaS provider).
        """
        self.platform = platform
        self.region = region
        self.requester_pays = requester_pays
        self.tier = tier

    @property
    def platform(self) -> Optional[CloudPlatform]:
        """Get or sets the cloud provider where data is stored.

        Returns:
            str or None
        """
        return self._get_property(PLATFORM_PROP, CloudPlatform)

    @platform.setter
    def platform(self, v: Optional[CloudPlatform]) -> None:
        self._set_property(PLATFORM_PROP, v)

    @property
    def region(self) -> Optional[str]:
        """Gets or sets the region where the data is stored. Relevant to speed of
        access and inter-region egress costs (as defined by PaaS provider)."""
        return self._get_property(REGION_PROP, str)

    @region.setter
    def region(self, v: Optional[str]) -> None:
        self._set_property(REGION_PROP, v)

    @property
    def requester_pays(self) -> Optional[bool]:
        # This value "defaults to false", according to the extension spec.
        return self._get_property(REQUESTER_PAYS_PROP, bool)

    @requester_pays.setter
    def requester_pays(self, v: Optional[bool]) -> None:
        self._set_property(REQUESTER_PAYS_PROP, v)

    @property
    def tier(self) -> Optional[str]:
        return self._get_property(TIER_PROP, str)

    @tier.setter
    def tier(self, v: Optional[str]) -> None:
        self._set_property(TIER_PROP, v)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> StorageExtension[T]:
        """Extends the given STAC Object with properties from the :stac-ext:`Storage
        Extension <storage>`.

        This extension can be applied to instances of :class:`~pystac.Item` or
        :class:`~pystac.Asset`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Item):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(StorageExtension[T], ItemStorageExtension(obj))
        elif isinstance(obj, pystac.Asset):
            cls.validate_owner_has_extension(obj, add_if_missing)
            return cast(StorageExtension[T], AssetStorageExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"StorageExtension does not apply to type '{type(obj).__name__}'"
            )

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesStorageExtension:
        """Returns the extended summaries object for the given collection."""
        cls.validate_has_extension(obj, add_if_missing)
        return SummariesStorageExtension(obj)


class ItemStorageExtension(StorageExtension[pystac.Item]):
    """A concrete implementation of :class:`StorageExtension` on an
    :class:`~pystac.Item` that extends the properties of the Item to include
    properties defined in the :stac-ext:`Storage Extension <storage>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`StorageExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: pystac.Item
    """The :class:`~pystac.Item` being extended."""

    properties: Dict[str, Any]
    """The :class:`~pystac.Item` properties, including extension properties."""

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return "<ItemStorageExtension Item id={}>".format(self.item.id)


class AssetStorageExtension(StorageExtension[pystac.Asset]):
    """A concrete implementation of :class:`StorageExtension` on an
    :class:`~pystac.Asset` that extends the Asset fields to include properties defined
    in the :stac-ext:`Storage Extension <storage>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`StorageExtension.ext` on an :class:`~pystac.Asset` to extend it.
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
        return "<AssetStorageExtension Asset href={}>".format(self.asset_href)


class SummariesStorageExtension(SummariesExtension):
    """A concrete implementation of :class:`~SummariesExtension` that extends
    the ``summaries`` field of a :class:`~pystac.Collection` to include properties
    defined in the :stac-ext:`Storage Extension <storage>`.
    """

    @property
    def platform(self) -> Optional[List[CloudPlatform]]:
        """Get or sets the summary of :attr:`StorageExtension.platform` values
        for this Collection.
        """
        return self.summaries.get_list(PLATFORM_PROP)

    @platform.setter
    def platform(self, v: Optional[List[CloudPlatform]]) -> None:
        self._set_summary(PLATFORM_PROP, v)

    @property
    def region(self) -> Optional[List[str]]:
        """Get or sets the summary of :attr:`StorageExtension.region` values
        for this Collection.
        """
        return self.summaries.get_list(REGION_PROP)

    @region.setter
    def region(self, v: Optional[List[str]]) -> None:
        self._set_summary(REGION_PROP, v)

    @property
    def requester_pays(self) -> Optional[List[bool]]:
        """Get or sets the summary of :attr:`StorageExtension.requester_pays` values
        for this Collection.
        """
        return self.summaries.get_list(REQUESTER_PAYS_PROP)

    @requester_pays.setter
    def requester_pays(self, v: Optional[List[bool]]) -> None:
        self._set_summary(REQUESTER_PAYS_PROP, v)

    @property
    def tier(self) -> Optional[List[str]]:
        """Get or sets the summary of :attr:`StorageExtension.tier` values
        for this Collection.
        """
        return self.summaries.get_list(TIER_PROP)

    @tier.setter
    def tier(self, v: Optional[List[str]]) -> None:
        self._set_summary(TIER_PROP, v)


class StorageExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: Set[str] = set()
    stac_object_types = {
        pystac.STACObjectType.COLLECTION,
        pystac.STACObjectType.ITEM,
    }


STORAGE_EXTENSION_HOOKS: ExtensionHooks = StorageExtensionHooks()
