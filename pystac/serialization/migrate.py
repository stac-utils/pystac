import re
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import pystac as ps
from pystac.version import STACVersion
from pystac.extensions import Extensions
from pystac.serialization.identify import (STACJSONDescription, STACVersionID, STACVersionRange)


def _migrate_links(d: Dict[str, Any], version: STACVersionID) -> None:
    if version < '0.6':
        if 'links' in d:
            if isinstance(d['links'], dict):
                d['links'] = list(d['links'].values())


def _migrate_catalog(d: Dict[str, Any], version: STACVersionID, info: STACJSONDescription) -> None:
    _migrate_links(d, version)

    if version < '0.8':
        d['stac_extensions'] = info.common_extensions + info.custom_extensions


def _migrate_collection(d: Dict[str, Any], version: STACVersionID,
                        info: STACJSONDescription) -> None:
    _migrate_catalog(d, version, info)


def _migrate_item(d: Dict[str, Any], version: STACVersionID, info: STACJSONDescription) -> None:
    _migrate_links(d, version)

    if version < '0.8':
        d['stac_extensions'] = info.common_extensions + info.custom_extensions


def _migrate_itemcollection(d: Dict[str, Any], version: STACVersionID,
                            info: STACJSONDescription) -> None:
    if version < '0.9.0':
        d['stac_extensions'] = info.common_extensions + info.custom_extensions


# Extensions


def _migrate_item_assets(d: Dict[str, Any], version: STACVersionID,
                         info: STACJSONDescription) -> Optional[Set[str]]:
    if version < '1.0.0-beta.2':
        if info.object_type == ps.STACObjectType.COLLECTION:
            if 'assets' in d:
                d['item_assets'] = d['assets']
                del d['assets']
    return None


def _migrate_checksum(d: Dict[str, Any], version: STACVersionID,
                      info: STACJSONDescription) -> Optional[Set[str]]:
    return None


def _migrate_datacube(d: Dict[str, Any], version: STACVersionID,
                      info: STACJSONDescription) -> Optional[Set[str]]:
    return None


def _migrate_datetime_range(d: Dict[str, Any], version: STACVersionID,
                            info: STACJSONDescription) -> Optional[Set[str]]:
    if version < '0.9':
        # Datetime range was removed
        if 'dtr:start_datetime' in d['properties'] and 'start_datetime' not in d['properties']:
            d['properties']['start_datetime'] = d['properties']['dtr:start_datetime']
            del d['properties']['dtr:start_datetime']

        if 'dtr:end_datetime' in d['properties'] and 'end_datetime' not in d['properties']:
            d['properties']['end_datetime'] = d['properties']['dtr:end_datetime']
            del d['properties']['dtr:end_datetime']

    return None


def _migrate_eo(d: Dict[str, Any], version: STACVersionID,
                info: STACJSONDescription) -> Optional[Set[str]]:
    added_extensions: Set[str] = set([])
    if version < '0.5':
        if 'eo:crs' in d['properties']:
            # Try to pull out the EPSG code.
            # Otherwise, just leave it alone.
            wkt = d['properties']['eo:crs']
            matches = list(re.finditer(r'AUTHORITY\[[^\]]*\"(\d+)"\]', wkt))
            if len(matches) > 0:
                epsg_code = matches[-1].group(1)
                d['properties'].pop('eo:crs')
                d['properties']['eo:epsg'] = int(epsg_code)

    if version < '0.6':
        # Change eo:bands from a dict to a list. eo:bands on an asset
        # is an index instead of a dict key. eo:bands is in properties.
        bands_dict = d['eo:bands']
        keys_to_indices: Dict[str, int] = {}
        bands: List[Dict[str, Any]] = []
        for i, (k, band) in enumerate(bands_dict.items()):
            keys_to_indices[k] = i
            bands.append(band)

        d.pop('eo:bands')
        d['properties']['eo:bands'] = bands
        for k, asset in d['assets'].items():
            if 'eo:bands' in asset:
                asset_band_indices: List[int] = []
                for bk in asset['eo:bands']:
                    asset_band_indices.append(keys_to_indices[bk])
                asset['eo:bands'] = sorted(asset_band_indices)

    if version < '0.9':
        # Some eo fields became common_metadata
        if 'eo:platform' in d['properties'] and 'platform' not in d['properties']:
            d['properties']['platform'] = d['properties']['eo:platform']
            del d['properties']['eo:platform']

        if 'eo:instrument' in d['properties'] and 'instruments' not in d['properties']:
            d['properties']['instruments'] = [d['properties']['eo:instrument']]
            del d['properties']['eo:instrument']

        if 'eo:constellation' in d['properties'] and 'constellation' not in d['properties']:
            d['properties']['constellation'] = d['properties']['eo:constellation']
            del d['properties']['eo:constellation']

        # Some eo fields became view extension fields
        eo_to_view_fields = [
            'off_nadir', 'azimuth', 'incidence_angle', 'sun_azimuth', 'sun_elevation'
        ]

        view_enabled = 'view' in d['stac_extensions']
        for field in eo_to_view_fields:
            if 'eo:{}'.format(field) in d['properties']:
                if not view_enabled:
                    added_extensions.add('view')
                    view_enabled = True
                if not 'view:{}'.format(field) in d['properties']:
                    d['properties']['view:{}'.format(field)] = \
                        d['properties']['eo:{}'.format(field)]
                    del d['properties']['eo:{}'.format(field)]

    if version < '1.0.0-beta.1' and info.object_type == ps.STACObjectType.ITEM:
        # gsd moved from eo to common metadata
        if 'eo:gsd' in d['properties']:
            d['properties']['gsd'] = d['properties']['eo:gsd']
            del d['properties']['eo:gsd']

        # The way bands were declared in assets changed.
        # In 1.0.0-beta.1 they are inlined into assets as
        # opposed to having indices back into a property-level array.
        if 'eo:bands' in d['properties']:
            bands = d['properties']['eo:bands']
            for asset in d['assets'].values():
                if 'eo:bands' in asset:
                    new_bands: List[Dict[str, Any]] = []
                    for band_index in asset['eo:bands']:
                        new_bands.append(bands[band_index])
                    asset['eo:bands'] = new_bands

    return added_extensions


def _migrate_label(d: Dict[str, Any], version: STACVersionID,
                   info: STACJSONDescription) -> Optional[Set[str]]:
    if info.object_type == ps.STACObjectType.ITEM and version < '1.0.0':
        props = d['properties']
        # Migrate 0.8.0-rc1 non-pluralized forms
        # As it's a common mistake, convert for any pre-1.0.0 version.
        if 'label:property' in props and 'label:properties' not in props:
            props['label:properties'] = props['label:property']
            del props['label:property']

        if 'label:task' in props and 'label:tasks' not in props:
            props['label:tasks'] = props['label:task']
            del props['label:task']

        if 'label:overview' in props and 'label:overviews' not in props:
            props['label:overviews'] = props['label:overview']
            del props['label:overview']

        if 'label:method' in props and 'label:methods' not in props:
            props['label:methods'] = props['label:method']
            del props['label:method']

    return None


def _migrate_pointcloud(d: Dict[str, Any], version: STACVersionID,
                        info: STACJSONDescription) -> Optional[Set[str]]:
    return None


def _migrate_sar(d: Dict[str, Any], version: STACVersionID,
                 info: STACJSONDescription) -> Optional[Set[str]]:
    if version < '0.9':
        # Some sar fields became common_metadata
        if 'sar:platform' in d['properties'] and 'platform' not in d['properties']:
            d['properties']['platform'] = d['properties']['sar:platform']
            del d['properties']['sar:platform']

        if 'sar:instrument' in d['properties'] and 'instruments' not in d['properties']:
            d['properties']['instruments'] = [d['properties']['sar:instrument']]
            del d['properties']['sar:instrument']

        if 'sar:constellation' in d['properties'] and 'constellation' not in d['properties']:
            d['properties']['constellation'] = d['properties']['sar:constellation']
            del d['properties']['sar:constellation']

    return None


def _migrate_scientific(d: Dict[str, Any], version: STACVersionID,
                        info: STACJSONDescription) -> Optional[Set[str]]:
    return None


def _migrate_single_file_stac(d: Dict[str, Any], version: STACVersionID,
                              info: STACJSONDescription) -> Optional[Set[str]]:
    return None


def _get_object_migrations(
) -> Dict[str, Callable[[Dict[str, Any], STACVersionID, STACJSONDescription], None]]:
    return {
        ps.STACObjectType.CATALOG: _migrate_catalog,
        ps.STACObjectType.COLLECTION: _migrate_collection,
        ps.STACObjectType.ITEM: _migrate_item,
        ps.STACObjectType.ITEMCOLLECTION: _migrate_itemcollection
    }


def _get_extension_migrations(
) -> Dict[str, Callable[[Dict[str, Any], STACVersionID, STACJSONDescription], Optional[Set[str]]]]:
    return {
        Extensions.CHECKSUM: _migrate_checksum,
        Extensions.DATACUBE: _migrate_datacube,
        Extensions.EO: _migrate_eo,
        Extensions.ITEM_ASSETS: _migrate_item_assets,
        Extensions.LABEL: _migrate_label,
        Extensions.POINTCLOUD: _migrate_pointcloud,
        Extensions.SAR: _migrate_sar,
        Extensions.SCIENTIFIC: _migrate_scientific,
        Extensions.SINGLE_FILE_STAC: _migrate_single_file_stac
    }


def _get_removed_extension_migrations(
) -> Dict[str, Callable[[Dict[str, Any], STACVersionID, STACJSONDescription], Optional[Set[str]]]]:
    return {
        # Removed in 0.9.0
        'dtr': _migrate_datetime_range,
        'datetime-range': _migrate_datetime_range,
        'commons': lambda a, b, c: None  # No changes needed, just remove the extension_id
    }


def _get_extension_renames() -> Dict[str, str]:
    return {'asset': 'item-assets'}


def migrate_to_latest(json_dict: Dict[str, Any],
                      info: STACJSONDescription) -> Tuple[Dict[str, Any], STACJSONDescription]:
    """Migrates the STAC JSON to the latest version

    Args:
        json_dict (dict): The dict of STAC JSON to identify.
        info (STACJSONDescription): The info from
            :func:`~pystac.serialization.identify.identify_stac_object` that describes
            the STAC object contained in the JSON dict.

    Returns:
        dict: A copy of the dict that is migrated to the latest version (the
        version that is pystac.version.STACVersion.DEFAULT_STAC_VERSION)
    """
    result = deepcopy(json_dict)
    version = info.version_range.latest_valid_version()

    object_migrations = _get_object_migrations()
    extension_migrations = _get_extension_migrations()
    extension_renames = _get_extension_renames()
    removed_extension_migrations = _get_removed_extension_migrations()

    if version != STACVersion.DEFAULT_STAC_VERSION:
        object_migrations[info.object_type](result, version, info)

        extensions_to_add = set([])
        for ext in info.common_extensions:
            if ext in extension_renames:
                result['stac_extensions'].remove(ext)
                ext = extension_renames[ext]
                extensions_to_add.add(ext)

            if ext in extension_migrations:
                added_extensions = extension_migrations[ext](result, version, info)
                if added_extensions:
                    extensions_to_add |= added_extensions

            if ext in removed_extension_migrations:
                removed_extension_migrations[ext](result, version, info)
                result['stac_extensions'].remove(ext)

        for ext in extensions_to_add:
            result['stac_extensions'].append(ext)

        migrated_extensions = set(info.common_extensions)
        migrated_extensions = migrated_extensions | set(extensions_to_add)
        migrated_extensions = migrated_extensions - set(removed_extension_migrations.keys())
        migrated_extensions = migrated_extensions - set(extension_renames.keys())
        common_extensions = list(migrated_extensions)
    else:
        common_extensions = info.common_extensions

    result['stac_version'] = STACVersion.DEFAULT_STAC_VERSION

    return result, STACJSONDescription(
        info.object_type,
        STACVersionRange(STACVersion.DEFAULT_STAC_VERSION, STACVersion.DEFAULT_STAC_VERSION),
        common_extensions, info.custom_extensions)
