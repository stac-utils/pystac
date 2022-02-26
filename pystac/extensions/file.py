"""Implements the :stac-ext:`File Info Extension <file>`."""

from typing import Any, Dict, Iterable, List, Optional, Union

import pystac
from pystac.extensions.base import ExtensionManagementMixin, PropertiesExtension
from pystac.extensions.hooks import ExtensionHooks
from pystac.serialization.identify import (
    OldExtensionShortIDs,
    STACJSONDescription,
    STACVersionID,
)
from pystac.utils import StringEnum, get_required, map_opt

SCHEMA_URI = "https://stac-extensions.github.io/file/v2.0.0/schema.json"

PREFIX = "file:"
BYTE_ORDER_PROP = PREFIX + "byte_order"
CHECKSUM_PROP = PREFIX + "checksum"
HEADER_SIZE_PROP = PREFIX + "header_size"
SIZE_PROP = PREFIX + "size"
VALUES_PROP = PREFIX + "values"


class ByteOrder(StringEnum):
    """List of allows values for the ``"file:byte_order"`` field defined by the
    :stac-ext:`File Info Extension <file>`."""

    LITTLE_ENDIAN = "little-endian"
    BIG_ENDIAN = "big-endian"


class MappingObject:
    """Represents a value map used by assets that are used as classification layers, and
    give details about the values in the asset and their meanings."""

    properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    def apply(self, values: List[Any], summary: str) -> None:
        """Sets the properties for this :class:`~MappingObject` instance.

        Args:
            values : The value(s) in the file. At least one array element is required.
            summary : A short description of the value(s).
        """
        self.values = values
        self.summary = summary

    @classmethod
    def create(cls, values: List[Any], summary: str) -> "MappingObject":
        """Creates a new :class:`~MappingObject` instance.

        Args:
            values : The value(s) in the file. At least one array element is required.
            summary : A short description of the value(s).
        """
        m = cls({})
        m.apply(values=values, summary=summary)
        return m

    @property
    def values(self) -> List[Any]:
        """Gets or sets the list of value(s) in the file. At least one array element is
        required."""
        return get_required(self.properties.get("values"), self, "values")

    @values.setter
    def values(self, v: List[Any]) -> None:
        self.properties["values"] = v

    @property
    def summary(self) -> str:
        """Gets or sets the short description of the value(s)."""
        return get_required(self.properties.get("summary"), self, "summary")

    @summary.setter
    def summary(self, v: str) -> None:
        self.properties["summary"] = v

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MappingObject":
        return cls.create(**d)

    def to_dict(self) -> Dict[str, Any]:
        return self.properties


class FileExtension(
    PropertiesExtension, ExtensionManagementMixin[Union[pystac.Item, pystac.Collection]]
):
    """A class that can be used to extend the properties of an :class:`~pystac.Asset`
    with properties from the :stac-ext:`File Info Extension <file>`.

    To create an instance of :class:`FileExtension`, use the
    :meth:`FileExtension.ext` method. For example:

    .. code-block:: python

       >>> asset: pystac.Asset = ...
       >>> file_ext = FileExtension.ext(asset)
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
        return "<AssetFileExtension Asset href={}>".format(self.asset_href)

    def apply(
        self,
        byte_order: Optional[ByteOrder] = None,
        checksum: Optional[str] = None,
        header_size: Optional[int] = None,
        size: Optional[int] = None,
        values: Optional[List[MappingObject]] = None,
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

    @property
    def byte_order(self) -> Optional[ByteOrder]:
        """Gets or sets the byte order of integer values in the file. One of big-endian
        or little-endian."""
        return self._get_property(BYTE_ORDER_PROP, ByteOrder)

    @byte_order.setter
    def byte_order(self, v: Optional[ByteOrder]) -> None:
        self._set_property(BYTE_ORDER_PROP, v)

    @property
    def checksum(self) -> Optional[str]:
        """Get or sets the multihash for the corresponding file, encoded as hexadecimal
        (base 16) string with lowercase letters."""
        return self._get_property(CHECKSUM_PROP, str)

    @checksum.setter
    def checksum(self, v: Optional[str]) -> None:
        self._set_property(CHECKSUM_PROP, v)

    @property
    def header_size(self) -> Optional[int]:
        """Get or sets the header size of the file, in bytes."""
        return self._get_property(HEADER_SIZE_PROP, int)

    @header_size.setter
    def header_size(self, v: Optional[int]) -> None:
        self._set_property(HEADER_SIZE_PROP, v)

    @property
    def size(self) -> Optional[int]:
        """Get or sets the size of the file, in bytes."""
        return self._get_property(SIZE_PROP, int)

    @size.setter
    def size(self, v: Optional[int]) -> None:
        self._set_property(SIZE_PROP, v)

    @property
    def values(self) -> Optional[List[MappingObject]]:
        """Get or sets the list of :class:`~MappingObject` instances that lists the
        values that are in the file and describe their meaning. See the
        :stac-ext:`Mapping Object <file#mapping-object>` docs for an example. If given,
        at least one array element is required."""
        return map_opt(
            lambda values: [
                MappingObject.from_dict(mapping_obj) for mapping_obj in values
            ],
            self._get_property(VALUES_PROP, List[Dict[str, Any]]),
        )

    @values.setter
    def values(self, v: Optional[List[MappingObject]]) -> None:
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
    def ext(cls, obj: pystac.Asset, add_if_missing: bool = False) -> "FileExtension":
        """Extends the given STAC Object with properties from the :stac-ext:`File Info
        Extension <file>`.

        This extension can be applied to instances of :class:`~pystac.Asset`.
        """
        if isinstance(obj, pystac.Asset):
            cls.validate_owner_has_extension(obj, add_if_missing)
            return cls(obj)
        else:
            raise pystac.ExtensionTypeError(
                f"File Info extension does not apply to type '{type(obj).__name__}'"
            )


class FileExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"file"}
    stac_object_types = {pystac.STACObjectType.ITEM}

    def migrate(
        self, obj: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        # The checksum field was previously it's own extension.
        old_checksum: Optional[Dict[str, str]] = None
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


FILE_EXTENSION_HOOKS: ExtensionHooks = FileExtensionHooks()
