"""Implements the Storage Extension.

https://github.com/stac-extensions/storage
"""

from __future__ import annotations

import warnings
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
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.utils import StringEnum, get_required, map_opt

#: Generalized version of :class:`~pystac.Catalog`, :class:`~pystac.Collection`,
#: :class:`~pystac.Item`, :class:`~pystac.Asset`, :class:`~pystac.Link`,
#: or :class:`~pystac.ItemAssetDefinition`
T = TypeVar(
    "T",
    pystac.Catalog,
    pystac.Collection,
    pystac.Item,
    pystac.Asset,
    pystac.Link,
    pystac.ItemAssetDefinition,
)

SCHEMA_URI_PATTERN: str = (
    "https://stac-extensions.github.io/storage/v{version}/schema.json"
)
DEFAULT_VERSION: str = "2.0.0"
SUPPORTED_VERSIONS: list[str] = ["2.0.0", "1.0.0"]

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
    """
    Helper class for storage scheme objects.

    Can set well-defined properties, or if needed,
    any arbitrary property.
    """

    _known_fields = {"type", "platform", "region", "requester_pays"}
    _properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]):
        super().__setattr__("_properties", properties)

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(type(self), name):
            object.__setattr__(self, name, value)
            return

        if name in self._known_fields:
            prop = getattr(type(self), name)
            prop.fset(self, value)
            return

        props = object.__getattribute__(self, "_properties")
        props[name] = value

    def __getattr__(self, name: str) -> Any:
        props = object.__getattribute__(self, "_properties")

        if name in props:
            return props[name]

        raise AttributeError(name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StorageScheme):
            return NotImplemented
        return bool(self._properties == other._properties)

    def __repr__(self) -> str:
        return f"<StorageScheme platform={self.platform}>"

    def apply(
        self,
        type: str,
        platform: str,
        region: str | None = None,
        requester_pays: bool | None = None,
        **kwargs: Any,
    ) -> None:
        self.type = type
        self.platform = platform
        self.region = region
        self.requester_pays = requester_pays
        self._properties.update(kwargs)

    @classmethod
    def create(
        cls,
        type: str,
        platform: str,
        region: str | None = None,
        requester_pays: bool | None = None,
        **kwargs: Any,
    ) -> StorageScheme:
        """Set the properties for a new StorageScheme object.

        Additional properties can be set through kwargs to fulfill
        any additional variables in a templated uri.

        Args:
            type (str): Type identifier for the platform.
            platform (str): The cloud provider where data is stored as URI or URI
                template to the API.
            region (str | None): The region where the data is stored.
                Defaults to None.
            requester_pays (bool | None): requester pays or data manager/cloud
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
        return cast(
            str,
            get_required(
                self._properties.get(TYPE_PROP),
                self,
                TYPE_PROP,
            ),
        )

    @type.setter
    def type(self, v: str) -> None:
        self._properties[TYPE_PROP] = v

    @property
    def platform(self) -> str:
        """
        Get or set the required platform property
        """
        return cast(
            str,
            get_required(
                self._properties.get(PLATFORM_PROP),
                self,
                PLATFORM_PROP,
            ),
        )

    @platform.setter
    def platform(self, v: str) -> None:
        self._properties[PLATFORM_PROP] = v

    @property
    def region(self) -> str | None:
        """
        Get or set the optional region property
        """
        return self._properties.get(REGION_PROP)

    @region.setter
    def region(self, v: str | None) -> None:
        if v is not None:
            self._properties[REGION_PROP] = v
        else:
            self._properties.pop(REGION_PROP, None)

    @property
    def requester_pays(self) -> bool | None:
        """
        Get or set the optional requester_pays property
        """
        return self._properties.get(REQUESTER_PAYS_PROP)

    @requester_pays.setter
    def requester_pays(self, v: bool | None) -> None:
        if v is not None:
            self._properties[REQUESTER_PAYS_PROP] = v
        else:
            self._properties.pop(REQUESTER_PAYS_PROP, None)

    def to_dict(self) -> dict[str, Any]:
        """
        Returns the dictionary encoding of this object

        Returns:
            dict[str, Any]: The dictionary encoding of this object
        """
        return self._properties


class StorageExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection | pystac.Catalog],
):
    """An class that can be used to extend the properties of an
    :class:`~pystac.Catalog`, :class:`~pystac.Collection`, :class:`~pystac.Item`,
    :class:`~pystac.Asset`, :class:`~pystac.Link`, or
    :class:`~pystac.ItemAssetDefinition` with properties from the
    :stac-ext:`Storage Extension <storage>`.
    This class is generic over the type of STAC Object to be extended (e.g.
    :class:`~pystac.Item`, :class:`~pystac.Collection`).
    To create a concrete instance of :class:`StorageExtension`, use the
    :meth:`StorageExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> storage_ext = StorageExtension.ext(item)
    """

    name: Literal["storage"] = "storage"

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI_PATTERN.format(version=DEFAULT_VERSION)

    # For type checking purposes only, these methods are overridden in mixins
    def apply(
        self,
        *,
        schemes: dict[str, StorageScheme] | None = None,
        refs: list[str] | None = None,
    ) -> None:
        raise NotImplementedError()

    @property
    def schemes(self) -> dict[str, StorageScheme]:
        raise NotImplementedError()

    @schemes.setter
    def schemes(self, v: dict[str, StorageScheme]) -> None:
        raise NotImplementedError()

    def add_scheme(self, key: str, scheme: StorageScheme) -> None:
        raise NotImplementedError()

    @property
    def refs(self) -> list[str]:
        raise NotImplementedError()

    @refs.setter
    def refs(self, v: list[str]) -> None:
        raise NotImplementedError()

    def add_ref(self, ref: str) -> None:
        raise NotImplementedError()

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> StorageExtension[T]:
        """Extends the given STAC Object with properties from the :stac-ext:`Storage
        Extension <storage>`.

        This extension can be applied to instances of :class:`~pystac.Catalog`,
        :class:`~pystac.Collection`, :class:`~pystac.Item`, :class:`~pystac.Asset`,
        :class:`~pystac.Link`, or :class:`~pystac.ItemAssetDefinition`.

        Raises:
            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(StorageExtension[T], ItemStorageExtension(obj))

        elif isinstance(obj, pystac.Collection):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(StorageExtension[T], CollectionStorageExtension(obj))

        elif isinstance(obj, pystac.Catalog):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(StorageExtension[T], CatalogStorageExtension(obj))

        elif isinstance(obj, pystac.Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(StorageExtension[T], AssetStorageExtension(obj))

        elif isinstance(obj, pystac.Link):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(StorageExtension[T], LinkStorageExtension(obj))

        elif isinstance(obj, pystac.ItemAssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(StorageExtension[T], ItemAssetsStorageExtension(obj))

        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesStorageExtension:
        """Returns the extended summaries object for the given collection."""
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesStorageExtension(obj)


class _SchemesMixin:
    """Mixin for objects that support Storage Schemes (Items, Collections, Catalogs)."""

    properties: dict[str, Any]
    _set_property: Any

    def apply(
        self,
        *,
        schemes: dict[str, StorageScheme] | None = None,
        refs: list[str] | None = None,
    ) -> None:
        if refs is not None:
            raise ValueError("'refs' cannot be applied with this STAC object type.")
        if schemes is None:
            raise RequiredPropertyMissing(
                self,
                SCHEMES_PROP,
                "'schemes' property is required for this object type.",
            )
        self.schemes = schemes

    @property
    def schemes(self) -> dict[str, StorageScheme]:
        schemes_dict: dict[str, Any] = get_required(
            self.properties.get(SCHEMES_PROP), self, SCHEMES_PROP
        )
        return {k: StorageScheme(v) for k, v in schemes_dict.items()}

    @schemes.setter
    def schemes(self, v: dict[str, StorageScheme]) -> None:
        v_trans = {k: c.to_dict() for k, c in v.items()}
        self._set_property(SCHEMES_PROP, v_trans)

    def add_scheme(self, key: str, scheme: StorageScheme) -> None:
        current = self.properties.get(SCHEMES_PROP, {})
        current[key] = scheme.to_dict()
        self._set_property(SCHEMES_PROP, current)


class _RefsMixin:
    """Mixin for objects that support Storage Refs (Assets, Links)."""

    properties: dict[str, Any]
    _set_property: Any

    def apply(
        self,
        *,
        schemes: dict[str, StorageScheme] | None = None,
        refs: list[str] | None = None,
    ) -> None:
        if schemes is not None:
            raise ValueError("'schemes' cannot be applied with this STAC object type.")
        if refs is None:
            raise RequiredPropertyMissing(
                self, REFS_PROP, "'refs' property is required for this object type."
            )
        self.refs = refs

    @property
    def refs(self) -> list[str]:
        return get_required(self.properties.get(REFS_PROP), self, REFS_PROP)

    @refs.setter
    def refs(self, v: list[str]) -> None:
        self._set_property(REFS_PROP, v)

    def add_ref(self, ref: str) -> None:
        try:
            current = self.refs
            if ref not in current:
                current.append(ref)
                self.refs = current
        except RequiredPropertyMissing:
            self.refs = [ref]


class ItemStorageExtension(_SchemesMixin, StorageExtension[pystac.Item]):
    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemStorageExtension Item id={self.item.id}>"


class CatalogStorageExtension(_SchemesMixin, StorageExtension[pystac.Catalog]):
    """A concrete implementation of :class:`StorageExtension` on an
    :class:`~pystac.Catalog` that extends the properties of the Catalog to include
    properties defined in the :stac-ext:`Storage Extension <storage>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`StorageExtension.ext` on an :class:`~pystac.Catalog` to extend it.
    """

    catalog: pystac.Catalog
    """The :class:`~pystac.Catalog` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Catalog` properties, including extension properties."""

    def __init__(self, catalog: pystac.Catalog):
        self.catalog = catalog
        self.properties = catalog.extra_fields

    def __repr__(self) -> str:
        return f"<CatalogStorageExtension Catalog id={self.catalog.id}>"


class CollectionStorageExtension(_SchemesMixin, StorageExtension[pystac.Collection]):
    """A concrete implementation of :class:`StorageExtension` on an
    :class:`~pystac.Collection` that extends the properties of the Collection to include
    properties defined in the :stac-ext:`Storage Extension <storage>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`StorageExtension.ext` on an :class:`~pystac.Collection` to extend it.
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


class AssetStorageExtension(_RefsMixin, StorageExtension[pystac.Asset]):
    """A concrete implementation of :class:`StorageExtension` on an
    :class:`~pystac.Asset` that extends the properties of the Asset to include
    properties defined in the :stac-ext:`Storage Extension <storage>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`StorageExtension.ext` on an :class:`~pystac.Asset` to extend it.
    """

    asset: pystac.Asset
    """The :class:`~pystac.Asset` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Asset` properties, including extension properties."""

    def __init__(self, asset: pystac.Asset):
        self.asset = asset
        self.properties = asset.extra_fields

    def __repr__(self) -> str:
        return f"<AssetStorageExtension Asset href={self.asset.href}>"


class LinkStorageExtension(_RefsMixin, StorageExtension[pystac.Link]):
    """A concrete implementation of :class:`StorageExtension` on an
    :class:`~pystac.Link` that extends the properties of the Link to include
    properties defined in the :stac-ext:`Storage Extension <storage>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`StorageExtension.ext` on an :class:`~pystac.Link` to extend it.
    """

    link: pystac.Link
    """The :class:`~pystac.Link` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Link` properties, including extension properties."""

    def __init__(self, link: pystac.Link):
        self.link = link
        self.properties = link.extra_fields

    def __repr__(self) -> str:
        return f"<LinkStorageExtension Link href={self.link.href}>"


class ItemAssetsStorageExtension(
    _RefsMixin, StorageExtension[pystac.ItemAssetDefinition]
):
    """A concrete implementation of :class:`StorageExtension` on an
    :class:`~pystac.ItemAssetDefinition` that extends the properties of the
    ItemAssetDefinition to include properties defined in the
    :stac-ext:`Storage Extension <storage>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`StorageExtension.ext` on an :class:`~pystac.ItemAssetDefinition`
    to extend it.
    """

    item_asset: pystac.ItemAssetDefinition
    """The :class:`~pystac.ItemAssetDefinition` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.ItemAssetDefinition` properties,
    including extension properties."""

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        self.item_asset = item_asset
        self.properties = item_asset.properties

    def __repr__(self) -> str:
        return f"<ItemAssetsStorageExtension ItemAssetDefinition={self.item_asset}>"


class SummariesStorageExtension(SummariesExtension):
    """A concrete implementation of :class:`~pystac.extensions.base.SummariesExtension`
    that extends the ``summaries`` field of a :class:`~pystac.Collection` to include
    properties defined in the :stac-ext:`Storage Extension <storage>`.
    """

    @property
    def schemes(self) -> list[dict[str, StorageScheme]] | None:
        """Get or sets the summary of :attr:`StorageScheme.platform` values
        for this Collection.
        """
        return map_opt(
            lambda schemes: [
                {k: StorageScheme(v) for k, v in x.items()} for x in schemes
            ],
            self.summaries.get_list(SCHEMES_PROP),
        )

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
    schema_uri: str = SCHEMA_URI_PATTERN.format(version=DEFAULT_VERSION)
    prev_extension_ids = {
        SCHEMA_URI_PATTERN.format(version=v)
        for v in SUPPORTED_VERSIONS
        if v != DEFAULT_VERSION
    }
    stac_object_types = {
        pystac.STACObjectType.CATALOG,
        pystac.STACObjectType.COLLECTION,
        pystac.STACObjectType.ITEM,
    }

    # Mapping from v1.0.0 platform enum values to v2.0.0 type identifiers
    # Only AWS and Azure have defined v2.0.0 platform definitions
    _PLATFORM_TYPE_MAP: dict[str, str] = {
        "AWS": "aws-s3",
        "AZURE": "ms-azure",
    }

    # Mapping from v1.0.0 platform enum values to v2.0.0 platform URI templates
    _PLATFORM_URI_MAP: dict[str, str] = {
        "AWS": "https://{bucket}.s3.{region}.amazonaws.com",
        "AZURE": "https://{account}.blob.core.windows.net",
    }

    # Mapping from v1.0.0 platform enum values to scheme key prefixes
    _PLATFORM_KEY_PREFIX: dict[str, str] = {
        "AWS": "aws",
        "AZURE": "azure",
    }

    # Platforms that cannot be automatically migrated
    _UNSUPPORTED_PLATFORMS: set[str] = {"GCP", "IBM", "ALIBABA", "ORACLE", "OTHER"}

    def migrate(
        self, obj: dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        if SCHEMA_URI_PATTERN.format(version="1.0.0") in info.extensions:
            props = obj.get("properties", obj)

            # v1 defined item level storage properties can
            # be used across all assets
            item_platform = props.get(PREFIX + "platform")
            item_region = props.get(PREFIX + "region")
            item_requester_pays = props.get(PREFIX + "requester_pays")
            item_tier = props.get(PREFIX + "tier")

            schemes: dict[str, dict[str, Any]] = {}
            scheme_hash_to_key: dict[int, str] = {}
            assets_with_tier: list[str] = []
            unsupported_platforms: set[str] = set()
            migrated_assets: list[str] = []

            for asset_key, asset in obj.get("assets", {}).items():
                platform = asset.get(PREFIX + "platform", item_platform)
                region = asset.get(PREFIX + "region", item_region)
                requester_pays = asset.get(
                    PREFIX + "requester_pays", item_requester_pays
                )
                tier = asset.get(PREFIX + "tier", item_tier)

                if tier is not None:
                    assets_with_tier.append(asset_key)

                # cannot migrate assets without a platform
                if platform is None:
                    continue

                # cannot migrate assets with unsupported platforms
                platform_upper = platform.upper()
                if (
                    platform_upper in self._UNSUPPORTED_PLATFORMS
                    or platform_upper not in self._PLATFORM_TYPE_MAP
                ):
                    unsupported_platforms.add(platform_upper)
                    continue

                scheme: dict[str, Any] = {
                    "type": self._PLATFORM_TYPE_MAP[platform_upper],
                    "platform": self._PLATFORM_URI_MAP[platform_upper],
                }
                if region is not None:
                    scheme["region"] = region
                if requester_pays is not None:
                    scheme["requester_pays"] = requester_pays

                # Deduplicate schemes by content hash
                scheme_hash = hash(frozenset(scheme.items()))

                if scheme_hash in scheme_hash_to_key:
                    scheme_key = scheme_hash_to_key[scheme_hash]
                else:
                    # Generate scheme key: provider-region or provider
                    # if key would collide, appends an int suffix
                    key_prefix = self._PLATFORM_KEY_PREFIX[platform_upper]
                    base_key = (
                        f"{key_prefix}-{region.lower()}" if region else key_prefix
                    )

                    scheme_key = base_key
                    counter = 1

                    while scheme_key in schemes:
                        scheme_key = f"{base_key}-{counter}"
                        counter += 1

                    schemes[scheme_key] = scheme
                    scheme_hash_to_key[scheme_hash] = scheme_key

                asset.pop(PREFIX + "platform", None)
                asset.pop(PREFIX + "region", None)
                asset.pop(PREFIX + "requester_pays", None)
                asset[REFS_PROP] = [scheme_key]
                migrated_assets.append(asset_key)

            if assets_with_tier:
                warnings.warn(
                    "storage:tier was removed in storage extension v2.0.0 and cannot "
                    f"be migrated. Property left in place for: {assets_with_tier}",
                    UserWarning,
                )

            if unsupported_platforms:
                warnings.warn(
                    "The following platforms cannot be automatically migrated to "
                    f"storage extension v2.0.0: {unsupported_platforms}",
                    UserWarning,
                )

            # Only remove item-level properties if all assets were migrated
            if migrated_assets and not unsupported_platforms:
                props.pop(PREFIX + "platform", None)
                props.pop(PREFIX + "region", None)
                props.pop(PREFIX + "requester_pays", None)

            if schemes:
                props[SCHEMES_PROP] = schemes

        super().migrate(obj, version, info)


STORAGE_EXTENSION_HOOKS: ExtensionHooks = StorageExtensionHooks()
