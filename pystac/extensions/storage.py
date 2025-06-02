"""Implements the Storage Extension.

https://github.com/stac-extensions/storage
"""

from __future__ import annotations

from abc import ABC
from typing import (
    Any,
    Generic,
    Literal,
    TypeVar,
    cast,
)

import pystac
from pystac.errors import RequiredPropertyMissing
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import StringEnum, get_required, map_opt

#: Generalized version of :class:`~pystac.Item`, :class:`~pystac.Asset` or
#: :class:`~pystac.ItemAssetDefinition`
T = TypeVar("T", pystac.Item, pystac.Catalog, pystac.Collection)
U = TypeVar("U", pystac.Asset, pystac.Link, pystac.ItemAssetDefinition)

SCHEMA_URI: str = "https://stac-extensions.github.io/storage/v2.0.0/schema.json"
PREFIX: str = "storage:"

# Field names
REFS_PROP: str = PREFIX + "refs"
SCHEMES_PROP: str = PREFIX + "schemes"

# Storage scheme object names
TYPE_PROP: str = "type"
PLATFORM_PROP: str = "platform"
REGION_PROP: str = "region"
REQUESTER_PAYS_PROP: str = "requester_pays"


class StorageSchemeType(StringEnum):
    AWS_S3 = "aws-s3"
    CUSTOM_S3 = "custom-s3"
    AZURE = "ms-azure"


class StorageScheme:
    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]):
        super().__setattr__("properties", properties)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StorageScheme):
            raise NotImplementedError
        return self.properties == other.properties

    def __getattr__(self, name: str) -> Any:
        if name in self.properties:
            return self.properties[name]
        raise AttributeError(f"StorageScheme does not have attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self.properties[name] = value

    def apply(
        self,
        type: str,
        platform: str,
        region: str | None = None,
        requester_pays: bool | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        self.type = type
        self.platform = platform
        self.region = region
        self.requester_pays = requester_pays
        self.properties.update(kwargs)

    @classmethod
    def create(
        cls,
        type: str,
        platform: str,
        region: str | None = None,
        requester_pays: bool | None = None,
        **kwargs: dict[str, Any],
    ) -> StorageScheme:
        """Set the properties for a new StorageScheme object.

        Additional properties can be set through kwargs to fulfill
        any additional variables in a templated uri.

        Args:
            type (str): Type identifier for the platform.
            platform (str): The cloud provider where data is stored as URI or URI
                template to the API.
            region (str | None, optional): The region where the data is stored.
                Defaults to None.
            requester_pays (bool | None, optional): requester pays or data manager/cloud
                provider pays. Defaults to None.
            kwargs (dict[str | Any]): Additional properties to set on scheme

        Returns:
            StorageScheme: storage scheme
        """
        c = cls({})
        c.apply(
            type=type,
            platform=platform,
            region=region,
            requester_pays=requester_pays,
            **kwargs,
        )
        return c

    @property
    def type(self) -> str:
        """
        Get or set the required type property
        """
        return get_required(
            self.properties.get(TYPE_PROP),
            self,
            TYPE_PROP,
        )

    @type.setter
    def type(self, v: str) -> None:
        self.properties[TYPE_PROP] = v

    @property
    def platform(self) -> str:
        """
        Get or set the required platform property
        """
        return get_required(
            self.properties.get(PLATFORM_PROP),
            self,
            PLATFORM_PROP,
        )

    @platform.setter
    def platform(self, v: str) -> None:
        self.properties[PLATFORM_PROP] = v

    @property
    def region(self) -> str | None:
        """
        Get or set the optional region property
        """
        return self.properties.get(REGION_PROP)

    @region.setter
    def region(self, v: str) -> None:
        if v is not None:
            self.properties[REGION_PROP] = v
        else:
            self.properties.pop(REGION_PROP, None)

    @property
    def requester_pays(self) -> bool | None:
        """
        Get or set the optional requester_pays property
        """
        return self.properties.get(REQUESTER_PAYS_PROP)

    @requester_pays.setter
    def requester_pays(self, v: bool) -> None:
        if v is not None:
            self.properties[REQUESTER_PAYS_PROP] = v
        else:
            self.properties.pop(REQUESTER_PAYS_PROP, None)

    def to_dict(self) -> dict[str, Any]:
        """
        Returns the dictionary encoding of this object

        Returns:
            dict[str, Any
        """
        return self.properties


class _StorageExtension(ABC):
    name: Literal["storage"] = "storage"

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI


class StorageSchemesExtension(
    _StorageExtension,
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection | pystac.Catalog],
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Collection`, :class:`~pystac.Catalog`, or :class:`~pystac.Item`
    with properties from the :stac-ext:`Storage Extension <storage>`.
    This class is generic over the type of STAC Object to be extended (e.g.
    :class:`~pystac.Item`, :class:`~pystac.Collection`).

    To create a concrete instance of :class:`StorageExtension`, use the
    :meth:`StorageExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> storage_ext = StorageExtension.ext(item)
    """

    def apply(
        self,
        schemes: dict[str, StorageScheme],
    ) -> None:
        """Applies Storage Extension properties to the extended
        :class:`~pystac.Catalog`, :class:`~pystac.Collection`,
        or :class:`~pystac.Item`.

        Args:
            schemes (dict[str, StorageScheme]): Storage schemes used by Assets and Links
                in the STAC Item, Catalog or Collection.
        """
        self.schemes = schemes

    @property
    def schemes(self) -> dict[str, StorageScheme]:
        """Get or sets the schemes used by Assets and Links.

        Returns:
            dict[str, StorageScheme]: storage schemes
        """
        schemes: dict[str, dict[str, Any]] = get_required(
            self.properties.get(SCHEMES_PROP),
            self,
            SCHEMES_PROP,
        )
        return {k: StorageScheme(v) for k, v in schemes.items()}

    @schemes.setter
    def schemes(self, v: dict[str, StorageScheme]) -> None:
        v_trans = {k: c.to_dict() for k, c in v.items()}
        self._set_property(SCHEMES_PROP, v_trans)

    def add_scheme(self, key: str, scheme: StorageScheme) -> None:
        try:
            self.schemes = {**self.schemes, **{key: scheme}}
        except RequiredPropertyMissing:
            self.schemes = {key: scheme}

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> StorageSchemesExtension[T]:
        """Extends the given STAC Object with properties from the :stac-ext:`Storage
        Extension <storage>`.

        This extension can be applied to instances of :class:`~pystac.Catalog`,
        :class:`~pystac.Collection`, or :class:`~pystac.Item`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(StorageSchemesExtension[T], ItemStorageExtension(obj))
        elif isinstance(obj, pystac.Collection):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(StorageSchemesExtension[T], CollectionStorageExtension(obj))
        elif isinstance(obj, pystac.Catalog):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(StorageSchemesExtension[T], CatalogStorageExtension(obj))
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesStorageExtension:
        """Returns the extended summaries object for the given collection."""
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesStorageExtension(obj)


class ItemStorageExtension(StorageSchemesExtension[pystac.Item]):
    """A concrete implementation of :class:`StorageSchemesExtension` on an
    :class:`~pystac.Item` that extends the properties of the Item to include
    properties defined in the :stac-ext:`Storage Extension <storage>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`StorageSchemesExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: pystac.Item
    """The :class:`~pystac.Item` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Item` properties, including extension properties."""

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemStorageExtension Item id={self.item.id}>"


class CollectionStorageExtension(StorageSchemesExtension[pystac.Collection]):
    """A concrete implementation of :class:`StorageSchemesExtension` on an
    :class:`~pystac.Collection` that extends the properties of the Collection to include
    properties defined in the :stac-ext:`Storage Extension <storage>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`StorageSchemesExtension.ext` on an :class:`~pystac.Collection` to extend it.
    """

    collection: pystac.Collection
    """The :class:`~pystac.Collection` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Collection` properties, including extension properties."""

    def __init__(self, collection: pystac.Collection):
        self.collection = collection
        self.properties = collection.extra_fields

    def __repr__(self) -> str:
        return f"<CollectionStorageExtension Collection id={self.collection.id}>"


class CatalogStorageExtension(StorageSchemesExtension[pystac.Catalog]):
    """A concrete implementation of :class:`StorageSchemesExtension` on an
    :class:`~pystac.Catalog` that extends the properties of the Catalog to include
    properties defined in the :stac-ext:`Storage Extension <storage>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`StorageSchemesExtension.ext` on an :class:`~pystac.Catalog` to extend it.
    """

    catalog: pystac.Catalog
    """The :class:`~pystac.Catalog` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Catalog` properties, including extension properties."""

    def __init__(self, catalog: pystac.Catalog):
        self.catalog = catalog
        self.properties = catalog.extra_fields

    def __repr__(self) -> str:
        return f"<CatalogStorageExtension Collection id={self.catalog.id}>"


class StorageRefsExtension(
    _StorageExtension,
    Generic[U],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection | pystac.Catalog],
):
    def apply(
        self,
        refs: list[str],
    ) -> None:
        """Applies Storage Extension properties to the extended :class:`~pystac.Asset`,
        :class:`~pystac.Link`, or :class:`~pystac.ItemAssetDefinition`.

        Args:
            refs (list[str]): specifies which schemes in storage:schemes may be used to
                access an Asset or Link. Each value must be one of the keys defined in
                storage:schemes.
        """
        self.refs = refs

    @property
    def refs(self) -> list[str]:
        """Get or sets the keys of the schemes that may be used to access an Asset
            or Link.

        Returns:
            list[str]
        """
        return get_required(
            self.properties.get(REFS_PROP),
            self,
            REFS_PROP,
        )

    @refs.setter
    def refs(self, v: list[str]) -> None:
        self._set_property(REFS_PROP, v)

    def add_ref(self, ref: str) -> None:
        try:
            self.refs.append(ref)
        except RequiredPropertyMissing:
            self.refs = [ref]

    @classmethod
    def ext(cls, obj: U, add_if_missing: bool = False) -> StorageRefsExtension[U]:
        """Extends the given STAC Object with properties from the :stac-ext:`Storage
        Extension <storage>`.

        This extension can be applied to instances of :class:`~pystac.Item` or
        :class:`~pystac.Asset`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return AssetStorageExtension(obj)
        if isinstance(obj, pystac.Link):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return LinkStorageExtension(obj)
        if isinstance(obj, pystac.ItemAssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return ItemAssetsStorageExtension(obj)
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))


class AssetStorageExtension(StorageRefsExtension[pystac.Asset]):
    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return f"<AssetStorageExtension Asset href={self.asset_href}>"


class ItemAssetsStorageExtension(StorageRefsExtension[pystac.ItemAssetDefinition]):
    properties: dict[str, Any]
    asset_defn: pystac.ItemAssetDefinition

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        self.asset_defn = item_asset
        self.properties = item_asset.properties


class LinkStorageExtension(StorageRefsExtension[pystac.Link]):
    properties: dict[str, Any]
    link: pystac.Link

    def __init__(self, link: pystac.Link):
        self.link = link
        self.properties = link.extra_fields


class SummariesStorageExtension(SummariesExtension):
    """A concrete implementation of :class:`~pystac.extensions.base.SummariesExtension`
    that extends the ``summaries`` field of a :class:`~pystac.Collection` to include
    properties defined in the :stac-ext:`Storage Extension <storage>`.
    """

    @property
    def schemes(self) -> list[dict[str, StorageScheme]] | None:
        """Get or sets the summary of :attr:`StorageExtension.platform` values
        for this Collection.
        """
        v = map_opt(
            lambda schemes: [
                {k: StorageScheme(v) for k, v in x.items()} for x in schemes
            ],
            self.summaries.get_list(SCHEMES_PROP),
        )

        print(v)
        return v

    @schemes.setter
    def schemes(self, v: list[dict[str, StorageScheme]] | None) -> None:
        self._set_summary(
            SCHEMES_PROP,
            map_opt(
                lambda schemes: [
                    {k: c.to_dict() for k, c in x.items()} for x in schemes
                ],
                v,
            ),
        )


class StorageExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: set[str] = set()
    stac_object_types = {
        pystac.STACObjectType.CATALOG,
        pystac.STACObjectType.COLLECTION,
        pystac.STACObjectType.ITEM,
    }


STORAGE_EXTENSION_HOOKS: ExtensionHooks = StorageExtensionHooks()
