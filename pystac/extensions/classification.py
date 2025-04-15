"""Implements the :stac-ext:`Classification <classification>`."""

from __future__ import annotations

import re
import warnings
from collections.abc import Iterable
from re import Pattern
from typing import (
    Any,
    Generic,
    Literal,
    TypeVar,
    cast,
)

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.extensions.raster import RasterBand
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.utils import get_required, map_opt

#: Generalized version of :class:`~pystac.Item`, :class:`~pystac.Asset`,
#: :class:`~pystac.ItemAssetDefinition` or :class:`~pystac.extensions.raster.RasterBand`
T = TypeVar("T", pystac.Item, pystac.Asset, pystac.ItemAssetDefinition, RasterBand)

SCHEMA_URI_PATTERN: str = (
    "https://stac-extensions.github.io/classification/v{version}/schema.json"
)
DEFAULT_VERSION: str = "2.0.0"
SUPPORTED_VERSIONS: list[str] = ["2.0.0", "1.1.0", "1.0.0"]

# Field names
PREFIX: str = "classification:"
BITFIELDS_PROP: str = PREFIX + "bitfields"
CLASSES_PROP: str = PREFIX + "classes"
RASTER_BANDS_PROP: str = "raster:bands"

COLOR_HINT_PATTERN: Pattern[str] = re.compile("^([0-9A-Fa-f]{6})$")


class Classification:
    """Represents a single category of a classification.

    Use Classification.create to create a new Classification.
    """

    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]) -> None:
        self.properties = properties

    def apply(
        self,
        value: int,
        description: str | None = None,
        name: str | None = None,
        title: str | None = None,
        color_hint: str | None = None,
        nodata: bool | None = None,
        percentage: float | None = None,
        count: int | None = None,
    ) -> None:
        """
        Set the properties for a new Classification.

        Args:
            value: The integer value corresponding to this class
            description: The description of this class
            name: Short name of the class for machine readability. Must consist only
                of letters, numbers, -, and _ characters. Required as of v2.0 of
                this extension.
            title: Human-readable name for use in, e.g., a map legend
            color_hint: An optional hexadecimal string-encoded representation of the
                RGB color that is suggested to represent this class (six hexadecimal
                characters, all capitalized)
            nodata: If set to true classifies a value as a no-data value.
            percentage: The percentage of data values that belong to this class
                in comparison to all data values, in percent (0-100).
            count: The number of data values that belong to this class.
        """
        self.value = value
        # TODO pystac v2.0: make `name` non-optional, move it before
        # `description` in the arg list, and remove this check
        if name is None:
            raise Exception(
                "As of v2.0.0 of the classification extension, 'name' is required"
            )
        self.name = name
        self.title = title
        self.description = description
        self.color_hint = color_hint
        self.nodata = nodata
        self.percentage = percentage
        self.count = count

        if color_hint is not None:
            match = COLOR_HINT_PATTERN.match(color_hint)
            assert (
                color_hint is None or match is not None and match.group() == color_hint
            ), "Must format color hints as '^([0-9A-F]{6})$'"

    @classmethod
    def create(
        cls,
        value: int,
        description: str | None = None,
        name: str | None = None,
        title: str | None = None,
        color_hint: str | None = None,
        nodata: bool | None = None,
        percentage: float | None = None,
        count: int | None = None,
    ) -> Classification:
        """
        Create a new Classification.

        Args:
            value: The integer value corresponding to this class
            description: The optional long-form description of this class
            name: Short name of the class for machine readability. Must consist only
                of letters, numbers, -, and _ characters. Required as of v2.0 of
                this extension.
            title: Human-readable name for use in, e.g., a map legend
            color_hint: An optional hexadecimal string-encoded representation of the
                RGB color that is suggested to represent this class (six hexadecimal
                characters, all capitalized)
            nodata: If set to true classifies a value as a no-data value.
            percentage: The percentage of data values that belong to this class
                in comparison to all data values, in percent (0-100).
            count: The number of data values that belong to this class.
        """
        c = cls({})
        c.apply(
            value=value,
            name=name,
            title=title,
            description=description,
            color_hint=color_hint,
            nodata=nodata,
            percentage=percentage,
            count=count,
        )
        return c

    @property
    def value(self) -> int:
        """Get or set the class value

        Returns:
            int
        """
        return get_required(self.properties.get("value"), self, "value")

    @value.setter
    def value(self, v: int) -> None:
        self.properties["value"] = v

    @property
    def description(self) -> str | None:
        """Get or set the description of the class

        Returns:
            str
        """
        return self.properties.get("description")

    @description.setter
    def description(self, v: str | None) -> None:
        if v is not None:
            self.properties["description"] = v
        else:
            self.properties.pop("description", None)

    @property
    def name(self) -> str:
        """Get or set the name of the class

        Returns:
            Optional[str]
        """
        return get_required(self.properties.get("name"), self, "name")

    @name.setter
    def name(self, v: str) -> None:
        if v is None:
            raise Exception(
                "`name` was converted to a required attribute in classification"
                " version v2.0, so cannot be set to None"
            )
        self.properties["name"] = v

    @property
    def title(self) -> str | None:
        return self.properties.get("title")

    @title.setter
    def title(self, v: str) -> None:
        if v is not None:
            self.properties["title"] = v
        else:
            self.properties.pop("title", None)

    @property
    def color_hint(self) -> str | None:
        """Get or set the optional color hint for this class.

        The color hint must be a six-character string of capitalized hexadecimal
        characters ([0-9A-F]).

        Returns:
            Optional[str]
        """
        return self.properties.get("color_hint")

    @color_hint.setter
    def color_hint(self, v: str | None) -> None:
        if v is not None:
            match = COLOR_HINT_PATTERN.match(v)
            assert v is None or match is not None and match.group() == v, (
                "Must format color hints as '^([0-9A-F]{6})$'"
            )
            self.properties["color_hint"] = v
        else:
            self.properties.pop("color_hint", None)

    @property
    def nodata(self) -> bool | None:
        """Get or set the nodata value for this class.

        Returns:
            bool | None
        """
        return self.properties.get("nodata")

    @nodata.setter
    def nodata(self, v: bool | None) -> None:
        if v is not None:
            self.properties["nodata"] = v
        else:
            self.properties.pop("nodata", None)

    @property
    def percentage(self) -> float | None:
        """Get or set the percentage value for this class.

        Returns:
            Optional[float]
        """
        return self.properties.get("percentage")

    @percentage.setter
    def percentage(self, v: float | None) -> None:
        if v is not None:
            self.properties["percentage"] = v
        else:
            self.properties.pop("percentage", None)

    @property
    def count(self) -> int | None:
        """Get or set the count value for this class.

        Returns:
            Optional[int]
        """
        return self.properties.get("count")

    @count.setter
    def count(self, v: int | None) -> None:
        if v is not None:
            self.properties["count"] = v
        else:
            self.properties.pop("count", None)

    def to_dict(self) -> dict[str, Any]:
        """Returns the dictionary encoding of this class

        Returns:
            dict: The serialization of the Classification
        """
        return self.properties

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Classification):
            raise NotImplementedError
        return (
            self.value == other.value
            and self.description == other.description
            and self.name == other.name
            and self.color_hint == other.color_hint
        )

    def __repr__(self) -> str:
        return f"<Classification value={self.value} description={self.description}>"


class Bitfield:
    """Encodes the representation of values as bits in an integer.

    Use Bitfield.create to create a new Bitfield.
    """

    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]):
        self.properties = properties

    def apply(
        self,
        offset: int,
        length: int,
        classes: list[Classification],
        roles: list[str] | None = None,
        description: str | None = None,
        name: str | None = None,
    ) -> None:
        """Sets the properties for this Bitfield.

        Args:
            offset: describes the position of the least significant bit captured
                by this bitfield, with zero indicating the least significant binary
                digit
            length: the number of bits described by this bitfield
            classes: a list of Classification objects describing the various levels
                captured by this bitfield
            roles: the optional role of this bitfield (see `Asset Roles
                <https://github.com/radiantearth/stac-spec/blob/master/item-spec/item-spec.md#asset-roles>`)
            description: an optional short description of the classification
            name: the optional name of the class for machine readability
        """
        self.offset = offset
        self.length = length
        self.classes = classes
        self.roles = roles
        self.description = description
        self.name = name

        assert offset >= 0, "Non-negative offsets only"
        assert length >= 1, "Positive field lengths only"
        assert len(classes) > 0, "Must specify at least one class"
        assert roles is None or len(roles) > 0, (
            "When set, roles must contain at least one item"
        )

    @classmethod
    def create(
        cls,
        offset: int,
        length: int,
        classes: list[Classification],
        roles: list[str] | None = None,
        description: str | None = None,
        name: str | None = None,
    ) -> Bitfield:
        """Sets the properties for this Bitfield.

        Args:
            offset: describes the position of the least significant bit captured
                by this bitfield, with zero indicating the least significant binary
                digit
            length: the number of bits described by this bitfield
            classes: a list of Classification objects describing the various levels
                captured by this bitfield
            roles: the optional role of this bitfield (see `Asset Roles
                <https://github.com/radiantearth/stac-spec/blob/master/item-spec/item-spec.md#asset-roles>`)
            description: an optional short description of the classification
            name: the optional name of the class for machine readability
        """
        b = cls({})
        b.apply(
            offset=offset,
            length=length,
            classes=classes,
            roles=roles,
            description=description,
            name=name,
        )
        return b

    @property
    def offset(self) -> int:
        """Get or set the offset of the bitfield.

        Describes the position of the least significant bit captured by this
        bitfield, with zero indicating the least significant binary digit

        Returns:
            int
        """
        return get_required(self.properties.get("offset"), self, "offset")

    @offset.setter
    def offset(self, v: int) -> None:
        self.properties["offset"] = v

    @property
    def length(self) -> int:
        """Get or set the length (number of bits) of the bitfield

        Returns:
            int
        """
        return get_required(self.properties.get("length"), self, "length")

    @length.setter
    def length(self, v: int) -> None:
        self.properties["length"] = v

    @property
    def classes(self) -> list[Classification]:
        """Get or set the class definitions for the bitfield

        Returns:
            List[Classification]
        """

        return [
            Classification(d)
            for d in cast(
                list[dict[str, Any]],
                get_required(
                    self.properties.get("classes"),
                    self,
                    "classes",
                ),
            )
        ]

    @classes.setter
    def classes(self, v: list[Classification]) -> None:
        self.properties["classes"] = [c.to_dict() for c in v]

    @property
    def roles(self) -> list[str] | None:
        """Get or set the role of the bitfield.

        See `Asset Roles
        <https://github.com/radiantearth/stac-spec/blob/master/item-spec/item-spec.md#asset-roles>`

        Returns:
            Optional[List[str]]
        """
        return self.properties.get("roles")

    @roles.setter
    def roles(self, v: list[str] | None) -> None:
        if v is not None:
            self.properties["roles"] = v
        else:
            self.properties.pop("roles", None)

    @property
    def description(self) -> str | None:
        """Get or set the optional description of a bitfield.

        Returns:
            Optional[str]
        """
        return self.properties.get("description")

    @description.setter
    def description(self, v: str | None) -> None:
        if v is not None:
            self.properties["description"] = v
        else:
            self.properties.pop("description", None)

    @property
    def name(self) -> str | None:
        """Get or set the optional name of the bitfield.

        Returns:
            Optional[str]
        """
        return self.properties.get("name")

    @name.setter
    def name(self, v: str | None) -> None:
        if v is not None:
            self.properties["name"] = v
        else:
            self.properties.pop("name", None)

    def __repr__(self) -> str:
        return (
            f"<Bitfield offset={self.offset} length={self.length} "
            f"classes={self.classes}>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Returns the dictionary encoding of this bitfield

        Returns:
            dict: The serialization of the Bitfield
        """
        return self.properties


class ClassificationExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """An abstract class that can be used to extend the properties of
    :class:`~pystac.Item`, :class:`~pystac.Asset`,
    :class:`~pystac.extensions.raster.RasterBand`, or
    :class:`~pystac.ItemAssetDefinition` with properties from the
    :stac-ext:`Classification Extension <classification>`.  This class is generic
    over the type of STAC object being extended.

    This class is not to be instantiated directly.  One can either directly use the
    subclass corresponding to the object you are extending, or the `ext` class
    method can be used to construct the proper class for you.
    """

    name: Literal["classification"] = "classification"
    properties: dict[str, Any]
    """The :class:`~pystac.Asset` fields, including extension properties."""

    def apply(
        self,
        classes: list[Classification] | None = None,
        bitfields: list[Bitfield] | None = None,
    ) -> None:
        """Applies the classification extension fields to the extended object.

        Note: one may set either the classes or bitfields objects, but not both.

        Args:
            classes: a list of
                :class:`~pystac.extensions.classification.Classification` objects
                describing the various classes in the classification
        """
        assert (
            classes is None
            and bitfields is not None
            or bitfields is None
            and classes is not None
        ), "Must set exactly one of `classes` or `bitfields`"
        if classes:
            self.classes = classes
        if bitfields:
            self.bitfields = bitfields

    @property
    def classes(self) -> list[Classification] | None:
        """Get or set the classes for the base object

        Note: Setting the classes will clear the object's bitfields if they are
        not None

        Returns:
            Optional[List[Classification]]
        """
        return self._get_classes()

    @classes.setter
    def classes(self, v: list[Classification] | None) -> None:
        if self._get_bitfields() is not None:
            self.bitfields = None
        self._set_property(
            CLASSES_PROP, map_opt(lambda classes: [c.to_dict() for c in classes], v)
        )

    def _get_classes(self) -> list[Classification] | None:
        return map_opt(
            lambda classes: [Classification(c) for c in classes],
            self._get_property(CLASSES_PROP, list[dict[str, Any]]),
        )

    @property
    def bitfields(self) -> list[Bitfield] | None:
        """Get or set the bitfields for the base object

        Note: Setting the bitfields will clear the object's classes if they are
        not None

        Returns:
            Optional[List[Bitfield]]
        """
        return self._get_bitfields()

    @bitfields.setter
    def bitfields(self, v: list[Bitfield] | None) -> None:
        if self._get_classes() is not None:
            self.classes = None
        self._set_property(
            BITFIELDS_PROP,
            map_opt(lambda bitfields: [b.to_dict() for b in bitfields], v),
        )

    def _get_bitfields(self) -> list[Bitfield] | None:
        return map_opt(
            lambda bitfields: [Bitfield(b) for b in bitfields],
            self._get_property(BITFIELDS_PROP, list[dict[str, Any]]),
        )

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI_PATTERN.format(version=DEFAULT_VERSION)

    @classmethod
    def get_schema_uris(cls) -> list[str]:
        warnings.warn(
            "get_schema_uris is deprecated and will be removed in v2",
            DeprecationWarning,
        )
        return [SCHEMA_URI_PATTERN.format(version=v) for v in SUPPORTED_VERSIONS]

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> ClassificationExtension[T]:
        """Extends the given STAC object with propertied from the
        :stac-ext:`Classification Extension <classification>`

        This extension can be applied to instances of :class:`~pystac.Item`,
        :class:`~pystac.Asset`,
        :class:`~pystac.ItemAssetDefinition`, or
        :class:`~pystac.extensions.raster.RasterBand`.

        Raises:
            pystac.ExtensionTypeError : If an invalid object type is passed
        """
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(ClassificationExtension[T], ItemClassificationExtension(obj))
        elif isinstance(obj, pystac.Asset):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(ClassificationExtension[T], AssetClassificationExtension(obj))
        elif isinstance(obj, pystac.ItemAssetDefinition):
            cls.ensure_owner_has_extension(obj, add_if_missing)
            return cast(
                ClassificationExtension[T], ItemAssetsClassificationExtension(obj)
            )
        elif isinstance(obj, RasterBand):
            return cast(
                ClassificationExtension[T], RasterBandClassificationExtension(obj)
            )
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesClassificationExtension:
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesClassificationExtension(obj)


class ItemClassificationExtension(ClassificationExtension[pystac.Item]):
    item: pystac.Item

    properties: dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemClassificationExtension Item id={self.item.id}>"


class AssetClassificationExtension(ClassificationExtension[pystac.Asset]):
    asset: pystac.Asset
    asset_href: str
    properties: dict[str, Any]
    additional_read_properties: Iterable[dict[str, Any]] | None

    def __init__(self, asset: pystac.Asset):
        self.asset = asset
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return f"<AssetClassificationExtension Asset href={self.asset_href}>"


class ItemAssetsClassificationExtension(
    ClassificationExtension[pystac.ItemAssetDefinition]
):
    properties: dict[str, Any]
    asset_defn: pystac.ItemAssetDefinition

    def __init__(self, item_asset: pystac.ItemAssetDefinition):
        self.asset_defn = item_asset
        self.properties = item_asset.properties

    def __repr__(self) -> str:
        return (
            f"<ItemAssetsClassificationExtension ItemAssetDefinition={self.asset_defn}"
        )


class RasterBandClassificationExtension(ClassificationExtension[RasterBand]):
    properties: dict[str, Any]
    raster_band: RasterBand

    def __init__(self, raster_band: RasterBand):
        self.raster_band = raster_band
        self.properties = raster_band.properties

    def __repr__(self) -> str:
        return f"<RasterBandClassificationExtension RasterBand={self.raster_band}>"


class SummariesClassificationExtension(SummariesExtension):
    @property
    def classes(self) -> list[Classification] | None:
        return map_opt(
            lambda classes: [Classification(c) for c in classes],
            self.summaries.get_list(CLASSES_PROP),
        )

    @classes.setter
    def classes(self, v: list[Classification] | None) -> None:
        self._set_summary(CLASSES_PROP, map_opt(lambda x: [c.to_dict() for c in x], v))

    @property
    def bitfields(self) -> list[Bitfield] | None:
        return map_opt(
            lambda bitfields: [Bitfield(b) for b in bitfields],
            self.summaries.get_list(BITFIELDS_PROP),
        )

    @bitfields.setter
    def bitfields(self, v: list[Bitfield] | None) -> None:
        self._set_summary(
            BITFIELDS_PROP, map_opt(lambda x: [b.to_dict() for b in x], v)
        )


class ClassificationExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI_PATTERN.format(version=DEFAULT_VERSION)
    prev_extension_ids = {
        SCHEMA_URI_PATTERN.format(version=v)
        for v in SUPPORTED_VERSIONS
        if v != DEFAULT_VERSION
    }
    stac_object_types = {pystac.STACObjectType.ITEM}

    def migrate(
        self, obj: dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        if SCHEMA_URI_PATTERN.format(version="1.0.0") in info.extensions:
            for asset in obj.get("assets", {}).values():
                classification_classes = asset.get(CLASSES_PROP, None)
                if classification_classes is None or not isinstance(
                    classification_classes, list
                ):
                    continue
                for class_object in classification_classes:
                    if "color-hint" in class_object:
                        class_object["color_hint"] = class_object["color-hint"]
                        del class_object["color-hint"]
        super().migrate(obj, version, info)


CLASSIFICATION_EXTENSION_HOOKS: ExtensionHooks = ClassificationExtensionHooks()
