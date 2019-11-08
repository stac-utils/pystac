from pystac.version import STAC_VERSION
from pystac.serialization.common_properties import merge_common_properties


class STACObjectType:
    CATALOG = 'CATALOG'
    COLLECTION = 'COLLECTION'
    ITEM = 'ITEM'
    ITEMCOLLECTION = 'ITEMCOLLECTION'


class STACJSONDescription:
    """Describes the STAC object information for a STAC object represented in JSON

    Attributes:
        object_type (STACObjectType): Describes the STAC object type.
        version_range (STACVersionRange): The STAC version range that describes what
            has been identified as potential valid versions of the stac object.
        common_extensions (List[str]): List of common extension IDs implemented by this
            STAC object.
        custom_extensions (List[str]): List of custom extensions (URIs to JSON Schemas)
            used by this STAC Object.
    """
    def __init__(self, object_type, version_range, common_extensions,
                 custom_extensions):
        self.object_type = object_type
        self.version_range = version_range
        self.common_extensions = common_extensions
        self.custom_extensions = custom_extensions

    def __repr__(self):
        return '<{} {} common_ext={} custom_ext{}>'.format(
            self.object_type, self.version_range,
            ','.format(self.common_extensions),
            ','.format(self.custom_extensions))


class STACVersionRange:
    def __init__(self):
        self.min_version = '0.4.0'
        self.max_version = STAC_VERSION

    def set_min(self, v):
        if self.min_version < v:
            if v < self.max_version:
                self.min_version = v
            else:
                self.min_version = self.max_version

    def set_max(self, v):
        if v < self.max_version:
            if self.min_version < v:
                self.max_version = v
            else:
                self.max_version = self.min_version

    def set_to_single(self, v):
        self.set_min(v)
        self.set_max(v)

    def latest_valid_version(self):
        return self.max_version

    def contains(self, v):
        return self.min_version <= v and v <= self.max_version

    def is_single_version(self):
        return self.min_version >= self.max_version

    def __repr__(self):
        return '<VERSIONS {}-{}>'.format(self.min_version, self.max_version)


def _identify_stac_extensions(object_type, d, version_range):
    """Identifies extensions for STAC Objects that don't list their
    extensions in a 'stac_extensions' property.

    Returns a list of stac_extensions. May mutate the version_range to update
    min or max version.
    """
    stac_extensions = []

    # eo
    if object_type == STACObjectType.ITEM:
        if any(filter(lambda k: k.startswith('eo:'), d['properties'])):
            stac_extensions.append('eo')
            if 'eo:epsg' in d['properties']:
                if d['properties']['eo:epsg'] is None:
                    version_range.set_min('0.6.1')
            if 'eo:constellation' in d['properties']:
                version_range.set_min('0.6.0')
        if 'eo:bands' in d:
            version_range.set_max('0.5.2')

    # checksum
    if 'links' in d:
        found_checksum = False
        for link in d['links']:
            if any(filter(lambda p: p.startswith('checksum:'), link)):
                found_checksum = True
                stac_extensions.append('checksum')
        if not found_checksum:
            if 'assets' in d:
                for asset in d['assets']:
                    if any(filter(lambda p: p.startswith('checksum:'), link)):
                        found_checksum = True
                        stac_extensions.append('checksum')
        if found_checksum:
            version_range.set_min('0.6.2')

    # datacube
    if object_type == STACObjectType.ITEM:
        if any(filter(lambda k: k.startswith('cube:'), d['properties'])):
            stac_extensions.append('cube')
            version_range.set_min('0.6.1')

    # datetime-range
    if object_type == STACObjectType.ITEM:
        if 'dtr:start_datetime' in d['properties']:
            stac_extensions.append('dtr')
            version_range.set_min('0.6.0')

    # pointcloud
    if object_type == STACObjectType.ITEM:
        if any(filter(lambda k: k.startswith('pc:'), d['properties'])):
            stac_extensions.append('pointcloud')
            version_range.set_min('0.6.2')

    # sar
    if object_type == STACObjectType.ITEM:
        if any(filter(lambda k: k.startswith('sar:'), d['properties'])):
            stac_extensions.append('sar')
            version_range.set_min('0.6.2')
            if version_range.contains('0.6.2'):
                for prop in [
                        'sar:absolute_orbit', 'sar:resolution',
                        'sar:pixel_spacing', 'sar:looks'
                ]:
                    if prop in d['properties']:
                        if not isinstance(d['properties'][prop], list):
                            version_range.set_max('0.6.2')
            if version_range.contains('0.7.0'):
                for prop in [
                        'sar:incidence_angle', 'sar:relative_orbit',
                        'sar:observation_direction'
                ]:
                    if prop in d['properties']:
                        version_range.set_min('0.7.0')
            if 'sar:off_nadir' in d['properties']:
                version_range.set_max('0.6.2')

    # scientific
    if object_type == STACObjectType.ITEM or object_type == STACObjectType.COLLECTION:
        if 'properties' in d:
            if any(filter(lambda k: k.startswith('sci:'), d['properties'])):
                stac_extensions.append('scientific')
                version_range.set_min('0.6.0')

    # Single File STAC
    if object_type == STACObjectType.ITEMCOLLECTION:
        if 'collections' in d:
            stac_extensions.append('single-file-stac')
            version_range.set_min('0.8.0')

    return stac_extensions


def _split_extensions(stac_extensions):
    """Split extensions into common_extensions and custom_extensions"""

    common_extensions = []
    custom_extensions = []
    for ext in stac_extensions:
        # Custom extensions are a URI
        if ext.endswith('.json') or '/' in ext:
            custom_extensions.append(ext)
        else:
            common_extensions.append(ext)

    return (common_extensions, custom_extensions)


def identify_stac_object_type(json_dict):
    """Determines the STACObjectType of the provided JSON dict.

    Args:
        json_dict (dict): The dict of STAC JSON to identify.

    Returns:
        STACObjectType: The object type represented by the JSON.
    """
    object_type = None

    if 'type' in json_dict:
        if json_dict['type'] == 'FeatureCollection':
            object_type = STACObjectType.ITEMCOLLECTION
        else:
            object_type = STACObjectType.ITEM
    elif 'extent' in json_dict:
        object_type = STACObjectType.COLLECTION
    else:
        object_type = STACObjectType.CATALOG

    return object_type


def identify_stac_object(json_dict,
                         merge_collection_properties=False,
                         json_href=None,
                         collection_cache=None):
    """Determines the STACJSONDescription of the provided JSON dict.

    Args:
        json_dict (dict): The dict of STAC JSON to identify.
        merge_collection_properties (bool): If True, follow the collection links
            in Items if required to discover extensions and version (pre-0.8 STAC).
            Defaults to False.
        json_href (str): The path that this JSON came from. This is useful for
            for resolving relative paths to Collections in the case that
            ``merge_collection_properties`` is True and the collection link
            is relative.
        collection_cache (dict): If supplied, collection read for item links
            will check this cache for either the collection's ID (if available)
            or the HREF of the collection link. This is recommended to reduce
            unnecessary re-reading of collections.

    Returns:
        STACJSONDescription: The description of the STAC object serialized in the
        given dict.

    Note:
        If ``merge_collection_properties`` is False, there are cases where the
        common_extensions returned could be incorrect - e.g. if a collection lists
        'eo' extension properties but the Item does not contian any properties with
        the 'eo:' prefix.
    """
    object_type = identify_stac_object_type(json_dict)

    version_range = STACVersionRange()

    stac_version = json_dict.get('stac_version')
    stac_extensions = json_dict.get('stac_extensions', None)

    if stac_version is None:
        if object_type == STACObjectType.CATALOG or object_type == STACObjectType.COLLECTION:
            version_range.set_max('0.5.2')
        elif object_type == STACObjectType.ITEM:
            version_range.set_max('0.7.0')
        else:  # ItemCollection
            version_range.set_min('0.8.0')
    else:
        version_range.set_to_single(stac_version)

    if stac_extensions is None:
        # If this is post-0.8, we can assume there are no extensions
        # if the stac_extensions property doesn't exist for everything
        # but ItemCollection.
        if version_range.min_version is None or \
           version_range.min_version < '0.8.0' or \
           object_type == STACObjectType.ITEMCOLLECTION:
            if merge_collection_properties and object_type == STACObjectType.ITEM:
                merge_common_properties(json_dict, collection_cache, json_href)

            stac_extensions = _identify_stac_extensions(
                object_type, json_dict, version_range)
        else:
            stac_extensions = []

    if not version_range.is_single_version():
        # Final Checks

        # self links became non-required in 0.7.0
        if 'links' in json_dict:
            if not any(filter(lambda l: l['rel'] == 'self',
                              json_dict['links'])):
                version_range.set_min('0.7.0')

        # links were a dictionary only in 0.5
        if 'links' in json_dict and isinstance(json_dict['links'], dict):
            version_range.set_to_single('0.5.2')

    common_extensions, custom_extensions = _split_extensions(stac_extensions)

    return STACJSONDescription(object_type, version_range, common_extensions,
                               custom_extensions)
