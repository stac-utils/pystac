from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING, Tuple

import pystac
from pystac.version import STACVersion
from pystac.serialization.identify import (
    OldExtensionShortIDs,
    STACJSONDescription,
    STACVersionID,
)

if TYPE_CHECKING:
    from pystac import STACObjectType as STACObjectType_Type


def _migrate_catalog(
    d: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
) -> None:
    d["type"] = pystac.STACObjectType.CATALOG


def _migrate_collection_summaries(
    d: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
) -> None:
    if version < "1.0.0-rc.1":
        for prop, summary in d.get("summaries", {}).items():
            if isinstance(summary, dict) and "min" in summary and "max" in summary:
                d["summaries"][prop] = {
                    "minimum": summary["min"],
                    "maximum": summary["max"],
                }


def _migrate_collection(
    d: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
) -> None:
    d["type"] = pystac.STACObjectType.COLLECTION
    _migrate_collection_summaries(d, version, info)


def _migrate_item(
    d: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
) -> None:
    # No migrations necessary for supported STAC versions (>=0.8)
    pass


# Extensions
def _migrate_item_assets(
    d: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
) -> Optional[Set[str]]:
    if version < "1.0.0-beta.2":
        if info.object_type == pystac.STACObjectType.COLLECTION:
            if "assets" in d:
                d["item_assets"] = d["assets"]
                del d["assets"]
    return None


def _migrate_datetime_range(
    d: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
) -> Optional[Set[str]]:
    if version < "0.9":
        # Datetime range was removed
        if (
            "dtr:start_datetime" in d["properties"]
            and "start_datetime" not in d["properties"]
        ):
            d["properties"]["start_datetime"] = d["properties"]["dtr:start_datetime"]
            del d["properties"]["dtr:start_datetime"]

        if (
            "dtr:end_datetime" in d["properties"]
            and "end_datetime" not in d["properties"]
        ):
            d["properties"]["end_datetime"] = d["properties"]["dtr:end_datetime"]
            del d["properties"]["dtr:end_datetime"]

    return None


def _get_object_migrations() -> Dict[
    str, Callable[[Dict[str, Any], STACVersionID, STACJSONDescription], None]
]:
    return {
        pystac.STACObjectType.CATALOG: _migrate_catalog,
        pystac.STACObjectType.COLLECTION: _migrate_collection,
        pystac.STACObjectType.ITEM: _migrate_item,
    }


def _get_removed_extension_migrations() -> Dict[
    str,
    Tuple[
        Optional[List["STACObjectType_Type"]],
        Optional[
            Callable[
                [Dict[str, Any], STACVersionID, STACJSONDescription], Optional[Set[str]]
            ]
        ],
    ],
]:
    """Handles removed extensions.

    This does not handle renamed extension or extensions that were absorbed
    by other extensions; for instance the FileExtensions handles the migration of
    the since replaced 'checksum' extension.

    Dict of the extension ID to a tuple of optional list of STACObjectType which it was
    removed for (or None if removed from all), and an optional migrate function
    that can modify the object in case the extension was removed but the properties
    were moved.
    """
    return {
        # -- Removed in 1.0
        # assets in collections became a core property
        OldExtensionShortIDs.COLLECTION_ASSETS.value: (None, None),
        # Extensions that were placed on Collections that applied to
        # the 'commons' properties of their Items, but since the commons
        # property merging has went away these extensions are removed
        # from the collection. Note that a migrated Collection may still
        # have a "properties" in extra_fields with the extension fields.
        OldExtensionShortIDs.EO.value: ([pystac.STACObjectType.COLLECTION], None),
        OldExtensionShortIDs.FILE.value: ([pystac.STACObjectType.COLLECTION], None),
        OldExtensionShortIDs.LABEL.value: ([pystac.STACObjectType.COLLECTION], None),
        OldExtensionShortIDs.POINTCLOUD.value: (
            [pystac.STACObjectType.COLLECTION],
            None,
        ),
        OldExtensionShortIDs.PROJECTION.value: (
            [pystac.STACObjectType.COLLECTION],
            None,
        ),
        OldExtensionShortIDs.SAR.value: ([pystac.STACObjectType.COLLECTION], None),
        OldExtensionShortIDs.SAT.value: ([pystac.STACObjectType.COLLECTION], None),
        OldExtensionShortIDs.TIMESTAMPS.value: (
            [pystac.STACObjectType.COLLECTION],
            None,
        ),
        OldExtensionShortIDs.VIEW.value: ([pystac.STACObjectType.COLLECTION], None),
        # tiled-assets was never a fully published extension;
        # remove reference to the pre-1.0 RC short ID
        OldExtensionShortIDs.TILED_ASSETS.value: (None, None),
        # Single File STAC is a removed concept; is being reworked as of
        # STAC 1.0.0-RC.3. Remove short ID from PySTAC as it's unsupported
        OldExtensionShortIDs.SINGLE_FILE_STAC.value: (None, None),
        # -- Removed in 0.9.0
        "dtr": (None, _migrate_datetime_range),
        "datetime-range": (None, _migrate_datetime_range),
        "commons": (None, None),
    }


# TODO: Item Assets
def _get_extension_renames() -> Dict[str, str]:
    return {"asset": "item-assets"}


def migrate_to_latest(
    json_dict: Dict[str, Any], info: STACJSONDescription
) -> Dict[str, Any]:
    """Migrates the STAC JSON to the latest version

    Args:
        json_dict : The dict of STAC JSON to identify.
        info : The info from
            :func:`~pystac.serialization.identify.identify_stac_object` that describes
            the STAC object contained in the JSON dict.

    Returns:
        dict: A copy of the dict that is migrated to the latest version (the
        version that is pystac.version.STACVersion.DEFAULT_STAC_VERSION)
    """
    result = deepcopy(json_dict)
    version = info.version_range.latest_valid_version()

    object_migrations = _get_object_migrations()
    removed_extension_migrations = _get_removed_extension_migrations()

    if version != STACVersion.DEFAULT_STAC_VERSION:
        object_migrations[info.object_type](result, version, info)
        if "stac_extensions" not in result:
            # Force stac_extensions property, as it makes
            # downstream migration less complex
            result["stac_extensions"] = []
        pystac.EXTENSION_HOOKS.migrate(result, version, info)

        for ext in result["stac_extensions"][:]:
            if ext in removed_extension_migrations:
                object_types, migration_fn = removed_extension_migrations[ext]
                if object_types is None or info.object_type in object_types:
                    if migration_fn:
                        migration_fn(result, version, info)
                    result["stac_extensions"].remove(ext)

        result["stac_version"] = STACVersion.DEFAULT_STAC_VERSION
    else:
        # Ensure stac_extensions property for consistency
        if "stac_extensions" not in result:
            result["stac_extensions"] = []

    return result
