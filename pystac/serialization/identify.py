from pystac.version import STAC_VERSION
from pystac.extension import Extension


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
    def __init__(self, object_type, version_range, common_extensions, custom_extensions):
        self.object_type = object_type
        self.version_range = version_range
        self.common_extensions = common_extensions
        self.custom_extensions = custom_extensions

    def __repr__(self):
        return '<{} {} common_ext={} custom_ext={}>'.format(self.object_type, self.version_range,
                                                            ','.join(self.common_extensions),
                                                            ','.join(self.custom_extensions))


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

    def is_earlier_than(self, v):
        return self.max_version < v

    def __repr__(self):
        return '<VERSIONS {}-{}>'.format(self.min_version, self.max_version)


def _identify_stac_extensions(object_type, d, version_range):
    """Identifies extensions for STAC Objects that don't list their
    extensions in a 'stac_extensions' property.

    Returns a list of stac_extensions. May mutate the version_range to update
    min or max version.
    """
    stac_extensions = set([])

    # assets (collection assets)

    if object_type == STACObjectType.ITEMCOLLECTION:
        if 'assets' in d:
            stac_extensions.add(Extension.ASSETS)
            version_range.set_min('0.8.0')

    # checksum
    if 'links' in d:
        found_checksum = False
        for link in d['links']:
            if any(filter(lambda p: p.startswith('checksum:'), link)):
                found_checksum = True
                stac_extensions.add(Extension.CHECKSUM)
        if not found_checksum:
            if 'assets' in d:
                for asset in d['assets']:
                    if any(filter(lambda p: p.startswith('checksum:'), link)):
                        found_checksum = True
                        stac_extensions.add(Extension.CHECKSUM)
        if found_checksum:
            version_range.set_min('0.6.2')

    # datacube
    if object_type == STACObjectType.ITEM:
        if any(filter(lambda k: k.startswith('cube:'), d['properties'])):
            stac_extensions.add(Extension.DATACUBE)
            version_range.set_min('0.6.1')

    # datetime-range
    if object_type == STACObjectType.ITEM:
        if 'dtr:start_datetime' in d['properties']:
            stac_extensions.add(Extension.DATETIME_RANGE)
            version_range.set_min('0.6.0')

    # eo
    if object_type == STACObjectType.ITEM:
        if any(filter(lambda k: k.startswith('eo:'), d['properties'])):
            stac_extensions.add(Extension.EO)
            if 'eo:epsg' in d['properties']:
                if d['properties']['eo:epsg'] is None:
                    version_range.set_min('0.6.1')
            if 'eo:crs' in d['properties']:
                version_range.set_max('0.4.1')
            if 'eo:constellation' in d['properties']:
                version_range.set_min('0.6.0')
        if 'eo:bands' in d:
            stac_extensions.add(Extension.EO)
            version_range.set_max('0.5.2')

    # pointcloud
    if object_type == STACObjectType.ITEM:
        if any(filter(lambda k: k.startswith('pc:'), d['properties'])):
            stac_extensions.add(Extension.POINTCLOUD)
            version_range.set_min('0.6.2')

    # sar
    if object_type == STACObjectType.ITEM:
        if any(filter(lambda k: k.startswith('sar:'), d['properties'])):
            stac_extensions.add(Extension.SAR)
            version_range.set_min('0.6.2')
            if version_range.contains('0.6.2'):
                for prop in [
                        'sar:absolute_orbit', 'sar:resolution', 'sar:pixel_spacing', 'sar:looks'
                ]:
                    if prop in d['properties']:
                        if isinstance(d['properties'][prop], list):
                            version_range.set_max('0.6.2')
            if version_range.contains('0.7.0'):
                for prop in [
                        'sar:incidence_angle', 'sar:relative_orbit', 'sar:observation_direction',
                        'sar:resolution_range', 'sar:resolution_azimuth', 'sar:pixel_spacing_range',
                        'sar:pixel_spacing_azimuth', 'sar:looks_range', 'sar:looks_azimuth',
                        'sar:looks_equivalent_number'
                ]:
                    if prop in d['properties']:
                        version_range.set_min('0.7.0')
                if 'sar:absolute_orbit' in d['properties'] and not isinstance(
                        d['properties']['sar:absolute_orbit'], list):
                    version_range.set_min('0.7.0')
            if 'sar:off_nadir' in d['properties']:
                version_range.set_max('0.6.2')

    # scientific
    if object_type == STACObjectType.ITEM or object_type == STACObjectType.COLLECTION:
        if 'properties' in d:
            if any(filter(lambda k: k.startswith('sci:'), d['properties'])):
                stac_extensions.add(Extension.SCIENTIFIC)
                version_range.set_min('0.6.0')

    # Single File STAC
    if object_type == STACObjectType.ITEMCOLLECTION:
        if 'collections' in d:
            stac_extensions.add(Extension.SINGLE_FILE_STAC)
            version_range.set_min('0.8.0')

    return list(stac_extensions)


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


def identify_stac_object(json_dict):
    """Determines the STACJSONDescription of the provided JSON dict.

    Args:
        json_dict (dict): The dict of STAC JSON to identify.

    Returns:
        STACJSONDescription: The description of the STAC object serialized in the
        given dict.

    Note:
        Items are expected to have their collection common properties merged into
        the dict. You can use :func:`~pystac.serialization.merge_common_properties`
        to accomplish that. Otherwise, there are cases where the
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

    if stac_extensions is not None:
        version_range.set_min('0.8.0')

    if stac_extensions is None:
        # If this is post-0.8, we can assume there are no extensions
        # if the stac_extensions property doesn't exist for everything
        # but ItemCollection.
        if version_range.is_earlier_than('0.8.0') or \
           object_type == STACObjectType.ITEMCOLLECTION:
            stac_extensions = _identify_stac_extensions(object_type, json_dict, version_range)
        else:
            stac_extensions = []

    if not version_range.is_single_version():
        # Final Checks

        if 'links' in json_dict:
            # links were a dictionary only in 0.5
            if 'links' in json_dict and isinstance(json_dict['links'], dict):
                version_range.set_to_single('0.5.2')

            # self links became non-required in 0.7.0
            if not version_range.is_earlier_than('0.7.0') and \
               not any(filter(lambda l: l['rel'] == 'self',
                              json_dict['links'])):
                version_range.set_min('0.7.0')

    common_extensions, custom_extensions = _split_extensions(stac_extensions)

    return STACJSONDescription(object_type, version_range, common_extensions, custom_extensions)
