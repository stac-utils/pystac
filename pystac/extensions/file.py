"""Implements the :stac-ext:`File Info Extension <file>`."""

from __future__ import annotations

import warnings
from collections.abc import Iterable
from typing import Any, Generic, Literal, TypeVar, Union, cast

from pystac import (
    Asset,
    Catalog,
    Collection,
    ExtensionTypeError,
    Item,
    Link,
    STACObjectType,
)
from pystac.extensions.base import ExtensionManagementMixin, PropertiesExtension
from pystac.extensions.hooks import ExtensionHooks
from pystac.serialization.identify import (
    OldExtensionShortIDs,
    STACJSONDescription,
    STACVersionID,
)
from pystac.utils import StringEnum, get_required, map_opt

T = TypeVar("T", Asset, Link)

SCHEMA_URI = "https://stac-extensions.github.io/file/v2.1.0/schema.json"

PREFIX = "file:"
BYTE_ORDER_PROP = PREFIX + "byte_order"
CHECKSUM_PROP = PREFIX + "checksum"
HEADER_SIZE_PROP = PREFIX + "header_size"
SIZE_PROP = PREFIX + "size"
VALUES_PROP = PREFIX + "values"
LOCAL_PATH_PROP = PREFIX + "local_path"


class ByteOrder(StringEnum):
    """List of allows values for the ``"file:byte_order"`` field defined by the
    :stac-ext:`File Info Extension <file>`."""

    LITTLE_ENDIAN = "little-endian"
    BIG_ENDIAN = "big-endian"


class MappingObject:
    """Represents a value map used by assets that are used as classification layers, and
    give details about the values in the asset and their meanings."""

    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]) -> None:
        self.properties = properties

    def apply(self, values: list[Any], summary: str) -> None:
        """Sets the properties for this :class:`~MappingObject` instance.

        Args:
            values : The value(s) in the file. At least one array element is required.
            summary : A short description of the value(s).
        """
        self.values = values
        self.summary = summary

    @classmethod
    def create(cls, values: list[Any], summary: str) -> MappingObject:
        """Creates a new :class:`~MappingObject` instance.

        Args:
            values : The value(s) in the file. At least one array element is required.
            summary : A short description of the value(s).
        """
        m = cls({})
        m.apply(values=values, summary=summary)
        return m

    @property
    def values(self) -> list[Any]:
        """Gets or sets the list of value(s) in the file. At least one array element is
        required."""
        return get_required(self.properties.get("values"), self, "values")

    @values.setter
    def values(self, v: list[Any]) -> None:
        self.properties["values"] = v

    @property
    def summary(self) -> str:
        """Gets or sets the short description of the value(s)."""
        return get_required(self.properties.get("summary"), self, "summary")

    @summary.setter
    def summary(self, v: str) -> None:
        self.properties["summary"] = v

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> MappingObject:
        return cls.create(**d)

    def to_dict(self) -> dict[str, Any]:
        return self.properties


class FileExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Union[Catalog, Collection, Item]],
):
    """A class that can be used to extend the properties of an :class:`~pystac.Asset`
    or :class:`~pystac.Link` with properties from the
    :stac-ext:`File Info Extension <file>`.

    To create an instance of :class:`FileExtension`, use the
    :meth:`FileExtension.ext` method. For example:

    .. code-block:: python

       >>> asset: pystac.Asset = ...
       >>> file_ext = FileExtension.ext(asset)
    """

    name: Literal["file"] = "file"

    def apply(
        self,
        byte_order: ByteOrder | None = None,
        checksum: str | None = None,
        header_size: int | None = None,
        size: int | None = None,
        values: list[MappingObject] | None = None,
        local_path: str | None = None,
    ) -> None:
        """Applies file extension properties to the extended Item.

        Args:
            byte_order : Optional byte order of integer values in the file. One of
                ``"big-endian"`` or ``"little-endian"``.
            checksum : Optional multihash for the corresponding file,
                encoded as hexadecimal (base 16) string with lowercase letters.
            header_size : Optional header size of the file, in bytes.
            size : Optional size of the file, in bytes.
            values : Optional list of :class:`~MappingObject` instances that lists the
                values that are in the file and describe their meaning. See the
                :stac-ext:`Mapping Object <file#mapping-object>` docs for an example.
                If given, at least one array element is required.
        """
        self.byte_order = byte_order
        self.checksum = checksum
        self.header_size = header_size
        self.size = size
        self.values = values
        self.local_path = local_path

    @property
    def byte_order(self) -> ByteOrder | None:
        """Gets or sets the byte order of integer values in the file. One of big-endian
        or little-endian."""
        return self._get_property(BYTE_ORDER_PROP, ByteOrder)

    @byte_order.setter
    def byte_order(self, v: ByteOrder | None) -> None:
        self._set_property(BYTE_ORDER_PROP, v)

    @property
    def checksum(self) -> str | None:
        """Get or sets the multihash for the corresponding file, encoded as hexadecimal
        (base 16) string with lowercase letters."""
        return self._get_property(CHECKSUM_PROP, str)

    @checksum.setter
    def checksum(self, v: str | None) -> None:
        self._set_property(CHECKSUM_PROP, v)

    @property
    def header_size(self) -> int | None:
        """Get or sets the header size of the file, in bytes."""
        return self._get_property(HEADER_SIZE_PROP, int)

    @header_size.setter
    def header_size(self, v: int | None) -> None:
        self._set_property(HEADER_SIZE_PROP, v)

    @property
    def local_path(self) -> str | None:
        """Get or sets a relative local path for the asset/link.

        The ``file:local_path`` field indicates a **relative** path that
        can be used by clients for different purposes to organize the
        files locally. For compatibility reasons the name-separator
        character in paths **must** be ``/`` and the Windows separator ``\\``
        is **not** allowed.
        """
        return self._get_property(LOCAL_PATH_PROP, str)

    @local_path.setter
    def local_path(self, v: str | None) -> None:
        self._set_property(LOCAL_PATH_PROP, v, pop_if_none=True)

    @property
    def size(self) -> int | None:
        """Get or sets the size of the file, in bytes."""
        return self._get_property(SIZE_PROP, int)

    @size.setter
    def size(self, v: int | None) -> None:
        self._set_property(SIZE_PROP, v)

    @property
    def values(self) -> list[MappingObject] | None:
        """Get or sets the list of :class:`~MappingObject` instances that lists the
        values that are in the file and describe their meaning. See the
        :stac-ext:`Mapping Object <file#mapping-object>` docs for an example. If given,
        at least one array element is required."""
        return map_opt(
            lambda values: [
                MappingObject.from_dict(mapping_obj) for mapping_obj in values
            ],
            self._get_property(VALUES_PROP, list[dict[str, Any]]),
        )

    @values.setter
    def values(self, v: list[MappingObject] | None) -> None:
        self._set_property(
            VALUES_PROP,
            map_opt(
                lambda values: [mapping_obj.to_dict() for mapping_obj in values], v
            ),
        )

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: Asset | Link, add_if_missing: bool = False) -> FileExtension[T]:
        """Extends the given STAC Object with properties from the :stac-ext:`File Info
        Extension <file>`.

        This extension can be applied to instances of :class:`~pystac.Asset` or
        :class:`~pystac.Link`
        """
        if isinstance(obj, Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(FileExtension[T], AssetFileExtension(obj))
        elif isinstance(obj, Link):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(FileExtension[T], LinkFileExtension(obj))
        else:
            raise ExtensionTypeError(cls._ext_error_message(obj))


class AssetFileExtension(FileExtension[Asset]):
    """A concrete implementation of :class:`FileExtension` on an
    :class:`~pystac.Asset` that extends the Asset fields to include properties defined
    in the :stac-ext:`File Info Extension <file>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`FileExtension.ext` on an :class:`~pystac.Asset` to extend it.
    """

    asset_href: str
    """The ``href`` value of the :class:`~pystac.Asset` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Asset` fields, including extension properties."""

    additional_read_properties: Iterable[dict[str, Any]] | None = None
    """If present, this will be a list containing 1 dictionary representing the
    properties of the owner."""

    def __init__(self, asset: Asset):
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and hasattr(asset.owner, "properties"):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return f"<AssetFileExtension Asset href={self.asset_href}>"


class LinkFileExtension(FileExtension[Link]):
    """A concrete implementation of :class:`FileExtension` on an
    :class:`~pystac.Link` that extends the Link fields to include properties defined
    in the :stac-ext:`File Info Extension <file>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`FileExtension.ext` on an :class:`~pystac.Link` to extend it.
    """

    link_href: str
    """The ``href`` value of the :class:`~pystac.Link` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Link` fields, including extension properties."""

    additional_read_properties: Iterable[dict[str, Any]] | None = None
    """If present, this will be a list containing 1 dictionary representing the
    properties of the owner."""

    def __init__(self, link: Link):
        self.link_href = link.href
        self.properties = link.extra_fields
        if link.owner and hasattr(link.owner, "properties"):
            self.additional_read_properties = [link.owner.properties]

    def __repr__(self) -> str:
        return f"<LinkFileExtension Link href={self.link_href}>"


class FileExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {
        "file",
        "https://stac-extensions.github.io/file/v1.0.0/schema.json",
        "https://stac-extensions.github.io/file/v2.0.0/schema.json",
    }
    stac_object_types = {
        STACObjectType.ITEM,
        STACObjectType.COLLECTION,
        STACObjectType.CATALOG,
    }
    removed_fields = {
        "file:bits_per_sample",
        "file:data_type",
        "file:nodata",
        "file:unit",
    }

    def migrate(
        self, obj: dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        # The checksum field was previously it's own extension.
        old_checksum: dict[str, str] | None = None
        if info.version_range.latest_valid_version() < "v1.0.0-rc.2":
            if OldExtensionShortIDs.CHECKSUM.value in info.extensions:
                old_item_checksum = obj["properties"].get("checksum:multihash")
                if old_item_checksum is not None:
                    if old_checksum is None:
                        old_checksum = {}
                    old_checksum["__item__"] = old_item_checksum
                for asset_key, asset in obj["assets"].items():
                    old_asset_checksum = asset.get("checksum:multihash")
                    if old_asset_checksum is not None:
                        if old_checksum is None:
                            old_checksum = {}
                        old_checksum[asset_key] = old_asset_checksum

                try:
                    obj["stac_extensions"].remove(OldExtensionShortIDs.CHECKSUM.value)
                except ValueError:
                    pass

        super().migrate(obj, version, info)

        if old_checksum is not None:
            if SCHEMA_URI not in obj["stac_extensions"]:
                obj["stac_extensions"].append(SCHEMA_URI)
            for key in old_checksum:
                if key == "__item__":
                    obj["properties"][CHECKSUM_PROP] = old_checksum[key]
                else:
                    obj["assets"][key][CHECKSUM_PROP] = old_checksum[key]

        found_fields = {}
        for asset_key, asset in obj.get("assets", {}).items():
            if values := set(asset.keys()).intersection(self.removed_fields):
                found_fields[asset_key] = values

        if found_fields:
            warnings.warn(
                f"Assets {list(found_fields.keys())} contain fields: "
                f"{list(set.union(*found_fields.values()))} which "
                "were removed from the file extension spec in v2.0.0. Please "
                "consult the release notes "
                "(https://github.com/stac-extensions/file/releases/tag/v2.0.0) "
                "for instructions on how to migrate these fields.",
                UserWarning,
            )


FILE_EXTENSION_HOOKS: ExtensionHooks = FileExtensionHooks()
