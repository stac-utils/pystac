from __future__ import annotations

import warnings
from collections.abc import Callable, Iterable, Iterator
from collections.abc import Set as AbstractSet
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

YIELDING_BAND_FIELDS: dict[str, AbstractSet[str]] = {"raster:bands": {"name"}}
"""Fields of an extension's v1 band list that are dropped, with a warning, where
``bands`` or another extension's band list has a different value."""


def _to_common_band(
    band: dict[str, Any], prefix: str, fields: AbstractSet[str]
) -> dict[str, Any]:
    return {prefix + k if k in fields else k: v for k, v in band.items()}


def _is_band_list(value: Any) -> TypeGuard[list[dict[str, Any]]]:
    return isinstance(value, list) and all(isinstance(band, dict) for band in value)


def _is_subset(band: dict[str, Any], other: dict[str, Any]) -> bool:
    return all(k in other and other[k] == v for k, v in band.items())


def _conflicts(
    band: dict[str, Any], other: dict[str, Any], keys: Iterable[str]
) -> list[str]:
    return [k for k in keys if k in band and k in other and band[k] != other[k]]


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


def _other_band_lists(
    d: dict[str, Any], bands_prop: str
) -> Iterator[tuple[str, list[dict[str, Any]]]]:
    for k, v in d.items():
        if k != bands_prop and (k == "bands" or k.endswith(":bands")):
            if v and _is_band_list(v):
                yield k, v


def _band_list_problem(
    d: dict[str, Any], bands_prop: str, prefix: str, fields: AbstractSet[str]
) -> str | None:
    ext_bands = d.get(bands_prop)
    if not ext_bands or not _is_band_list(ext_bands):
        return None
    for other_prop, other in _other_band_lists(d, bands_prop):
        if len(other) != len(ext_bands):
            return f"it has {len(ext_bands)} bands but {other_prop} has {len(other)}"
        yielding = {
            *YIELDING_BAND_FIELDS.get(bands_prop, ()),
            *YIELDING_BAND_FIELDS.get(other_prop, ()),
        }
        for ext_band, band in zip(ext_bands, other):
            converted = _to_common_band(ext_band, prefix, fields)
            keys: Iterable[str] = converted
            if other_prop != "bands":
                keys = [k for k in converted if k in BAND_COMMON_FIELDS or ":" in k]
            keys = [k for k in keys if k not in yielding]
            if conflicts := _conflicts(converted, band, keys):
                return f"{other_prop} has different values for {', '.join(conflicts)}"
    return None


def _yielded_fields(
    d: dict[str, Any], bands_prop: str, prefix: str, fields: AbstractSet[str]
) -> dict[int, set[str]]:
    yielding = YIELDING_BAND_FIELDS.get(bands_prop, set())
    ext_bands = d.get(bands_prop)
    yielded: dict[int, set[str]] = {}
    if not yielding or not ext_bands or not _is_band_list(ext_bands):
        return yielded
    for other_prop, other in _other_band_lists(d, bands_prop):
        for i, (ext_band, band) in enumerate(zip(ext_bands, other)):
            converted = _to_common_band(ext_band, prefix, fields)
            if conflicts := _conflicts(converted, band, yielding):
                yielded.setdefault(i, set()).update(conflicts)
                warnings.warn(
                    f"Dropping {', '.join(conflicts)} of {bands_prop}: "
                    f"{other_prop} has a different value"
                )
    return yielded


def _item_bands_problem(
    obj: dict[str, Any], bands_prop: str, prefix: str, fields: AbstractSet[str]
) -> str | None:
    properties = obj["properties"]
    item_bands = properties.get(bands_prop)
    if not item_bands or not _is_band_list(item_bands) or "bands" in properties:
        return None
    asset_bands: list[dict[str, Any]] = []
    for asset in obj.get("assets", {}).values():
        if _is_band_list(ext_bands := asset.get(bands_prop)):
            asset_bands.extend(_to_common_band(b, prefix, fields) for b in ext_bands)
        if _is_band_list(bands := asset.get("bands")):
            asset_bands.extend(bands)
    for band in item_bands:
        converted = _to_common_band(band, prefix, fields)
        if not any(_is_subset(converted, asset_band) for asset_band in asset_bands):
            return "the Item properties have bands that no asset has"
    return None


def _migrate_extension_bands_in(
    d: dict[str, Any], bands_prop: str, prefix: str, fields: AbstractSet[str]
) -> None:
    ext_bands = d.get(bands_prop)
    if not _is_band_list(ext_bands):
        return
    yielded = _yielded_fields(d, bands_prop, prefix, fields)
    converted = [
        {
            k: v
            for k, v in _to_common_band(band, prefix, fields).items()
            if k not in yielded.get(i, ())
        }
        for i, band in enumerate(ext_bands)
    ]
    bands = d.get("bands")
    if not ext_bands:
        pass
    elif bands is None:
        d["bands"] = converted
    else:
        for band, new_band in zip(bands, converted):
            band.update(new_band)
    del d[bands_prop]


def migrate_extension_bands(
    obj: dict[str, Any], bands_prop: str, prefix: str, fields: AbstractSet[str]
) -> bool:
    """Moves an extension's v1 band list (e.g. ``eo:bands``) into the STAC 1.1
    ``bands`` field of an Item or Collection dict.

    Applies to Item properties and assets, and to Collection assets,
    ``item_assets`` and ``summaries``. If ``bands`` is not set, it is created from
    the extension's bands; otherwise the two lists are merged by index. The
    extension's own band fields (``fields``) get ``prefix``; all other fields are
    kept as they are. Empty band lists are removed.

    In extension v1, bands in Item properties were the bands of all assets; in
    STAC 1.1, they are the bands of assets that don't define their own. They are
    removed if each of them is also a band of an asset.

    Nothing is changed and a warning is emitted if a band list has a different
    number of bands than, or values different from, ``bands`` or another
    extension's band list next to it, or if bands in Item properties would be
    removed that no asset has. Fields in :data:`YIELDING_BAND_FIELDS` (``name`` of
    ``raster:bands``) are dropped with a warning instead. Band lists that contain
    anything other than band objects (pre-0.9 assets list band indices) are left
    unchanged.

    Args:
        obj : The Item or Collection dict to modify in place.
        bands_prop : The extension's band list field, e.g. ``"eo:bands"``.
        prefix : The extension's field prefix, e.g. ``"eo:"``.
        fields : The extension's v1 band fields, e.g. ``{"common_name"}``.

    Returns:
        bool: ``False`` if ``bands_prop`` is left anywhere in ``obj``.
    """
    containers = _band_containers(obj)
    problems = [_band_list_problem(c, bands_prop, prefix, fields) for c in containers]
    if obj.get("type") == pystac.STACObjectType.ITEM:
        problems.append(_item_bands_problem(obj, bands_prop, prefix, fields))
    if (problem := next((p for p in problems if p is not None), None)) is not None:
        warnings.warn(f"Not migrating {bands_prop}: {problem}")
        return False
    if obj.get("type") == pystac.STACObjectType.ITEM:
        properties = obj["properties"]
        if properties.get(bands_prop) and "bands" not in properties:
            if _is_band_list(properties[bands_prop]):
                del properties[bands_prop]
    for container in containers:
        _migrate_extension_bands_in(container, bands_prop, prefix, fields)
    return not any(bands_prop in container for container in containers)


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
