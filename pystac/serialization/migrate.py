from functools import lru_cache
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING, Tuple

import pystac as ps
from pystac.version import STACVersion
from pystac.serialization.identify import (OldExtensionShortIDs, STACJSONDescription, STACVersionID,
                                           STACVersionRange)

if TYPE_CHECKING:
    from pystac.stac_object import STACObjectType as STACObjectType_Type


def _migrate_links(d: Dict[str, Any], version: STACVersionID) -> None:
    if version < '0.6':
        if 'links' in d:
            if isinstance(d['links'], dict):
                d['links'] = list(d['links'].values())


def _migrate_catalog(d: Dict[str, Any], version: STACVersionID, info: STACJSONDescription) -> None:
    _migrate_links(d, version)

    if version < '0.8':
        d['stac_extensions'] = info.extensions


def _migrate_collection(d: Dict[str, Any], version: STACVersionID,
                        info: STACJSONDescription) -> None:
    _migrate_catalog(d, version, info)


def _migrate_item(d: Dict[str, Any], version: STACVersionID, info: STACJSONDescription) -> None:
    _migrate_links(d, version)

    if version < '0.8':
        d['stac_extensions'] = info.extensions


def _migrate_itemcollection(d: Dict[str, Any], version: STACVersionID,
                            info: STACJSONDescription) -> None:
    if version < '0.9.0':
        d['stac_extensions'] = info.extensions


# Extensions


class OldExtensionSchemaUriMap:
    """Ties old extension IDs to schemas hosted by https://schemas.stacspec.org.

    For STAC Versions 0.9.0 or earlier this will use the schemas hosted on the
    radiantearth/stac-spec GitHub repo.
    """

    # BASE_URIS contains a list of tuples, the first element is a version range and the
    # second being the base URI for schemas for that range. The schema URI of a STAC
    # for a particular version uses the base URI associated with the version range which
    # contains it. If the version it outside of any VersionRange, there is no URI for the
    # schema.
    @classmethod
    @lru_cache()
    def get_base_uris(cls) -> List[Tuple[STACVersionRange, Callable[[STACVersionID], str]]]:
        return [(STACVersionRange(min_version='1.0.0-beta.1'),
                 lambda version: 'https://schemas.stacspec.org/v{}'.format(version)),
                (STACVersionRange(min_version='0.8.0', max_version='0.9.0'), lambda version:
                 'https://raw.githubusercontent.com/radiantearth/stac-spec/v{}'.format(version))]

    # DEFAULT_SCHEMA_MAP contains a structure that matches extension schema URIs
    # based on the stac object type, extension ID and the stac version.
    # Uris are contained in a tuple whose first element represents the URI of the latest
    # version, so that a search through version ranges is avoided if the STAC being validated
    # is the latest version. If it's a previous version, the stac_version that matches
    # the listed version range is used, or else the URI from the latest version is used if
    # there are no overrides for previous versions.
    @classmethod
    @lru_cache()
    def get_schema_map(cls) -> Dict[str, Any]:
        return {
            OldExtensionShortIDs.CHECKSUM: ({
                ps.STACObjectType.CATALOG:
                'extensions/checksum/json-schema/schema.json',
                ps.STACObjectType.COLLECTION:
                'extensions/checksum/json-schema/schema.json',
                ps.STACObjectType.ITEM:
                'extensions/checksum/json-schema/schema.json'
            }, None),
            OldExtensionShortIDs.COLLECTION_ASSETS: ({
                ps.STACObjectType.COLLECTION:
                'extensions/collection-assets/json-schema/schema.json'
            }, None),
            OldExtensionShortIDs.DATACUBE: ({
                ps.STACObjectType.COLLECTION:
                'extensions/datacube/json-schema/schema.json',
                ps.STACObjectType.ITEM:
                'extensions/datacube/json-schema/schema.json'
            }, [(STACVersionRange(min_version='0.5.0', max_version='0.9.0'), {
                ps.STACObjectType.COLLECTION: None,
                ps.STACObjectType.ITEM: None
            })]),
            OldExtensionShortIDs.EO: ({
                ps.STACObjectType.ITEM:
                'extensions/eo/json-schema/schema.json'
            }, None),
            OldExtensionShortIDs.ITEM_ASSETS: ({
                ps.STACObjectType.COLLECTION:
                'extensions/item-assets/json-schema/schema.json'
            }, None),
            OldExtensionShortIDs.LABEL: ({
                ps.STACObjectType.ITEM:
                'extensions/label/json-schema/schema.json'
            }, [(STACVersionRange(min_version='0.8.0-rc1', max_version='0.8.1'), {
                ps.STACObjectType.ITEM: 'extensions/label/schema.json'
            })]),
            OldExtensionShortIDs.POINTCLOUD: (
                {
                    # Poincloud schema was broken in 1.0.0-beta.2 and prior;
                    # Use this schema version (corresponding to 1.0.0-rc.1)
                    # to allow for proper validation
                    ps.STACObjectType.ITEM:
                    'https://stac-extensions.github.io/pointcloud/v1.0.0/schema.json'
                },
                None),
            OldExtensionShortIDs.PROJECTION: ({
                ps.STACObjectType.ITEM:
                'extensions/projection/json-schema/schema.json'
            }, None),
            OldExtensionShortIDs.SAR: ({
                ps.STACObjectType.ITEM:
                'extensions/sar/json-schema/schema.json'
            }, None),
            OldExtensionShortIDs.SAT: ({
                ps.STACObjectType.ITEM:
                'extensions/sat/json-schema/schema.json'
            }, None),
            OldExtensionShortIDs.SCIENTIFIC: ({
                ps.STACObjectType.ITEM:
                'extensions/scientific/json-schema/schema.json',
                ps.STACObjectType.COLLECTION:
                'extensions/scientific/json-schema/schema.json'
            }, None),
            OldExtensionShortIDs.SINGLE_FILE_STAC: ({
                ps.STACObjectType.CATALOG:
                'extensions/single-file-stac/json-schema/schema.json'
            }, None),
            OldExtensionShortIDs.TILED_ASSETS: ({
                ps.STACObjectType.CATALOG:
                'extensions/tiled-assets/json-schema/schema.json',
                ps.STACObjectType.COLLECTION:
                'extensions/tiled-assets/json-schema/schema.json',
                ps.STACObjectType.ITEM:
                'extensions/tiled-assets/json-schema/schema.json'
            }, None),
            OldExtensionShortIDs.TIMESTAMPS: ({
                ps.STACObjectType.ITEM:
                'extensions/timestamps/json-schema/schema.json'
            }, None),
            OldExtensionShortIDs.VERSION: ({
                ps.STACObjectType.ITEM:
                'extensions/version/json-schema/schema.json',
                ps.STACObjectType.COLLECTION:
                'extensions/version/json-schema/schema.json'
            }, None),
            OldExtensionShortIDs.VIEW: ({
                ps.STACObjectType.ITEM:
                'extensions/view/json-schema/schema.json'
            }, None),

            # Removed or renamed extensions.
            'dtr': (None, None),  # Invalid schema
            'asset': (None, [(STACVersionRange(min_version='0.8.0-rc1', max_version='0.9.0'), {
                ps.STACObjectType.COLLECTION:
                'extensions/asset/json-schema/schema.json'
            })]),
        }

    @classmethod
    def _append_base_uri_if_needed(cls, uri: str, stac_version: STACVersionID) -> Optional[str]:
        # Only append the base URI if it's not already an absolute URI
        if '://' not in uri:
            base_uri = None
            for version_range, f in cls.get_base_uris():
                if version_range.contains(stac_version):
                    base_uri = f(stac_version)
                    return '{}/{}'.format(base_uri, uri)

            # No JSON Schema for the old extension
            return None
        else:
            return uri

    @classmethod
    def get_extension_schema_uri(cls, extension_id: str, object_type: "STACObjectType_Type",
                                 stac_version: STACVersionID) -> Optional[str]:
        uri = None

        is_latest = stac_version == ps.get_stac_version()

        ext_map = cls.get_schema_map()
        if extension_id in ext_map:
            if ext_map[extension_id][0] and \
               object_type in ext_map[extension_id][0]:
                uri = ext_map[extension_id][0][object_type]

            if not is_latest:
                if ext_map[extension_id][1]:
                    for version_range, ext_uris in ext_map[extension_id][1]:
                        if version_range.contains(stac_version):
                            if object_type in ext_uris:
                                uri = ext_uris[object_type]
                                break

        if uri is None:
            return uri
        else:
            return cls._append_base_uri_if_needed(uri, stac_version)


def _migrate_item_assets(d: Dict[str, Any], version: STACVersionID,
                         info: STACJSONDescription) -> Optional[Set[str]]:
    if version < '1.0.0-beta.2':
        if info.object_type == ps.STACObjectType.COLLECTION:
            if 'assets' in d:
                d['item_assets'] = d['assets']
                del d['assets']
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


def _get_object_migrations(
) -> Dict[str, Callable[[Dict[str, Any], STACVersionID, STACJSONDescription], None]]:
    return {
        ps.STACObjectType.CATALOG: _migrate_catalog,
        ps.STACObjectType.COLLECTION: _migrate_collection,
        ps.STACObjectType.ITEM: _migrate_item,
        ps.STACObjectType.ITEMCOLLECTION: _migrate_itemcollection
    }


def _get_removed_extension_migrations(
) -> Dict[str, Callable[[Dict[str, Any], STACVersionID, STACJSONDescription], Optional[Set[str]]]]:
    return {
        # Removed in 0.9.0
        'dtr': _migrate_datetime_range,
        'datetime-range': _migrate_datetime_range,
        'commons': lambda a, b, c: None  # No changes needed, just remove the extension_id
    }


# TODO: Item Assets
def _get_extension_renames() -> Dict[str, str]:
    return {'asset': 'item-assets'}


def migrate_to_latest(json_dict: Dict[str, Any], info: STACJSONDescription) -> Dict[str, Any]:
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
    removed_extension_migrations = _get_removed_extension_migrations()

    if version != STACVersion.DEFAULT_STAC_VERSION:
        object_migrations[info.object_type](result, version, info)
        ps.EXTENSION_HOOKS.migrate(result, version, info)

        for ext in (result.get('stac_extensions') or []):
            if ext in removed_extension_migrations:
                removed_extension_migrations[ext](result, version, info)
                result['stac_extensions'].remove(ext)
            else:
                # Ensure old ID's are moved to schemas
                # May need a better way to differentiate
                # old ID's from schemas, but going with
                # the file extension for now.
                if not ext.lower().endswith('.json'):
                    result['stac_extensions'].remove(ext)
                    uri = OldExtensionSchemaUriMap.get_extension_schema_uri(
                        ext, info.object_type, version)
                    if uri is not None:
                        result['stac_extensions'].append(uri)

    result['stac_version'] = STACVersion.DEFAULT_STAC_VERSION

    return result
