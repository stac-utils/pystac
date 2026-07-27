from __future__ import annotations

from enum import Enum
from functools import total_ordering
from typing import TYPE_CHECKING, Any

import pystac
from pystac.version import STACVersion

if TYPE_CHECKING:
    from pystac.stac_object import STACObjectType


class OldExtensionShortIDs(Enum):
    """Enumerates the IDs of common extensions."""

    CHECKSUM = "checksum"
    COLLECTION_ASSETS = "collection-assets"
    DATACUBE = "datacube"  # TODO
    EO = "eo"
    ITEM_ASSETS = "item-assets"  # TODO
    LABEL = "label"
    POINTCLOUD = "pointcloud"
    PROJECTION = "projection"
    SAR = "sar"
    SAT = "sat"
    SCIENTIFIC = "scientific"
    SINGLE_FILE_STAC = "single-file-stac"
    TILED_ASSETS = "tiled-assets"
    TIMESTAMPS = "timestamps"
    VERSION = "version"
    VIEW = "view"
    FILE = "file"


@total_ordering
class STACVersionID:
    """Defines STAC versions in an object that is orderable based on version number.
    For instance, ``1.0.0-beta.2 < 1.0.0``
    """

    version_string: str
    version_core: str
    version_prerelease: str | None

    def __init__(self, version_string: str) -> None:
        self.version_string = version_string

        # Account for RC or beta releases in version
        version_parts = version_string.split("-")
        self.version_core = version_parts[0]
        if len(version_parts) == 1:
            self.version_prerelease = None
        else:
            self.version_prerelease = "-".join(version_parts[1:])

    def __str__(self) -> str:
        return self.version_string

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, STACVersionID):
            other = STACVersionID(str(other))
        return str(self) == str(other)

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, STACVersionID):
            other = STACVersionID(str(other))
        if self.version_core < other.version_core:
            return True
        elif self.version_core > other.version_core:
            return False
        else:
            return self.version_prerelease is not None and (
                other.version_prerelease is None
                or other.version_prerelease > self.version_prerelease
            )


class STACVersionRange:
    """Defines a range of STAC versions."""

    _min_version: STACVersionID
    _max_version: STACVersionID

    def __init__(
        self,
        min_version: str | STACVersionID = "0.8.0",
        max_version: str | STACVersionID | None = None,
    ):
        if isinstance(min_version, str):
            self.min_version = STACVersionID(min_version)
        else:
            self.min_version = min_version

        if max_version is None:
            self.max_version = STACVersionID(STACVersion.DEFAULT_STAC_VERSION)
        else:
            if isinstance(max_version, str):
                self.max_version = STACVersionID(max_version)
            else:
                self.max_version = max_version

    @property
    def min_version(self) -> STACVersionID:
        return self._min_version

    @min_version.setter
    def min_version(self, v: str | STACVersionID) -> None:
        if isinstance(v, str):
            v = STACVersionID(v)
        self._min_version = v

    @property
    def max_version(self) -> STACVersionID:
        return self._max_version

    @max_version.setter
    def max_version(self, v: str | STACVersionID) -> None:
        if isinstance(v, str):
            v = STACVersionID(v)
        self._max_version = v

    def set_min(self, v: str | STACVersionID) -> None:
        if isinstance(v, str):
            v = STACVersionID(v)
        if self.min_version < v:
            if v < self.max_version:
                self.min_version = v
            else:
                self.min_version = self.max_version

    def set_max(self, v: str | STACVersionID) -> None:
        if isinstance(v, str):
            v = STACVersionID(v)
        if v < self.max_version:
            if self.min_version < v:
                self.max_version = v
            else:
                self.max_version = self.min_version

    def set_to_single(self, v: str | STACVersionID) -> None:
        self.set_min(v)
        self.set_max(v)

    def latest_valid_version(self) -> STACVersionID:
        return self.max_version

    def contains(self, v: str | STACVersionID) -> bool:
        if isinstance(v, str):
            v = STACVersionID(v)
        return self.min_version <= v <= self.max_version

    def is_single_version(self) -> bool:
        return self.min_version >= self.max_version

    def is_earlier_than(self, v: str | STACVersionID) -> bool:
        if isinstance(v, str):
            v = STACVersionID(v)
        return self.max_version < v

    def is_later_than(self, v: str | STACVersionID) -> bool:
        if isinstance(v, str):
            v = STACVersionID(v)
        return v < self.min_version

    def __repr__(self) -> str:
        return f"<VERSIONS {self.min_version}-{self.max_version}>"


class STACJSONDescription:
    """Describes the STAC object information for a STAC object represented in JSON

    Args:
        object_type : Describes the STAC object type. One of
            :class:`~pystac.STACObjectType`.
        version_range : The STAC version range that describes what
            has been identified as potential valid versions of the stac object.
        extensions : List of extension schema URIs for extensions this
            object implements
    """

    object_type: STACObjectType
    """Describes the STAC object type. One of :class:`~pystac.STACObjectType`."""

    version_range: STACVersionRange
    """The STAC version range that describes what has been identified
    as potential valid versions of the :class:`~pystac.STACObject`."""

    extensions: list[str]
    """List of extension schema URIs for extensions this object implements"""

    def __init__(
        self,
        object_type: STACObjectType,
        version_range: STACVersionRange,
        extensions: list[str],
    ) -> None:
        self.object_type = object_type
        self.version_range = version_range
        self.extensions = extensions

    def __repr__(self) -> str:
        return "<{} {} ext={}>".format(
            self.object_type, self.version_range, ",".join(self.extensions)
        )


def identify_stac_object_type(json_dict: dict[str, Any]) -> STACObjectType | None:
    """Determines the STACObjectType of the provided JSON dict. If the JSON dict does
    not represent a STAC object, returns ``None``.

    Will first try to identify the object using ``"type"`` field as described in the
    guidelines in :stac-spec:`How to Differentiate STAC Files
    <best-practices.md#how-to-differentiate-stac-files>`. If this fails, will fall back
    to using the pre-1.0 heuristic described in `this issue
    <https://github.com/radiantearth/stac-spec/issues/889#issuecomment-684529444>`__

    Args:
        json_dict : The dict of JSON to identify.
    """
    stac_version = (
        STACVersionID(json_dict["stac_version"])
        if "stac_version" in json_dict
        else None
    )
    obj_type = json_dict.get("type")

    # Try to identify using 'type' property for v1.0.0-rc.1 and higher
    introduced_type_attribute = STACVersionID("1.0.0-rc.1")
    if stac_version is not None and stac_version >= introduced_type_attribute:
        # Since v1.0.0-rc.1 requires a "type" field for all STAC objects, any object
        # that is missing this attribute is not a valid STAC object.
        if obj_type is None:
            return None

        # Try to match the "type" attribute
        if obj_type == pystac.STACObjectType.CATALOG:
            return pystac.STACObjectType.CATALOG
        elif obj_type == pystac.STACObjectType.COLLECTION:
            return pystac.STACObjectType.COLLECTION
        elif obj_type == pystac.STACObjectType.ITEM:
            return pystac.STACObjectType.ITEM
        else:
            return None

    # For pre-1.0 objects for version 0.8.* or later 'stac_version' must be present
    if stac_version is not None:
        # Pre-1.0 STAC objects with 'type' == "Feature" are Items
        if obj_type == "Feature":
            return pystac.STACObjectType.ITEM
        # Anything else with a 'type' field is not a STAC object
        if obj_type is not None:
            return None

        # Collections will contain either an 'extent' or a 'license' (or both)
        if "extent" in json_dict or "license" in json_dict:
            return pystac.STACObjectType.COLLECTION
        # Everything else that has a stac_version is a Catalog
        else:
            return pystac.STACObjectType.CATALOG

    return None


def identify_stac_object(json_dict: dict[str, Any]) -> STACJSONDescription:
    """Determines the STACJSONDescription of the provided JSON dict.

    Args:
        json_dict : The dict of STAC JSON to identify.

    Returns:
        STACJSONDescription: The description of the STAC object serialized in the
        given dict.
    """
    object_type = identify_stac_object_type(json_dict)

    if object_type is None:
        extra_message = f"'type' attribute is {json_dict.get('type', 'not set')}"
        raise pystac.STACTypeError(json_dict, pystac.STACObject, extra_message)

    version_range = STACVersionRange()

    stac_version = json_dict.get("stac_version")
    stac_extensions = json_dict.get("stac_extensions", None)

    if stac_version is None:
        version_range.set_min("0.8.0")
    else:
        version_range.set_to_single(stac_version)

    if stac_extensions is not None:
        version_range.set_min("0.8.0")

    if stac_extensions is None:
        stac_extensions = []

    return STACJSONDescription(object_type, version_range, stac_extensions)
