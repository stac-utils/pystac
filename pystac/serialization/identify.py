from enum import Enum
from functools import total_ordering
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING, Union, cast

import pystac
from pystac.version import STACVersion

if TYPE_CHECKING:
    from pystac.stac_object import STACObjectType as STACObjectType_Type


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

    def __init__(
        self,
        min_version: Union[str, STACVersionID] = "0.4.0",
        max_version: Optional[Union[str, STACVersionID]] = None,
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

    def set_min(self, v: STACVersionID) -> None:
        if self.min_version < v:
            if v < self.max_version:
                self.min_version = v
            else:
                self.min_version = self.max_version

    def set_max(self, v: STACVersionID) -> None:
        if v < self.max_version:
            if self.min_version < v:
                self.max_version = v
            else:
                self.max_version = self.min_version

    def set_to_single(self, v: STACVersionID) -> None:
        self.set_min(v)
        self.set_max(v)

    def latest_valid_version(self) -> STACVersionID:
        return self.max_version

    def contains(self, v: Union[str, STACVersionID]) -> bool:
        if isinstance(v, str):
            v = STACVersionID(v)
        return self.min_version <= v and v <= self.max_version  # type:ignore

    def is_single_version(self) -> bool:
        return self.min_version >= self.max_version  # type:ignore

    def is_earlier_than(self, v: Union[str, STACVersionID]) -> bool:
        if isinstance(v, str):
            v = STACVersionID(v)
        return self.max_version < v

    def is_later_than(self, v: Union[str, STACVersionID]) -> bool:
        if isinstance(v, str):
            v = STACVersionID(v)
        return v < self.min_version

    def __repr__(self) -> str:
        return "<VERSIONS {}-{}>".format(self.min_version, self.max_version)


class STACJSONDescription:
    """Describes the STAC object information for a STAC object represented in JSON

    Attributes:
        object_type : Describes the STAC object type. One of
            :class:`~pystac.STACObjectType`.
        version_range : The STAC version range that describes what
            has been identified as potential valid versions of the stac object.
        extensions : List of extension schema URIs for extensions this
            object implements
    """

    def __init__(
        self,
        object_type: "STACObjectType_Type",
        version_range: STACVersionRange,
        extensions: Set[str],
    ) -> None:
        self.object_type = object_type
        self.version_range = version_range
        self.extensions = extensions

    def __repr__(self) -> str:
        return "<{} {} ext={}>".format(
            self.object_type, self.version_range, ",".join(self.extensions)
        )


def _identify_stac_extensions(
    object_type: str, d: Dict[str, Any], version_range: STACVersionRange
) -> List[str]:
    """Identifies extensions for STAC Objects that don't list their
    extensions in a 'stac_extensions' property.

    Returns a list of stac_extensions. May mutate the version_range to update
    min or max version.
    """
    stac_extensions: Set[str] = set([])

    # assets (collection assets)

    if object_type == pystac.STACObjectType.ITEMCOLLECTION:
        if "assets" in d:
            stac_extensions.add("assets")
            version_range.set_min(STACVersionID("0.8.0"))

    # checksum
    if "links" in d:
        found_checksum = False
        for link in d["links"]:
            link_props = cast(Dict[str, Any], link).keys()

            if any(prop.startswith("checksum:") for prop in link_props):
                found_checksum = True
                stac_extensions.add(OldExtensionShortIDs.CHECKSUM.value)
        if not found_checksum:
            if "assets" in d:
                for asset in d["assets"].values():
                    asset_props = cast(Dict[str, Any], asset).keys()
                    if any(prop.startswith("checksum:") for prop in asset_props):
                        found_checksum = True
                        stac_extensions.add(OldExtensionShortIDs.CHECKSUM.value)
        if found_checksum:
            version_range.set_min(STACVersionID("0.6.2"))

    # datacube
    if object_type == pystac.STACObjectType.ITEM:
        if any(k.startswith("cube:") for k in cast(Dict[str, Any], d["properties"])):
            stac_extensions.add(OldExtensionShortIDs.DATACUBE.value)
            version_range.set_min(STACVersionID("0.6.1"))

    # datetime-range (old extension)
    if object_type == pystac.STACObjectType.ITEM:
        if "dtr:start_datetime" in d["properties"]:
            stac_extensions.add("datetime-range")
            version_range.set_min(STACVersionID("0.6.0"))

    # eo
    if object_type == pystac.STACObjectType.ITEM:
        if any(k.startswith("eo:") for k in cast(Dict[str, Any], d["properties"])):
            stac_extensions.add(OldExtensionShortIDs.EO.value)
            if "eo:epsg" in d["properties"]:
                if d["properties"]["eo:epsg"] is None:
                    version_range.set_min(STACVersionID("0.6.1"))
            if "eo:crs" in d["properties"]:
                version_range.set_max(STACVersionID("0.4.1"))
            if "eo:constellation" in d["properties"]:
                version_range.set_min(STACVersionID("0.6.0"))
        if "eo:bands" in d:
            stac_extensions.add(OldExtensionShortIDs.EO.value)
            version_range.set_max(STACVersionID("0.5.2"))

    # pointcloud
    if object_type == pystac.STACObjectType.ITEM:
        if any(k.startswith("pc:") for k in cast(Dict[str, Any], d["properties"])):
            stac_extensions.add(OldExtensionShortIDs.POINTCLOUD.value)
            version_range.set_min(STACVersionID("0.6.2"))

    # sar
    if object_type == pystac.STACObjectType.ITEM:
        if any(k.startswith("sar:") for k in cast(Dict[str, Any], d["properties"])):
            stac_extensions.add(OldExtensionShortIDs.SAR.value)
            version_range.set_min(STACVersionID("0.6.2"))
            if version_range.contains("0.6.2"):
                for prop in [
                    "sar:absolute_orbit",
                    "sar:resolution",
                    "sar:pixel_spacing",
                    "sar:looks",
                ]:
                    if prop in d["properties"]:
                        if isinstance(d["properties"][prop], list):
                            version_range.set_max(STACVersionID("0.6.2"))
            if version_range.contains("0.7.0"):
                for prop in [
                    "sar:incidence_angle",
                    "sar:relative_orbit",
                    "sar:observation_direction",
                    "sar:resolution_range",
                    "sar:resolution_azimuth",
                    "sar:pixel_spacing_range",
                    "sar:pixel_spacing_azimuth",
                    "sar:looks_range",
                    "sar:looks_azimuth",
                    "sar:looks_equivalent_number",
                ]:
                    if prop in d["properties"]:
                        version_range.set_min(STACVersionID("0.7.0"))
                if "sar:absolute_orbit" in d["properties"] and not isinstance(
                    d["properties"]["sar:absolute_orbit"], list
                ):
                    version_range.set_min(STACVersionID("0.7.0"))
            if "sar:off_nadir" in d["properties"]:
                version_range.set_max(STACVersionID("0.6.2"))

    # scientific
    if (
        object_type == pystac.STACObjectType.ITEM
        or object_type == pystac.STACObjectType.COLLECTION
    ):
        if "properties" in d:
            prop_keys = cast(Dict[str, Any], d["properties"]).keys()
            if any(k.startswith("sci:") for k in prop_keys):
                stac_extensions.add(OldExtensionShortIDs.SCIENTIFIC.value)
                version_range.set_min(STACVersionID("0.6.0"))

    # Single File STAC
    if object_type == pystac.STACObjectType.ITEMCOLLECTION:
        if "collections" in d:
            stac_extensions.add(OldExtensionShortIDs.SINGLE_FILE_STAC.value)
            version_range.set_min(STACVersionID("0.8.0"))
            if "stac_extensions" not in d:
                version_range.set_max(STACVersionID("0.8.1"))

    return list(stac_extensions)


def identify_stac_object_type(
    json_dict: Dict[str, Any]
) -> Optional["STACObjectType_Type"]:
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
    # Try to identify using 'type' property, if present
    if "type" in json_dict:
        # Try to find 'type' property in known STACObjectType values
        for t in pystac.STACObjectType:
            if json_dict["type"].lower() == t.value.lower():
                return t

    obj_type = json_dict.get("type")

    # For pre-1.0 objects for version 0.8.* or later 'stac_version' must be present,
    # except for in ItemCollections (which are handled in the else clause)
    if "stac_version" in json_dict:
        # Pre-1.0 STAC objects with 'type' == "Feature" are Items
        if obj_type == "Feature":
            return pystac.STACObjectType.ITEM
        # Pre-1.0 STAC objects with 'type' == "FeatureCollection" are ItemCollections
        if obj_type == "FeatureCollection":
            return pystac.STACObjectType.ITEMCOLLECTION
        # Anything else with a 'type' field is not a STAC object
        if obj_type is not None:
            return None

        # Collections will contain either an 'extent' or a 'license' (or both)
        if "extent" in json_dict or "license" in json_dict:
            return pystac.STACObjectType.COLLECTION
        # Everything else that has a stac_version is a Catalog
        else:
            return pystac.STACObjectType.CATALOG
    else:
        # Prior to STAC 0.9 ItemCollections did not have a stac_version field and could
        # only be identified by the fact that all of their 'features' are STAC Items
        if obj_type == "FeatureCollection":
            if all(
                identify_stac_object_type(feat) == pystac.STACObjectType.ITEM
                for feat in json_dict.get("features", [])
            ):
                return pystac.STACObjectType.ITEMCOLLECTION
        return None


def identify_stac_object(json_dict: Dict[str, Any]) -> STACJSONDescription:
    """Determines the STACJSONDescription of the provided JSON dict.

    Args:
        json_dict : The dict of STAC JSON to identify.

    Returns:
        STACJSONDescription: The description of the STAC object serialized in the
        given dict.
    """
    object_type = identify_stac_object_type(json_dict)

    if object_type is None:
        raise pystac.STACTypeError("JSON does not represent a STAC object.")

    version_range = STACVersionRange()

    stac_version = json_dict.get("stac_version")
    stac_extensions = json_dict.get("stac_extensions", None)

    if stac_version is None:
        version_range.set_min(STACVersionID("0.8.0"))
    else:
        version_range.set_to_single(stac_version)

    if stac_extensions is not None:
        version_range.set_min(STACVersionID("0.8.0"))

    if stac_extensions is None:
        # If this is post-0.8, we can assume there are no extensions
        # if the stac_extensions property doesn't exist for everything
        # but ItemCollection (except after 0.9.0, when ItemCollection also got
        # the stac_extensions property).
        if (
            object_type == pystac.STACObjectType.ITEMCOLLECTION
            and not version_range.is_later_than("0.8.1")
        ):
            stac_extensions = _identify_stac_extensions(
                object_type, json_dict, version_range
            )
        else:
            stac_extensions = []

        # Between 1.0.0-beta.2 and 1.0.0-RC1, STAC extensions changed from
        # being split between 'common' and custom extensions, with common
        # extensions having short names that were used in the stac_extensions
        # property list, to being mostly externalized from the core spec and
        # always identified with the schema URI as the identifier. This
        # code translates the short name IDs used pre-1.0.0-RC1 to the
        # relevant extension schema uri identifier.

    return STACJSONDescription(object_type, version_range, set(stac_extensions))
