"""Implements the :stac-ext:`Versioning Indicators Extension <version>`."""

from __future__ import annotations

import warnings
from collections.abc import Generator
from contextlib import contextmanager
from typing import (
    Any,
    Generic,
    Literal,
    TypeVar,
    cast,
)

from pystac import (
    Asset,
    Catalog,
    Collection,
    ExtensionTypeError,
    Item,
    ItemAssetDefinition,
    Link,
    MediaType,
    STACObject,
    STACObjectType,
)
from pystac.errors import DeprecatedWarning
from pystac.extensions.base import ExtensionManagementMixin, PropertiesExtension
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import StringEnum, map_opt

#: Generalized version of :class:`~pystac.Catalog`, :class:`~pystac.Collection`,
#: :class:`~pystac.Item`, :class:`~pystac.Asset` or :class:`~pystac.ItemAssetDefinition`
T = TypeVar("T", Catalog, Collection, Item, Asset, ItemAssetDefinition)

#: Generalized version of :class:`~pystac.Catalog`, :class:`~pystac.Collection`, or
#: :class:`~pystac.Item`
U = TypeVar("U", Catalog, Collection, Item)

SCHEMA_URI = "https://stac-extensions.github.io/version/v1.2.0/schema.json"

# STAC fields - These are unusual for an extension in that they do not have
# a prefix.  e.g. nothing like "ver:"
VERSION: str = "version"
DEPRECATED: str = "deprecated"
EXPERIMENTAL: str = "experimental"


class VersionRelType(StringEnum):
    """A list of rel types defined in the Version Extension.

    See the :stac-ext:`Version Extension Relation types
    <version#relation-types>` documentation
    for details."""

    LATEST = "latest-version"
    """Indicates a link pointing to a resource containing the latest version."""

    PREDECESSOR = "predecessor-version"
    """Indicates a link pointing to a resource containing the predecessor version in the
    version history."""

    SUCCESSOR = "successor-version"
    """Indicates a link pointing to a resource containing the successor version in the
    version history."""

    HISTORY = "version-history"
    """This link points to a version history or changelog.
    
    This can be for example a Markdown file with the corresponding media type or
    a STAC Catalog or Collection.
    """


class BaseVersionExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Catalog | Collection | Item],
):
    """A base extension that just gets and sets attributes, not links.

    Used for Assets and AssetDefinitions.
    """

    name: Literal["version"] = "version"

    def apply_base(
        self,
        version: str | None = None,
        deprecated: bool | None = None,
        experimental: bool | None = None,
    ) -> None:
        """Applies attributes to this extension object."""
        self.version = version
        self.deprecated = deprecated
        self.experimental = experimental

    @property
    def version(self) -> str | None:
        """Get or sets a version string of this object."""
        return self._get_property(VERSION, str)

    @version.setter
    def version(self, v: str) -> None:
        self._set_property(VERSION, v, pop_if_none=True)

    @property
    def deprecated(self) -> bool | None:
        """Get or sets whether this object is deprecated.

        A value of ``True`` specifies that the object is deprecated with the
        potential to be removed. It should be transitioned out of usage as soon
        as possible and users should refrain from using it in new projects. A
        link with relation type ``latest-version`` SHOULD be added to the links
        and MUST refer to the resource that can be used instead.

        NOTE:
            A :class:`pystac.DeprecatedWarning` is issued if the ``deprecated``
            property is ``True`` when deserializing a dictionary to an object.
            The :meth:`~pystac.extensions.version.ignore_deprecated` context
            manager is provided as a convenience to suppress these warnings:

            >>> with ignore_deprecated():
            ...    deprecated_item = pystac.Item.from_dict(deprecated_item_dict)
        """
        return self._get_property(DEPRECATED, bool)

    @deprecated.setter
    def deprecated(self, v: bool | None) -> None:
        self._set_property(DEPRECATED, v, pop_if_none=True)

    @property
    def experimental(self) -> bool | None:
        """Get and set whether this object is experimental.

        Specifies that the context this field is used in (e.g. Asset or
        Collection) is experimental with the potential to break or be unstable.
        """
        return self._get_property(EXPERIMENTAL, bool)

    @experimental.setter
    def experimental(self, v: bool | None) -> None:
        self._set_property(EXPERIMENTAL, v, pop_if_none=True)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> BaseVersionExtension[T]:
        """Extends the given STAC Object with properties from the :stac-ext:`Versioning
        Indicators Extension <version>`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, Collection):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(BaseVersionExtension[T], CollectionVersionExtension(obj))
        elif isinstance(obj, Catalog):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(BaseVersionExtension[T], CatalogVersionExtension(obj))
        elif isinstance(obj, Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(BaseVersionExtension[T], ItemVersionExtension(obj))
        elif isinstance(obj, Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(BaseVersionExtension[T], AssetVersionExtension(obj))
        else:
            raise ExtensionTypeError(cls._ext_error_message(obj))


class VersionExtension(
    Generic[U],
    BaseVersionExtension[U],
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Item`, :class:`~pystac.Collection`, or
    :class:`~pystac.Catalog` with properties from the :stac-ext:`Versioning
    Indicators Extension <version>`. This class is generic over the type of STAC
    Object to be extended.

    To create a concrete instance of :class:`VersionExtension`, use the
    :meth:`VersionExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> version_ext = VersionExtension.ext(item)
    """

    obj: STACObject

    def __init__(self, obj: STACObject) -> None:
        self.obj = obj

    def apply(
        self,
        version: str | None = None,
        deprecated: bool | None = None,
        experimental: bool | None = None,
        latest: U | None = None,
        predecessor: U | None = None,
        successor: U | None = None,
    ) -> None:
        """Applies version extension properties to the extended :class:`~pystac.Item` or
        :class:`~pystac.Collection`.

        Args:
            version : The version string for the item.
            deprecated : Optional flag set to ``True`` if an Item is deprecated with the
                potential to be removed.  Defaults to ``False`` if not present.
            latest : Item representing the latest (e.g., current) version.
            predecessor : Item representing the resource containing the predecessor
                version in the version history.
            successor : Item representing the resource containing the successor version
                in the version history.
        """
        self.apply_base(version, deprecated, experimental)
        if latest:
            self.latest = latest
        if predecessor:
            self.predecessor = predecessor
        if successor:
            self.successor = successor

    @property
    def latest(self) -> U | None:
        """Gets or sets the :class:`~pystac.Link` to the :class:`~pystac.Item`
        representing the most recent version.
        """
        return map_opt(
            lambda x: cast(U, x),
            next(iter(self.obj.get_stac_objects(VersionRelType.LATEST)), None),
        )

    @latest.setter
    def latest(self, value: U | None) -> None:
        self.obj.clear_links(VersionRelType.LATEST)
        if value is not None:
            self.obj.add_link(Link(VersionRelType.LATEST, value, MediaType.JSON))

    @property
    def predecessor(self) -> U | None:
        """Gets or sets the :class:`~pystac.Link` to the :class:`~pystac.Item`
        representing the resource containing the predecessor version in the version
        history.
        """
        return map_opt(
            lambda x: cast(U, x),
            next(iter(self.obj.get_stac_objects(VersionRelType.PREDECESSOR)), None),
        )

    @predecessor.setter
    def predecessor(self, value: U | None) -> None:
        self.obj.clear_links(VersionRelType.PREDECESSOR)
        if value is not None:
            self.obj.add_link(
                Link(
                    VersionRelType.PREDECESSOR,
                    value,
                    MediaType.JSON,
                )
            )

    @property
    def successor(self) -> U | None:
        """Gets or sets the :class:`~pystac.Link` to the :class:`~pystac.Item`
        representing the resource containing the successor version in the version
        history.
        """
        return map_opt(
            lambda x: cast(U, x),
            next(iter(self.obj.get_stac_objects(VersionRelType.SUCCESSOR)), None),
        )

    @successor.setter
    def successor(self, value: U | None) -> None:
        self.obj.clear_links(VersionRelType.SUCCESSOR)
        if value is not None:
            self.obj.add_link(Link(VersionRelType.SUCCESSOR, value, MediaType.JSON))

    @classmethod
    def ext(cls, obj: U, add_if_missing: bool = False) -> VersionExtension[U]:
        """Extends the given STAC Object with properties from the :stac-ext:`Versioning
        Indicators Extension <version>`.

        This extension can be applied to instances of :class:`~pystac.Item` or
        :class:`~pystac.Collection`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, Collection):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(VersionExtension[U], CollectionVersionExtension(obj))
        elif isinstance(obj, Catalog):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(VersionExtension[U], CatalogVersionExtension(obj))
        elif isinstance(obj, Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(VersionExtension[U], ItemVersionExtension(obj))
        else:
            raise ExtensionTypeError(cls._ext_error_message(obj))


class CatalogVersionExtension(VersionExtension[Catalog]):
    """A concrete implementation of :class:`VersionExtension` on a
    :class:`~pystac.Catalog` that extends the properties of the Catalog to
    include properties defined in the :stac-ext:`Versioning Indicators Extension
    <version>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`VersionExtension.ext` on an :class:`~pystac.Catalog` to extend it.
    """

    catalog: Catalog
    links: list[Link]
    properties: dict[str, Any]

    def __init__(self, catalog: Catalog):
        self.catalog = catalog
        self.properties = catalog.extra_fields
        self.links = catalog.links
        super().__init__(self.catalog)

    def __repr__(self) -> str:
        return f"<CatalogVersionExtension Item id={self.catalog.id}>"


class CollectionVersionExtension(VersionExtension[Collection]):
    """A concrete implementation of :class:`VersionExtension` on a
    :class:`~pystac.Collection` that extends the properties of the Collection to
    include properties defined in the :stac-ext:`Versioning Indicators Extension
    <version>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`VersionExtension.ext` on an :class:`~pystac.Collection` to extend it.
    """

    collection: Collection
    links: list[Link]
    properties: dict[str, Any]

    def __init__(self, collection: Collection):
        self.collection = collection
        self.properties = collection.extra_fields
        self.links = collection.links
        super().__init__(self.collection)

    def __repr__(self) -> str:
        return f"<CollectionVersionExtension Item id={self.collection.id}>"


class ItemVersionExtension(VersionExtension[Item]):
    """A concrete implementation of :class:`VersionExtension` on an
    :class:`~pystac.Item` that extends the properties of the Item to include properties
    defined in the :stac-ext:`Versioning Indicators Extension <version>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`VersionExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: Item
    links: list[Link]
    properties: dict[str, Any]

    def __init__(self, item: Item):
        self.item = item
        self.properties = item.properties
        self.links = item.links
        super().__init__(self.item)

    def __repr__(self) -> str:
        return f"<ItemVersionExtension Item id={self.item.id}>"


class AssetVersionExtension(BaseVersionExtension[Asset]):
    """A concrete implementation of :class:`VersionExtension` on an
    :class:`~pystac.Asset` that extends the properties of the Asset to include
    properties defined in the :stac-ext:`Versioning Indicators Extension
    <version>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`VersionExtension.ext` on an :class:`~pystac.Asset` to extend it.
    """

    asset: Asset
    properties: dict[str, Any]

    def __init__(self, asset: Asset):
        self.asset = asset
        self.properties = asset.extra_fields

    def __repr__(self) -> str:
        return f"<AssetVersionExtension Asset href={self.asset.href}>"


class ItemAssetsViewExtension(BaseVersionExtension[ItemAssetDefinition]):
    properties: dict[str, Any]

    def __init__(self, item_asset: ItemAssetDefinition):
        self.properties = item_asset.properties


class VersionExtensionHooks(ExtensionHooks):
    schema_uri = SCHEMA_URI
    prev_extension_ids = {
        "version",
        "https://stac-extensions.github.io/version/v1.0.0/schema.json",
        "https://stac-extensions.github.io/version/v1.1.0/schema.json",
    }
    stac_object_types = {
        STACObjectType.COLLECTION,
        STACObjectType.ITEM,
        STACObjectType.CATALOG,
    }

    def get_object_links(self, so: STACObject) -> list[str] | None:
        if isinstance(so, Collection) or isinstance(so, Item):
            return [
                VersionRelType.LATEST,
                VersionRelType.PREDECESSOR,
                VersionRelType.SUCCESSOR,
            ]
        return None


VERSION_EXTENSION_HOOKS: ExtensionHooks = VersionExtensionHooks()


@contextmanager
def ignore_deprecated() -> Generator[None]:
    """Context manager for suppressing the :class:`pystac.DeprecatedWarning`
    when creating a deprecated :class:`~pystac.Item` or :class:`~pystac.Collection`
    from a dictionary."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=DeprecatedWarning)
        yield
