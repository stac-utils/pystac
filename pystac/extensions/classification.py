"""Implements the :stac-ext:`Classification <classification>`."""

from __future__ import annotations

import re
from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Pattern,
    TypeVar,
    Union,
    cast,
)

import pystac
import pystac.extensions.item_assets as item_assets
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.extensions.raster import RasterBand
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.utils import get_required, map_opt

T = TypeVar("T", pystac.Item, pystac.Asset, item_assets.AssetDefinition, RasterBand)

SCHEMA_URI_PATTERN: str = (
    "https://stac-extensions.github.io/classification/v{version}/schema.json"
)
DEFAULT_VERSION: str = "1.1.0"
SUPPORTED_VERSIONS: List[str] = ["1.1.0", "1.0.0"]

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

    properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    def apply(
        self,
        value: int,
        description: str,
        name: Optional[str] = None,
        color_hint: Optional[str] = None,
    ) -> None:
        """
        Set the properties for a new Classification.

        Args:
            value: The integer value corresponding to this class
            description: The description of this class
            name: The optional human-readable short name for this class
            color_hint: An optional hexadecimal string-encoded representation of the
                RGB color that is suggested to represent this class (six hexadecimal
                characters, all capitalized)
        """
        self.value = value
        self.name = name
        self.description = description
        self.color_hint = color_hint

        if color_hint is not None:
            match = COLOR_HINT_PATTERN.match(color_hint)
            assert (
                color_hint is None or match is not None and match.group() == color_hint
            ), "Must format color hints as '^([0-9A-F]{6})$'"

        if color_hint is not None:
            match = COLOR_HINT_PATTERN.match(color_hint)
            assert (
                color_hint is None or match is not None and match.group() == color_hint
            ), "Must format color hints as '^([0-9A-F]{6})$'"

    @classmethod
    def create(
        cls,
        value: int,
        description: str,
        name: Optional[str] = None,
        color_hint: Optional[str] = None,
    ) -> Classification:
        """
        Create a new Classification.

        Args:
            value: The integer value corresponding to this class
            name: The human-readable short name for this class
            description: The optional long-form description of this class
            color_hint: An optional hexadecimal string-encoded representation of the
                RGB color that is suggested to represent this class (six hexadecimal
                characters, all capitalized)
        """
        c = cls({})
        c.apply(
            value=value,
            name=name,
            description=description,
            color_hint=color_hint,
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
    def description(self) -> str:
        """Get or set the description of the class

        Returns:
            str
        """
        return get_required(self.properties.get("description"), self, "description")

    @description.setter
    def description(self, v: str) -> None:
        self.properties["description"] = v

    @property
    def name(self) -> Optional[str]:
        """Get or set the name of the class

        Returns:
            Optional[str]
        """
        return self.properties.get("name")

    @name.setter
    def name(self, v: Optional[str]) -> None:
        if v is not None:
            self.properties["name"] = v
        else:
            self.properties.pop("name", None)

    @property
    def color_hint(self) -> Optional[str]:
        """Get or set the optional color hint for this class.

        The color hint must be a six-character string of capitalized hexadecimal
        characters ([0-9A-F]).

        Returns:
            Optional[str]
        """
        return self.properties.get("color-hint")

    @color_hint.setter
    def color_hint(self, v: Optional[str]) -> None:
        if v is not None:
            match = COLOR_HINT_PATTERN.match(v)
            assert (
                v is None or match is not None and match.group() == v
            ), "Must format color hints as '^([0-9A-F]{6})$'"
            self.properties["color-hint"] = v
        else:
            self.properties.pop("color-hint", None)

    def to_dict(self) -> Dict[str, Any]:
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

    properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Any]):
        self.properties = properties

    def apply(
        self,
        offset: int,
        length: int,
        classes: List[Classification],
        roles: Optional[List[str]] = None,
        description: Optional[str] = None,
        name: Optional[str] = None,
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
        assert (
            roles is None or len(roles) > 0
        ), "When set, roles must contain at least one item"

    @classmethod
    def create(
        cls,
        offset: int,
        length: int,
        classes: List[Classification],
        roles: Optional[List[str]] = None,
        description: Optional[str] = None,
        name: Optional[str] = None,
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
    def classes(self) -> List[Classification]:
        """Get or set the class definitions for the bitfield

        Returns:
            List[Classification]
        """

        return [
            Classification(d)
            for d in cast(
                List[Dict[str, Any]],
                get_required(
                    self.properties.get("classes"),
                    self,
                    "classes",
                ),
            )
        ]

    @classes.setter
    def classes(self, v: List[Classification]) -> None:
        self.properties["classes"] = [c.to_dict() for c in v]

    @property
    def roles(self) -> Optional[List[str]]:
        """Get or set the role of the bitfield.

        See `Asset Roles
        <https://github.com/radiantearth/stac-spec/blob/master/item-spec/item-spec.md#asset-roles>`

        Returns:
            Optional[List[str]]
        """
        return self.properties.get("roles")

    @roles.setter
    def roles(self, v: Optional[List[str]]) -> None:
        if v is not None:
            self.properties["roles"] = v
        else:
            self.properties.pop("roles", None)

    @property
    def description(self) -> Optional[str]:
        """Get or set the optional description of a bitfield.

        Returns:
            Optional[str]
        """
        return self.properties.get("description")

    @description.setter
    def description(self, v: Optional[str]) -> None:
        if v is not None:
            self.properties["description"] = v
        else:
            self.properties.pop("description", None)

    @property
    def name(self) -> Optional[str]:
        """Get or set the optional name of the bitfield.

        Returns:
            Optional[str]
        """
        return self.properties.get("name")

    @name.setter
    def name(self, v: Optional[str]) -> None:
        if v is not None:
            self.properties["name"] = v
        else:
            self.properties.pop("name", None)

    def __repr__(self) -> str:
        return (
            f"<Bitfield offset={self.offset} length={self.length} "
            f"classes={self.classes}>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary encoding of this bitfield

        Returns:
            dict: The serialization of the Bitfield
        """
        return self.properties


class ClassificationExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Union[pystac.Item, pystac.Collection]],
):
    """An abstract class that can be used to extend the properties of
    :class:`~pystac.Item`, :class:`~pystac.Asset`,
    :class:`~pystac.extension.raster.RasterBand`, or
    :class:`~pystac.extension.item_assets.AssetDefinition` with properties from the
    :stac-ext:`Classification Extension <classification>`.  This class is generic
    over the type of STAC object being extended.

    This class is not to be instantiated directly.  One can either directly use the
    subclass corresponding to the object you are extending, or the `ext` class
    method can be used to construct the proper class for you.
    """

    properties: Dict[str, Any]
    """The :class:`~pystac.Asset` fields, including extension properties."""

    def apply(
        self,
        classes: Optional[List[Classification]] = None,
        bitfields: Optional[List[Bitfield]] = None,
    ) -> None:
        """Applies the classifiation extension fields to the extended object.

        Note: one may set either the classes or bitfields objects, but not both.

        Args:
            classes: a list of
                :class:`~pystac.extension.classification.Classification` objects
                describing the various classes in the classification
        """
        assert (
            classes is None
            and bitfields is not None
            or bitfields is None
            and classes is not None
        ), "Must set exactly one of `classes` or `bitfields`"
        self.classes = classes
        self.bitfields = bitfields

    @property
    def classes(self) -> Optional[List[Classification]]:
        """Get or set the classes for the base object

        Note: Setting the classes will clear the object's bitfields if they are
        not None

        Returns:
            Optional[List[Classification]]
        """
        return self._get_classes()

    @classes.setter
    def classes(self, v: Optional[List[Classification]]) -> None:
        if self._get_bitfields() is not None:
            self.bitfields = None
        self._set_property(
            CLASSES_PROP, map_opt(lambda classes: [c.to_dict() for c in classes], v)
        )

    def _get_classes(self) -> Optional[List[Classification]]:
        return map_opt(
            lambda classes: [Classification(c) for c in classes],
            self._get_property(CLASSES_PROP, List[Dict[str, Any]]),
        )

    @property
    def bitfields(self) -> Optional[List[Bitfield]]:
        """Get or set the bitfields for the base object

        Note: Setting the bitfields will clear the object's classes if they are
        not None

        Returns:
            Optional[List[Bitfield]]
        """
        return self._get_bitfields()

    @bitfields.setter
    def bitfields(self, v: Optional[List[Bitfield]]) -> None:
        if self._get_classes() is not None:
            self.classes = None
        self._set_property(
            BITFIELDS_PROP,
            map_opt(lambda bitfields: [b.to_dict() for b in bitfields], v),
        )

    def _get_bitfields(self) -> Optional[List[Bitfield]]:
        return map_opt(
            lambda bitfields: [Bitfield(b) for b in bitfields],
            self._get_property(BITFIELDS_PROP, List[Dict[str, Any]]),
        )

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI_PATTERN.format(version=DEFAULT_VERSION)

    @classmethod
    def get_schema_uris(cls) -> List[str]:
        return [SCHEMA_URI_PATTERN.format(version=v) for v in SUPPORTED_VERSIONS]

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> ClassificationExtension[T]:
        """Extends the given STAC object with propertied from the
        :stac-ext:`Classification Extension <classification>`

        This extension can be applied to instances of :class:`~pystac.Item`,
        :class:`~pystac.Asset`,
        :class:`~pystac.extensions.item_assets.AssetDefinition`, or
        :class:`~pystac.extension.raster.RasterBand`.

        Raises:
            pystac.ExtensionTypeError : If an invalid object type is passed
        """
        if isinstance(obj, pystac.Item):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(ClassificationExtension[T], ItemClassificationExtension(obj))
        elif isinstance(obj, pystac.Asset):
            cls.validate_owner_has_extension(obj, add_if_missing)
            return cast(ClassificationExtension[T], AssetClassificationExtension(obj))
        elif isinstance(obj, item_assets.AssetDefinition):
            cls.validate_has_extension(
                cast(Union[pystac.Item, pystac.Collection], obj.owner), add_if_missing
            )
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
        cls.validate_has_extension(obj, add_if_missing)
        return SummariesClassificationExtension(obj)


class ItemClassificationExtension(ClassificationExtension[pystac.Item]):
    item: pystac.Item

    properties: Dict[str, Any]

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemClassificationExtension Item id={self.item.id}>"


class AssetClassificationExtension(ClassificationExtension[pystac.Asset]):
    asset: pystac.Asset
    asset_href: str
    properties: Dict[str, Any]
    additional_read_properties: Optional[Iterable[Dict[str, Any]]]

    def __init__(self, asset: pystac.Asset):
        self.asset = asset
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return f"<AssetClassificationExtension Asset href={self.asset_href}>"


class ItemAssetsClassificationExtension(
    ClassificationExtension[item_assets.AssetDefinition]
):
    properties: Dict[str, Any]
    asset_defn: item_assets.AssetDefinition

    def __init__(self, item_asset: item_assets.AssetDefinition):
        self.asset_defn = item_asset
        self.properties = item_asset.properties

    def __repr__(self) -> str:
        return f"<ItemAssetsClassificationExtension AssetDefinition={self.asset_defn}"


class RasterBandClassificationExtension(ClassificationExtension[RasterBand]):
    properties: Dict[str, Any]
    raster_band: RasterBand

    def __init__(self, raster_band: RasterBand):
        self.raster_band = raster_band
        self.properties = raster_band.properties

    def __repr__(self) -> str:
        return f"<RasterBandClassificationExtension RasterBand={self.raster_band}>"


class SummariesClassificationExtension(SummariesExtension):
    @property
    def classes(self) -> Optional[List[Classification]]:
        return map_opt(
            lambda classes: [Classification(c) for c in classes],
            self.summaries.get_list(CLASSES_PROP),
        )

    @classes.setter
    def classes(self, v: Optional[List[Classification]]) -> None:
        self._set_summary(CLASSES_PROP, map_opt(lambda x: [c.to_dict() for c in x], v))

    @property
    def bitfields(self) -> Optional[List[Bitfield]]:
        return map_opt(
            lambda bitfields: [Bitfield(b) for b in bitfields],
            self.summaries.get_list(BITFIELDS_PROP),
        )

    @bitfields.setter
    def bitfields(self, v: Optional[List[Bitfield]]) -> None:
        self._set_summary(
            BITFIELDS_PROP, map_opt(lambda x: [b.to_dict() for b in x], v)
        )


class ClassificationExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI_PATTERN.format(version=DEFAULT_VERSION)
    prev_extension_ids = set(ClassificationExtension.get_schema_uris()) - set(
        [ClassificationExtension.get_schema_uri()]
    )
    stac_object_types = {pystac.STACObjectType.ITEM}

    def migrate(
        self, obj: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        super().migrate(obj, version, info)


CLASSIFICATION_EXTENSION_HOOKS: ExtensionHooks = ClassificationExtensionHooks()
