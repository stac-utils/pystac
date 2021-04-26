import enum
from typing import Any, Generic, List, Optional, TypeVar, Union

import pystac as ps
from pystac.extensions.base import EnableExtensionMixin, ExtensionException, PropertiesExtension
from pystac.utils import map_opt

T = TypeVar('T', contravariant=True, bound=Union[ps.Item, ps.Asset])

SCHEMA_URI = "https://stac-extensions.github.io/eo/v1.0.0/schema.json"

DATA_TYPE_PROP = 'file:data_type'
SIZE_PROP = "file:size"
NODATA_PROP = 'file:nodata'
CHECKSUM_PROP = 'file:checksum'


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


class FileExtension(Generic[T], PropertiesExtension):
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
    def apply(self,
              data_type: Optional[FileDataType] = None,
              size: Optional[int] = None,
              nodata: Optional[List[Any]] = None,
              checksum: Optional[str] = None) -> None:
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
        return map_opt(lambda s: FileDataType(s), self._get_property(DATA_TYPE_PROP, str))

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


class ItemFileExtension(EnableExtensionMixin[ps.Item], FileExtension[ps.Item]):
    schema_uri = SCHEMA_URI

    def __init__(self, item: ps.Item):
        self.obj = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return '<ItemFileExtension Item id={}>'.format(self.obj.id)


class AssetFileExtension(FileExtension[ps.Asset]):
    def __init__(self, asset: ps.Asset):
        self.asset_href = asset.href
        self.properties = asset.properties
        if asset.owner:
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return '<AssetFileExtension Asset href={}>'.format(self.asset_href)


def file_ext(obj: Union[ps.Item, ps.Asset]) -> FileExtension[T]:
    if isinstance(obj, ps.Item):
        return ItemFileExtension(obj)
    elif isinstance(obj, ps.Asset):
        return AssetFileExtension(obj)
    else:
        raise ExtensionException(f"File extension does not apply to type {type(obj)}")