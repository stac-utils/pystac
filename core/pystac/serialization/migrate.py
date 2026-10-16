from __future__ import annotations

import warnings
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeGuard

import pystac
from pystac.serialization.identify import (
    OldExtensionShortIDs,
    STACJSONDescription,
    STACVersionID,
)
from pystac.version import STACVersion

if TYPE_CHECKING:
    from pystac import STACObjectType


def _migrate_catalog(
    d: dict[str, Any], version: STACVersionID, info: STACJSONDescription
) -> None:
    d["type"] = pystac.STACObjectType.CATALOG
    _migrate_license(d)


def _migrate_collection_summaries(
    d: dict[str, Any], version: STACVersionID, info: STACJSONDescription
) -> None:
    if version < "1.0.0-rc.1":
        for prop, summary in d.get("summaries", {}).items():
            if isinstance(summary, dict) and "min" in summary and "max" in summary:
                d["summaries"][prop] = {
                    "minimum": summary["min"],
                    "maximum": summary["max"],
                }


def _migrate_collection(
    d: dict[str, Any], version: STACVersionID, info: STACJSONDescription
) -> None:
    d["type"] = pystac.STACObjectType.COLLECTION
    _migrate_license(d)
    _migrate_collection_summaries(d, version, info)


def _migrate_item(
    d: dict[str, Any], version: STACVersionID, info: STACJSONDescription
) -> None:
    _migrate_license(d["properties"])


def _migrate_license(d: dict[str, Any]) -> None:
    if d.get("license") in ["various", "proprietary"]:
        d["license"] = "other"

    return None


def _migrate_datetime_range(
    d: dict[str, Any], version: STACVersionID, info: STACJSONDescription
) -> set[str] | None:
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


BAND_COMMON_FIELDS = {
    "name",
    "description",
    "nodata",
    "data_type",
    "statistics",
    "unit",
}


def _to_common_band(band: dict[str, Any], prefix: str) -> dict[str, Any]:
    return {
        k if k in BAND_COMMON_FIELDS or ":" in k else prefix + k: v
        for k, v in band.items()
    }


def _is_band_list(value: Any) -> TypeGuard[list[dict[str, Any]]]:
    return isinstance(value, list) and all(isinstance(band, dict) for band in value)


def _band_containers(obj: dict[str, Any]) -> list[dict[str, Any]]:
    if obj.get("type") == pystac.STACObjectType.ITEM:
        return [obj["properties"], *obj.get("assets", {}).values()]
    if obj.get("type") == pystac.STACObjectType.COLLECTION:
        containers = [*obj.get("assets", {}).values()]
        containers.extend(obj.get("item_assets", {}).values())
        if obj.get("summaries") is not None:
            containers.append(obj["summaries"])
        return containers
    return []


def _band_length_mismatch(d: dict[str, Any], bands_prop: str) -> str | None:
    ext_bands = d.get(bands_prop)
    bands = d.get("bands")
    if not ext_bands or not _is_band_list(ext_bands) or bands is None:
        return None
    if len(bands) == len(ext_bands):
        return None
    return f"it has {len(ext_bands)} bands but bands has {len(bands)}"


def _migrate_extension_bands_in(
    d: dict[str, Any], bands_prop: str, prefix: str
) -> None:
    ext_bands = d.get(bands_prop)
    if not _is_band_list(ext_bands):
        return
    bands = d.get("bands")
    if not ext_bands:
        pass
    elif bands is None:
        d["bands"] = [_to_common_band(band, prefix) for band in ext_bands]
    else:
        for band, ext_band in zip(bands, ext_bands):
            for k, v in _to_common_band(ext_band, prefix).items():
                band.setdefault(k, v)
    del d[bands_prop]


def migrate_extension_bands(obj: dict[str, Any], bands_prop: str, prefix: str) -> bool:
    """Moves an extension's v1 band list (e.g. ``eo:bands``) into the STAC 1.1
    ``bands`` field of an Item or Collection dict.

    Applies to Item properties and assets, and to Collection assets,
    ``item_assets`` and ``summaries``. If ``bands`` is not set, it is created from
    the extension's bands; otherwise the two lists are merged by index, and fields
    already on ``bands`` are kept. Fields of the common Band Object (``name``,
    ``description``, ``nodata``, ``data_type``, ``statistics``, ``unit``) and fields
    that already have a prefix are kept as they are; other fields get ``prefix``.
    Empty band lists are removed.

    A band list is left unchanged if it contains anything other than band objects
    (pre-0.9 assets list band indices). If any band list has a different number of
    bands than the ``bands`` next to it, nothing is changed and a warning is
    emitted.

    Args:
        obj : The Item or Collection dict to modify in place.
        bands_prop : The extension's band list field, e.g. ``"eo:bands"``.
        prefix : The extension's field prefix, e.g. ``"eo:"``.

    Returns:
        bool: ``False`` if nothing was changed because of a band count mismatch.
    """
    containers = _band_containers(obj)
    for container in containers:
        if (mismatch := _band_length_mismatch(container, bands_prop)) is not None:
            warnings.warn(f"Not migrating {bands_prop}: {mismatch}")
            return False
    for container in containers:
        _migrate_extension_bands_in(container, bands_prop, prefix)
    return True


def has_extension_fields(obj: dict[str, Any], prefix: str) -> bool:
    """Returns whether an Item or Collection dict has a field starting with
    ``prefix``.

    Looks where the eo v2.0.0 and raster v2.0.0 schemas require one: Item properties
    and assets, and the Collection itself, its assets, ``item_assets`` and
    ``summaries``, including their ``bands``.

    Args:
        obj : The Item or Collection dict.
        prefix : The extension's field prefix, e.g. ``"eo:"``.
    """
    containers = _band_containers(obj)
    if obj.get("type") == pystac.STACObjectType.COLLECTION:
        containers.append(obj)
    for container in containers:
        fields = [container]
        if _is_band_list(bands := container.get("bands")):
            fields.extend(bands)
        if any(k.startswith(prefix) for d in fields for k in d):
            return True
    return False


def _get_object_migrations() -> dict[
    str, Callable[[dict[str, Any], STACVersionID, STACJSONDescription], None]
]:
    return {
        pystac.STACObjectType.CATALOG: _migrate_catalog,
        pystac.STACObjectType.COLLECTION: _migrate_collection,
        pystac.STACObjectType.ITEM: _migrate_item,
    }


def _get_removed_extension_migrations() -> dict[
    str,
    tuple[
        list[STACObjectType] | None,
        None
        | (
            Callable[
                [dict[str, Any], STACVersionID, STACJSONDescription],
                set[str] | None,
            ]
        ),
    ],
]:
    """Handles removed extensions.

    This does not handle renamed extension or extensions that were absorbed
    by other extensions; for instance the FileExtensions handles the migration of
    the previous 'checksum' extension.

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
        # property merging has gone away these extensions are removed
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


def migrate_to_latest(
    json_dict: dict[str, Any], info: STACJSONDescription
) -> dict[str, Any]:
    """Migrates the STAC JSON to the latest version

    Args:
        json_dict : The dict of STAC JSON to identify.
        info : The info from
            :func:`~pystac.serialization.identify_stac_object` that describes
            the STAC object contained in the JSON dict.

    Returns:
        dict: A copy of the dict that is migrated to the latest version (the
        version that is pystac.version.STACVersion.DEFAULT_STAC_VERSION)
    """
    from copy import deepcopy

    result = deepcopy(json_dict)
    version = info.version_range.latest_valid_version()

    object_migrations = _get_object_migrations()
    removed_extension_migrations = _get_removed_extension_migrations()

    if version != STACVersion.DEFAULT_STAC_VERSION:
        object_migrations[info.object_type](result, version, info)
        result["stac_version"] = STACVersion.DEFAULT_STAC_VERSION

    # Ensure stac_extensions property for consistency
    result["stac_extensions"] = result.get("stac_extensions", None) or []

    pystac.EXTENSION_HOOKS.migrate(result, version, info)
    for ext in result["stac_extensions"][:]:
        if ext in removed_extension_migrations:
            object_types, migration_fn = removed_extension_migrations[ext]
            if object_types is None or info.object_type in object_types:
                if migration_fn:
                    migration_fn(result, version, info)
                result["stac_extensions"].remove(ext)

    return result
