"""Implements the :stac-ext:`Table Extension <table>.`"""
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import get_required

T = TypeVar("T", pystac.Collection, pystac.Item, pystac.Asset)

SCHEMA_URI = "https://stac-extensions.github.io/table/v1.2.0/schema.json"

PREFIX: str = "table:"
COLUMNS_PROP = PREFIX + "columns"
PRIMARY_GEOMETRY_PROP = PREFIX + "primary_geometry"
ROW_COUNT_PROP = PREFIX + "row_count"
STORAGE_OPTIONS_PROP = PREFIX + "storage_options"
TABLES_PROP = PREFIX + "tables"

# Column properties
COL_NAME_PROP = "name"
COL_DESCRIPTION_PROP = "description"
COL_TYPE_PROP = "type"

# Table properties
TBL_NAME_PROP = "name"
TBL_DESCRIPTION_PROP = "description"


class Column:
    """Object representing a column of a table."""

    properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Any]):
        self.properties = properties

    @property
    def name(self) -> str:
        """The column name"""
        return get_required(
            self.properties.get(COL_NAME_PROP), "table:column", COL_NAME_PROP
        )

    @name.setter
    def name(self, v: str) -> None:
        self.properties[COL_NAME_PROP] = v

    @property
    def description(self) -> Optional[str]:
        """Detailed multi-line description to explain the column. `CommonMark 0.29
        <http://commonmark.org/>`__ syntax MAY be used for rich text representation."""
        return self.properties.get(COL_DESCRIPTION_PROP)

    @description.setter
    def description(self, v: Optional[str]) -> None:
        if v is None:
            self.properties.pop(COL_DESCRIPTION_PROP, None)
        else:
            self.properties[COL_DESCRIPTION_PROP] = v

    @property
    def col_type(self) -> Optional[str]:
        """Data type of the column. If using a file format with a type system (like Parquet),
        we recommend you use those types"""
        return self.properties.get(COL_TYPE_PROP)

    @col_type.setter
    def col_type(self, v: Optional[str]) -> None:
        if v is None:
            self.properties.pop(COL_TYPE_PROP, None)
        else:
            self.properties[COL_TYPE_PROP] = v

    def to_dict(self) -> Dict[str, Any]:
        """Returns a JSON-like dictionary representing this ``Column``."""
        return self.properties


class Table:
    """Object containing a high-level summary about a table"""

    properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Any]):
        self.properties = properties

    @property
    def name(self) -> str:
        """The table name"""
        return get_required(self.properties.get(TBL_NAME_PROP), self, TBL_NAME_PROP)

    @name.setter
    def name(self, v: str) -> None:
        self.properties[COL_NAME_PROP] = v

    @property
    def description(self) -> Optional[str]:
        """Detailed multi-line description to explain the table. `CommonMark 0.29
        <http://commonmark.org/>`__ syntax MAY be used for rich text representation."""
        return self.properties.get(COL_DESCRIPTION_PROP)

    @description.setter
    def description(self, v: Optional[str]) -> None:
        if v is None:
            self.properties.pop(COL_DESCRIPTION_PROP, None)
        else:
            self.properties[COL_DESCRIPTION_PROP] = v

    def to_dict(self) -> Dict[str, Any]:
        """Returns a JSON-like dictionary representing this ``Table``."""
        return self.properties


class TableExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Union[pystac.Collection, pystac.Item]],
):
    """An abstract class that can be used to extend the properties of a
    :class:`~pystac.Collection`, :class:`~pystac.Item`, or :class:`~pystac.Asset` with
    properties from the :stac-ext:`Datacube Extension <datacube>`. This class is
    generic over the type of STAC Object to be extended (e.g. :class:`~pystac.Item`,
    :class:`~pystac.Asset`).

    To create a concrete instance of :class:`TableExtension`, use the
    :meth:`TableExtension.ext` method. For example:

    .. code-block:: python

        >>> item: pystac.Item = ...
        >>> tbl_ext = TableExtension.ext(item)

    """

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> "TableExtension[T]":
        """Extend the given STAC Object with properties from the
        :stac-ext:`Table Extension <table>`.

        This extension can be applied to instances of :class:`~pystac.Collection`,
        :class:`~pystac.Item` or :class:`~pystac.Asset`.

        Raises:
            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Collection):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(TableExtension[T], CollectionTableExtension(obj))
        if isinstance(obj, pystac.Item):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(TableExtension[T], ItemTableExtension(obj))
        if isinstance(obj, pystac.Asset):
            cls.validate_owner_has_extension(obj, add_if_missing)
            return cast(TableExtension[T], AssetTableExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"Table extension does not apply to type '{type(obj).__name__}'"
            )

    @property
    def columns(self) -> Optional[List[Column]]:
        """A list of :class:`Column` objects describing each column"""
        return self.properties.get(COLUMNS_PROP)

    @columns.setter
    def columns(self, v: List[Column]) -> None:
        if v is None:
            self.properties.pop(COLUMNS_PROP, None)
        else:
            self.properties[COLUMNS_PROP] = v

    @property
    def primary_geometry(self) -> Optional[str]:
        """The primary geometry column name"""
        return self._get_property(PRIMARY_GEOMETRY_PROP, str)

    @primary_geometry.setter
    def primary_geometry(self, v: Optional[str]) -> None:
        if v is None:
            self.properties.pop(PRIMARY_GEOMETRY_PROP, None)
        else:
            self.properties[PRIMARY_GEOMETRY_PROP] = v

    @property
    def row_count(self) -> Optional[int]:
        """The number of rows in the dataset"""
        return self._get_property(ROW_COUNT_PROP, int)

    @row_count.setter
    def row_count(self, v: Optional[int]) -> None:
        if v is None:
            self.properties.pop(ROW_COUNT_PROP, None)
        else:
            self.properties[ROW_COUNT_PROP] = v


class CollectionTableExtension(TableExtension[pystac.Collection]):
    """A concrete implementation of :class:`TableExtension` on a
    :class:`~pystac.Collection` that extends the properties of the Item to include
    properties defined in the :stac-ext:`Table Extension <table>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`TableExtension.ext` on an :class:`~pystac.Collection` to extend it.
    """

    collection: pystac.Collection
    properties: Dict[str, Any]

    def __init__(self, collection: pystac.Collection):
        self.collection = collection
        self.properties = collection.extra_fields

    @property
    def tables(self) -> Dict[str, Table]:
        """A mapping of table names to table objects"""
        return get_required(self.properties.get(TABLES_PROP), self, TABLES_PROP)

    @tables.setter
    def tables(self, v: Dict[str, Table]) -> None:
        self.properties[TABLES_PROP] = v

    def __repr__(self) -> str:
        return "<CollectionTableExtension Item id={}>".format(self.collection.id)


class ItemTableExtension(TableExtension[pystac.Item]):
    """A concrete implementation of :class:`TableExtension` on an
    :class:`~pystac.Item` that extends the properties of the Item to include properties
    defined in the :stac-ext:`Table Extension <table>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`TableExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: pystac.Item
    properties: Dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return "<ItemTableExtension Item id={}>".format(self.item.id)


class AssetTableExtension(TableExtension[pystac.Asset]):
    """A concrete implementation of :class:`TableExtension` on an
    :class:`~pystac.Asset` that extends the Asset fields to include properties defined
    in the :stac-ext:`Table Extension <table>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`TableExtension.ext` on an :class:`~pystac.Asset` to extend it.
    """

    asset_href: str
    properties: Dict[str, Any]
    additional_read_properties: Optional[List[Dict[str, Any]]]

    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]
        else:
            self.additional_read_properties = None

    @property
    def storage_options(self) -> Optional[Dict[str, Any]]:
        """Additional keywords for opening the dataset"""
        return self.properties.get(STORAGE_OPTIONS_PROP)

    @storage_options.setter
    def storage_options(self, v: Optional[Dict[str, Any]]) -> Any:
        if v is None:
            self.properties.pop(STORAGE_OPTIONS_PROP, None)
        else:
            self.properties[STORAGE_OPTIONS_PROP] = v

    def __repr__(self) -> str:
        return "<AssetTableExtension Item id={}>".format(self.asset_href)


class TableExtensinoHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"table"}
    stac_object_types = {pystac.STACObjectType.COLLECTION, pystac.STACObjectType.ITEM}


TABLE_EXTENSION_HOOKS: ExtensionHooks = TableExtensinoHooks()
