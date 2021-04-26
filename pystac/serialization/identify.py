from enum import Enum
from functools import total_ordering, lru_cache
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING, Tuple, Union, cast

import pystac as ps
from pystac.version import STACVersion

if TYPE_CHECKING:
    from pystac.stac_object import STACObjectType as STACObjectType_Type


class OldExtensionShortIDs(str, Enum):
    """Enumerates the IDs of common extensions."""
    def __str__(self) -> str:
        return str(self.value)

    CHECKSUM = 'checksum'
    COLLECTION_ASSETS = 'collection-assets'
    DATACUBE = 'datacube'
    EO = 'eo'
    ITEM_ASSETS = 'item-assets'
    LABEL = 'label'
    POINTCLOUD = 'pointcloud'
    PROJECTION = 'projection'
    SAR = 'sar'
    SAT = 'sat'
    SCIENTIFIC = 'scientific'
    SINGLE_FILE_STAC = 'single-file-stac'
    TILED_ASSETS = 'tiled-assets'
    TIMESTAMPS = 'timestamps'
    VERSION = 'version'
    VIEW = 'view'
    FILE = 'file'


@total_ordering
class STACVersionID:
    """Defines STAC versions in an object that is orderable based on version number.
    For instance, ``1.0.0-beta.2 < 1.0.0``
    """
    def __init__(self, version_string: str) -> None:
        self.version_string = version_string

        # Account for RC or beta releases in version
        version_parts = version_string.split('-')
        self.version_core = version_parts[0]
        if len(version_parts) == 1:
            self.version_prerelease = None
        else:
            self.version_prerelease = '-'.join(version_parts[1:])

    def __str__(self) -> str:
        return self.version_string

    def __eq__(self, other: Any) -> bool:
        if type(other) is str:
            other = STACVersionID(other)
        return self.version_string == other.version_string

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other: Any) -> bool:
        if type(other) is str:
            other = STACVersionID(other)
        if self.version_core < other.version_core:
            return True
        elif self.version_core > other.version_core:
            return False
        else:
            return self.version_prerelease is not None and (
                other.version_prerelease is None
                or other.version_prerelease > self.version_prerelease)


class STACVersionRange:
    """Defines a range of STAC versions."""
    def __init__(self,
                 min_version: Union[str, STACVersionID] = '0.4.0',
                 max_version: Optional[Union[str, STACVersionID]] = None):
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
        return '<VERSIONS {}-{}>'.format(self.min_version, self.max_version)


class OldExtensionSchemaUriMap:
    """Implementation of SchemaUriMap that uses schemas hosted by https://schemas.stacspec.org.

    For STAC Versions 0.9.0 or earlier this will use the schemas hosted on the
    radiantearth/stac-spec GitHub repo.
    """

    # BASE_URIS contains a list of tuples, the first element is a version range and the
    # second being the base URI for schemas for that range. The schema URI of a STAC
    # for a particular version uses the base URI associated with the version range which
    # contains it. If the version it outside of any VersionRange, there is no URI for the
    # schema.
    @lru_cache()
    def get_base_uris(self) -> List[Tuple[STACVersionRange, Callable[[str], str]]]:
        return [(STACVersionRange(min_version='1.0.0-beta.1'),
                 lambda version: 'https://schemas.stacspec.org/v{}'.format(version)),
                (STACVersionRange(min_version='0.8.0', max_version='0.9.0'), lambda version:
                 'https://raw.githubusercontent.com/radiantearth/stac-spec/v{}'.format(version))]

    # DEFAULT_SCHEMA_MAP contains a structure that matches 'core' or 'extension' schema URIs
    # based on the stac object type and the stac version, using a similar technique as BASE_URIS.
    # Uris are contained in a tuple whose first element represents the URI of the latest
    # version, so that a search through version ranges is avoided if the STAC being validated
    # is the latest version. If it's a previous version, the stac_version that matches
    # the listed version range is used, or else the URI from the latest version is used if
    # there are no overrides for previous versions.
    def get_schema_map(self) -> Dict[str, Any]:
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
                    ps.STACObjectType.ITEM: None  # 'extensions/pointcloud/json-schema/schema.json'
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

    def _append_base_uri_if_needed(self, uri: str, stac_version: str) -> Optional[str]:
        # Only append the base URI if it's not already an absolute URI
        if '://' not in uri:
            base_uri = None
            for version_range, f in self.get_base_uris():
                if version_range.contains(stac_version):
                    base_uri = f(stac_version)
                    return '{}/{}'.format(base_uri, uri)

            # No JSON Schema for the old extension
            return None
        else:
            return uri

    def get_extension_schema_uri(self, extension_id: str, object_type: "STACObjectType_Type",
                                 stac_version: str) -> Optional[str]:
        uri = None

        is_latest = stac_version == ps.get_stac_version()

        ext_map = self.get_schema_map()
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
            return self._append_base_uri_if_needed(uri, stac_version)


class STACJSONDescription:
    """Describes the STAC object information for a STAC object represented in JSON

    Attributes:
        object_type (str): Describes the STAC object type. One of :class:`~pystac.STACObjectType`.
        version_range (STACVersionRange): The STAC version range that describes what
            has been identified as potential valid versions of the stac object.
        extensions (List[str]): List of extension schema URIs for extensions this
            object implements
    """
    def __init__(self, object_type: "STACObjectType_Type", version_range: STACVersionRange,
                 extensions: List[str]) -> None:
        self.object_type = object_type
        self.version_range = version_range
        self.extensions = extensions

    def __repr__(self) -> str:
        return '<{} {} ext={}>'.format(self.object_type, self.version_range,
                                       ','.join(self.extensions))


def _identify_stac_extensions(object_type: str, d: Dict[str, Any],
                              version_range: STACVersionRange) -> List[str]:
    """Identifies extensions for STAC Objects that don't list their
    extensions in a 'stac_extensions' property.

    Returns a list of stac_extensions. May mutate the version_range to update
    min or max version.
    """
    stac_extensions = set([])

    # assets (collection assets)

    if object_type == ps.STACObjectType.ITEMCOLLECTION:
        if 'assets' in d:
            stac_extensions.add('assets')
            version_range.set_min(STACVersionID('0.8.0'))

    # checksum
    if 'links' in d:
        found_checksum = False
        for link in d['links']:
            # Account for old links as dicts
            if isinstance(link, str):
                link_props = cast(Dict[str, Any], d['links'][link]).keys()
            else:
                link_props = cast(Dict[str, Any], link).keys()

            if any(prop.startswith('checksum:') for prop in link_props):
                found_checksum = True
                stac_extensions.add(OldExtensionShortIDs.CHECKSUM)
        if not found_checksum:
            if 'assets' in d:
                for asset in d['assets'].values():
                    asset_props = cast(Dict[str, Any], asset).keys()
                    if any(prop.startswith('checksum:') for prop in asset_props):
                        found_checksum = True
                        stac_extensions.add(OldExtensionShortIDs.CHECKSUM)
        if found_checksum:
            version_range.set_min(STACVersionID('0.6.2'))

    # datacube
    if object_type == ps.STACObjectType.ITEM:
        if any(k.startswith('cube:') for k in cast(Dict[str, Any], d['properties'])):
            stac_extensions.add(OldExtensionShortIDs.DATACUBE)
            version_range.set_min(STACVersionID('0.6.1'))

    # datetime-range (old extension)
    if object_type == ps.STACObjectType.ITEM:
        if 'dtr:start_datetime' in d['properties']:
            stac_extensions.add('datetime-range')
            version_range.set_min(STACVersionID('0.6.0'))

    # eo
    if object_type == ps.STACObjectType.ITEM:
        if any(k.startswith('eo:') for k in cast(Dict[str, Any], d['properties'])):
            stac_extensions.add(OldExtensionShortIDs.EO)
            if 'eo:epsg' in d['properties']:
                if d['properties']['eo:epsg'] is None:
                    version_range.set_min(STACVersionID('0.6.1'))
            if 'eo:crs' in d['properties']:
                version_range.set_max(STACVersionID('0.4.1'))
            if 'eo:constellation' in d['properties']:
                version_range.set_min(STACVersionID('0.6.0'))
        if 'eo:bands' in d:
            stac_extensions.add(OldExtensionShortIDs.EO)
            version_range.set_max(STACVersionID('0.5.2'))

    # pointcloud
    if object_type == ps.STACObjectType.ITEM:
        if any(k.startswith('pc:') for k in cast(Dict[str, Any], d['properties'])):
            stac_extensions.add(OldExtensionShortIDs.POINTCLOUD)
            version_range.set_min(STACVersionID('0.6.2'))

    # sar
    if object_type == ps.STACObjectType.ITEM:
        if any(k.startswith('sar:') for k in cast(Dict[str, Any], d['properties'])):
            stac_extensions.add(OldExtensionShortIDs.SAR)
            version_range.set_min(STACVersionID('0.6.2'))
            if version_range.contains('0.6.2'):
                for prop in [
                        'sar:absolute_orbit', 'sar:resolution', 'sar:pixel_spacing', 'sar:looks'
                ]:
                    if prop in d['properties']:
                        if isinstance(d['properties'][prop], list):
                            version_range.set_max(STACVersionID('0.6.2'))
            if version_range.contains('0.7.0'):
                for prop in [
                        'sar:incidence_angle', 'sar:relative_orbit', 'sar:observation_direction',
                        'sar:resolution_range', 'sar:resolution_azimuth', 'sar:pixel_spacing_range',
                        'sar:pixel_spacing_azimuth', 'sar:looks_range', 'sar:looks_azimuth',
                        'sar:looks_equivalent_number'
                ]:
                    if prop in d['properties']:
                        version_range.set_min(STACVersionID('0.7.0'))
                if 'sar:absolute_orbit' in d['properties'] and not isinstance(
                        d['properties']['sar:absolute_orbit'], list):
                    version_range.set_min(STACVersionID('0.7.0'))
            if 'sar:off_nadir' in d['properties']:
                version_range.set_max(STACVersionID('0.6.2'))

    # scientific
    if object_type == ps.STACObjectType.ITEM or object_type == ps.STACObjectType.COLLECTION:
        if 'properties' in d:
            prop_keys = cast(Dict[str, Any], d['properties']).keys()
            if any(k.startswith('sci:') for k in prop_keys):
                stac_extensions.add(OldExtensionShortIDs.SCIENTIFIC)
                version_range.set_min(STACVersionID('0.6.0'))

    # Single File STAC
    if object_type == ps.STACObjectType.ITEMCOLLECTION:
        if 'collections' in d:
            stac_extensions.add(OldExtensionShortIDs.SINGLE_FILE_STAC)
            version_range.set_min(STACVersionID('0.8.0'))
            if 'stac_extensions' not in d:
                version_range.set_max(STACVersionID('0.8.1'))

    return list(stac_extensions)


def identify_stac_object_type(json_dict: Dict[str, Any]) -> "STACObjectType_Type":
    """Determines the STACObjectType of the provided JSON dict.

    Args:
        json_dict (dict): The dict of STAC JSON to identify.

    Returns:
        STACObjectType: The object type represented by the JSON.
    """
    object_type = None

    # Identify pre-1.0 ITEMCOLLECTION (since removed)
    if 'type' in json_dict and 'assets' not in json_dict:
        if 'stac_version' in json_dict and cast(str, json_dict['stac_version']).startswith('0'):
            if json_dict['type'] == 'FeatureCollection':
                object_type = ps.STACObjectType.ITEMCOLLECTION

    if 'extent' in json_dict:
        object_type = ps.STACObjectType.COLLECTION
    elif 'assets' in json_dict:
        object_type = ps.STACObjectType.ITEM
    else:
        object_type = ps.STACObjectType.CATALOG

    return object_type


def identify_stac_object(json_dict: Dict[str, Any]) -> STACJSONDescription:
    """Determines the STACJSONDescription of the provided JSON dict.

    Args:
        json_dict (dict): The dict of STAC JSON to identify.

    Returns:
        STACJSONDescription: The description of the STAC object serialized in the
        given dict.
    """
    object_type = identify_stac_object_type(json_dict)

    version_range = STACVersionRange()

    stac_version = json_dict.get('stac_version')
    stac_extensions = json_dict.get('stac_extensions', None)

    if stac_version is None:
        if (object_type == ps.STACObjectType.CATALOG
                or object_type == ps.STACObjectType.COLLECTION):
            version_range.set_max(STACVersionID('0.5.2'))
        elif object_type == ps.STACObjectType.ITEM:
            version_range.set_max(STACVersionID('0.7.0'))
        else:  # ItemCollection
            version_range.set_min(STACVersionID('0.8.0'))
    else:
        version_range.set_to_single(stac_version)

    if stac_extensions is not None:
        version_range.set_min(STACVersionID('0.8.0'))

    if stac_extensions is None:
        # If this is post-0.8, we can assume there are no extensions
        # if the stac_extensions property doesn't exist for everything
        # but ItemCollection (except after 0.9.0, when ItemCollection also got
        # the stac_extensions property).
        if version_range.is_earlier_than('0.8.0') or \
           (object_type == ps.STACObjectType.ITEMCOLLECTION and not version_range.is_later_than(
               '0.8.1')):
            stac_extensions = _identify_stac_extensions(object_type, json_dict, version_range)
        else:
            stac_extensions = []

        # Between 1.0.0-beta.2 and 1.0.0-RC1, STAC extensions changed from
        # being split between 'common' and custom extensions, with common
        # extensions having short names that were used in the stac_extensions
        # property list, to being mostly externalized from the core spec and
        # always identified with the schema URI as the identifier. This
        # code translates the short name IDs used pre-1.0.0-RC1 to the
        # relevant extension schema uri identifier.


    if not version_range.is_single_version():
        # Final Checks

        if 'links' in json_dict:
            # links were a dictionary only in 0.5
            if 'links' in json_dict and isinstance(json_dict['links'], dict):
                version_range.set_to_single(STACVersionID('0.5.2'))

            # self links became non-required in 0.7.0
            if not version_range.is_earlier_than('0.7.0') and \
               not any(filter(lambda l: cast(Dict[str, Any], l)['rel'] == 'self',
                              json_dict['links'])):
                version_range.set_min(STACVersionID('0.7.0'))

    return STACJSONDescription(object_type, version_range, stac_extensions)
