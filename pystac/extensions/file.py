"""Implements the File extension.

https://github.com/stac-extensions/file
"""

import enum
from typing import Any, Dict, Generic, List, Optional, Set, TypeVar, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.serialization.identify import (
    OldExtensionShortIDs,
    STACJSONDescription,
    STACVersionID,
)
from pystac.utils import map_opt

T = TypeVar("T", pystac.Item, pystac.Asset)

SCHEMA_URI = "https://stac-extensions.github.io/file/v1.0.0/schema.json"

DATA_TYPE_PROP = "file:data_type"
SIZE_PROP = "file:size"
NODATA_PROP = "file:nodata"
CHECKSUM_PROP = "file:checksum"


class FileDataType(str, enum.Enum):
    def __str__(self) -> str:
        return str(self.value)

    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"
    INT64 = "int64"
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"
    UINT64 = "uint64"
    FLOAT16 = "float16"
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    CINT16 = "cint16"
    CINT32 = "cint32"
    CFLOAT32 = "cfloat32"
    CFLOAT64 = "cfloat64"
    OTHER = "other"


class FileExtension(
    Generic[T], PropertiesExtension, ExtensionManagementMixin[pystac.Item]
):
    """FileItemExt is the extension of the Item in the file extension which
    adds file related details such as checksum, data type and size for assets.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The Item that is being extended.

    Note:
        Using FileItemExt to directly wrap an item will add the 'file' extension ID to
        the item's stac_extensions.
    """

    def apply(
        self,
        data_type: Optional[FileDataType] = None,
        size: Optional[int] = None,
        nodata: Optional[List[Any]] = None,
        checksum: Optional[str] = None,
    ) -> None:
        """Applies file extension properties to the extended Item.

        Args:
            data_type (FileDataType): The data type of the file.
            size (int or None): size of the file in bytes.
            nodata (List[Object] or None): Value(s) for no-data.
            checksum (str or None): Multihash for the corresponding file,
                encoded as hexadecimal (base 16) string with lowercase letters.
        """
        self.data_type = data_type
        self.size = size
        self.nodata = nodata
        self.checksum = checksum

    @property
    def data_type(self) -> Optional[FileDataType]:
        """Get or sets the data_type of the file.

        Returns:
            FileDataType
        """
        return map_opt(
            lambda s: FileDataType(s), self._get_property(DATA_TYPE_PROP, str)
        )

    @data_type.setter
    def data_type(self, v: Optional[FileDataType]) -> None:
        self._set_property(DATA_TYPE_PROP, str(v))

    @property
    def size(self) -> Optional[int]:
        """Get or sets the size in bytes of the file

        Returns:
            int or None
        """
        return self._get_property(SIZE_PROP, int)

    @size.setter
    def size(self, v: Optional[int]) -> None:
        self._set_property(SIZE_PROP, v)

    @property
    def nodata(self) -> Optional[List[Any]]:
        """Get or sets the no data values"""
        return self._get_property(NODATA_PROP, List[Any])

    @nodata.setter
    def nodata(self, v: Optional[List[Any]]) -> None:
        self._set_property(NODATA_PROP, v)

    @property
    def checksum(self) -> Optional[str]:
        """Get or sets the checksum

        Returns:
            str or None
        """
        return self._get_property(CHECKSUM_PROP, str)

    @checksum.setter
    def checksum(self, v: Optional[str]) -> None:
        self._set_property(CHECKSUM_PROP, v)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @staticmethod
    def ext(obj: T) -> "FileExtension[T]":
        if isinstance(obj, pystac.Item):
            return cast(FileExtension[T], ItemFileExtension(obj))
        elif isinstance(obj, pystac.Asset):
            return cast(FileExtension[T], AssetFileExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"File extension does not apply to type {type(obj)}"
            )

    @staticmethod
    def summaries(obj: pystac.Collection) -> "SummariesFileExtension":
        return SummariesFileExtension(obj)


class ItemFileExtension(FileExtension[pystac.Item]):
    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return "<ItemFileExtension Item id={}>".format(self.item.id)


class AssetFileExtension(FileExtension[pystac.Asset]):
    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.properties
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return "<AssetFileExtension Asset href={}>".format(self.asset_href)


class SummariesFileExtension(SummariesExtension):
    @property
    def data_type(self) -> Optional[List[FileDataType]]:
        """Get or sets the data_type of the file.

        Returns:
            FileDataType
        """
        return map_opt(
            lambda x: [FileDataType(t) for t in x],
            self.summaries.get_list(DATA_TYPE_PROP, str),
        )

    @data_type.setter
    def data_type(self, v: Optional[List[FileDataType]]) -> None:
        self._set_summary(DATA_TYPE_PROP, map_opt(lambda x: [str(t) for t in x], v))

    @property
    def size(self) -> Optional[pystac.RangeSummary[int]]:
        """Get or sets the size in bytes of the file

        Returns:
            int or None
        """
        return self.summaries.get_range(SIZE_PROP, int)

    @size.setter
    def size(self, v: Optional[pystac.RangeSummary[int]]) -> None:
        self._set_summary(SIZE_PROP, v)

    @property
    def nodata(self) -> Optional[List[Any]]:
        """Get or sets the list of no data values"""
        return self.summaries.get_list(NODATA_PROP, List[Any])

    @nodata.setter
    def nodata(self, v: Optional[List[Any]]) -> None:
        self._set_summary(NODATA_PROP, v)


class FileExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: Set[str] = set(["file"])
    stac_object_types: Set[pystac.STACObjectType] = set([pystac.STACObjectType.ITEM])

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


FILE_EXTENSION_HOOKS = FileExtensionHooks()
