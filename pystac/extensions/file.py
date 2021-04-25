import enum
from typing import Any, List, Optional

from pystac import Extensions
from pystac.item import Asset, Item
from pystac.extensions.base import (ItemExtension, ExtensionDefinition, ExtendedObject)


class FileDataType(enum.Enum):
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


class FileItemExt(ItemExtension):
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
    def __init__(self, item: Item) -> None:
        if item.stac_extensions is None:
            item.stac_extensions = [str(Extensions.FILE)]
        elif str(Extensions.FILE) not in item.stac_extensions:
            item.stac_extensions.append(str(Extensions.FILE))

        self.item = item

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
        return self.get_data_type()

    @data_type.setter
    def data_type(self, v: Optional[FileDataType]) -> None:
        self.set_data_type(v)

    def get_data_type(self, asset: Optional[Asset] = None) -> Optional[FileDataType]:
        """Gets an Item or an Asset data_type.

        If an Asset is supplied and the data_type property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            FileDataType
        """
        if asset is not None and 'file:data_type' in asset.properties:
            data_type = asset.properties.get('file:data_type')
        else:
            data_type = self.item.properties.get('file:data_type')

        if data_type is not None:
            return FileDataType(data_type)
        return None

    def set_data_type(self,
                      data_type: Optional[FileDataType],
                      asset: Optional[Asset] = None) -> None:
        """Set an Item or an Asset data_type.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        v = None if data_type is None else data_type.value
        self._set_property('file:data_type', v, asset)

    @property
    def size(self) -> Optional[int]:
        """Get or sets the size in bytes of the file

        Returns:
            int or None
        """
        return self.get_size()

    @size.setter
    def size(self, v: Optional[int]) -> None:
        self.set_size(v)

    def get_size(self, asset: Optional[Asset] = None) -> Optional[int]:
        """Gets an Item or an Asset file size.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            int
        """
        if asset is None or 'file:size' not in asset.properties:
            return self.item.properties.get('file:size')
        else:
            return asset.properties.get('file:size')

    def set_size(self, size: Optional[int], asset: Optional[Asset] = None) -> None:
        """Set an Item or an Asset size.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        self._set_property('file:size', size, asset)

    @property
    def nodata(self) -> Optional[List[Any]]:
        """Get or sets the no data values"""
        return self.get_nodata()

    @nodata.setter
    def nodata(self, v: Optional[List[Any]]) -> None:
        self.set_nodata(v)

    def get_nodata(self, asset: Optional[Asset] = None) -> Optional[List[Any]]:
        """Gets an Item or an Asset nodata values.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            list[object]
        """
        if asset is None or 'file:nodata' not in asset.properties:
            return self.item.properties.get('file:nodata')
        else:
            return asset.properties.get('file:nodata')

    def set_nodata(self, nodata: Optional[List[Any]], asset: Optional[Asset] = None) -> None:
        """Set an Item or an Asset nodata values.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        self._set_property('file:nodata', nodata, asset)

    @property
    def checksum(self) -> Optional[str]:
        """Get or sets the checksum

        Returns:
            str or None
        """
        return self.get_checksum()

    @checksum.setter
    def checksum(self, v: Optional[str]) -> None:
        self.set_checksum(v)

    def get_checksum(self, asset: Optional[Asset] = None) -> Optional[str]:
        """Gets an Item or an Asset checksum.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value
        """
        if asset is None or 'file:checksum' not in asset.properties:
            return self.item.properties.get('file:checksum')
        else:
            return asset.properties.get('file:checksum')

    def set_checksum(self, checksum: Optional[str], asset: Optional[Asset] = None) -> None:
        """Set an Item or an Asset checksum.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        self._set_property('file:checksum', checksum, asset)

    def __repr__(self) -> str:
        return '<FileItemExt Item id={}>'.format(self.item.id)

    @classmethod
    def _object_links(cls) -> List[str]:
        return []

    @classmethod
    def from_item(cls, item: Item) -> "FileItemExt":
        return cls(item)


FILE_EXTENSION_DEFINITION: ExtensionDefinition = ExtensionDefinition(
    Extensions.FILE, [ExtendedObject(Item, FileItemExt)])
