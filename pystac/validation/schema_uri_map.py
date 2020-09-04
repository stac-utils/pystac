from abc import (ABC, abstractmethod)

import pystac
from pystac import (STACObjectType, Extensions)
from pystac.serialization import STACVersionRange


class SchemaUriMap(ABC):
    """Abstract class defining schema URIs for STAC core objects and extensions.
    """
    def __init__(self):
        pass

    @abstractmethod
    def get_core_schema_uri(self, object_type, stac_version):
        """Get the schema URI for the given object type and stac version.

        Args:
            object_type (str): STAC object type. One of :class:`~pystac.STACObjectType`
            stac_version (str): The STAC version of the schema to return.

        Returns:
            str: The URI of the schema, or None if not found.
        """
        pass

    @abstractmethod
    def get_extension_schema_uri(self, extension_id, object_type, stac_version):
        """Get the extension's schema URI for the given object type, stac version.

        Args:
            extension_id (str): The Extension ID of the extension of the schema.
            object_type (str): STAC object type. One of :class:`~pystac.STACObjectType`
            stac_version (str): The STAC version of the schema to return.

        Returns:
            str: The URI of the schema, or None if not found.
        """
        pass


class DefaultSchemaUriMap(SchemaUriMap):
    """Implementation of SchemaUriMap that uses schemas hosted by https://schemas.stacspec.org.

    For STAC Versions 0.9.0 or earlier this will use the schemas hosted on the
    radiantearth/stac-spec GitHub repo.
    """

    # BASE_URIS contains a list of tuples, the first element is a version range and the
    # second being the base URI for schemas for that range. The schema URI of a STAC
    # for a particular version uses the base URI associated with the version range which
    # contains it. If the version it outside of any VersionRange, there is no URI for the
    # schema.
    BASE_URIS = [(STACVersionRange(min_version='1.0.0-beta.1'),
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
    DEFAULT_SCHEMA_MAP = {
        'core': {
            STACObjectType.CATALOG: ('catalog-spec/json-schema/catalog.json', None),
            STACObjectType.COLLECTION: ('collection-spec/json-schema/collection.json', None),
            STACObjectType.ITEM: ('item-spec/json-schema/item.json', None),
            STACObjectType.ITEMCOLLECTION: (None, [
                STACVersionRange(min_version='v0.8.0-rc1', max_version='0.9.0'),
                'item-spec/json-schema/itemcollection.json'
            ])
        },
        'extension': {
            Extensions.CHECKSUM: ({
                STACObjectType.CATALOG: 'extensions/checksum/json-schema/schema.json',
                STACObjectType.COLLECTION: 'extensions/checksum/json-schema/schema.json',
                STACObjectType.ITEM: 'extensions/checksum/json-schema/schema.json'
            }, None),
            Extensions.COLLECTION_ASSETS: ({
                STACObjectType.COLLECTION:
                'extensions/collection-assets/json-schema/schema.json'
            }, None),
            Extensions.DATACUBE: ({
                STACObjectType.COLLECTION: 'extensions/datacube/json-schema/schema.json',
                STACObjectType.ITEM: 'extensions/datacube/json-schema/schema.json'
            }, [(STACVersionRange(min_version='0.5.0', max_version='0.9.0'), {
                STACObjectType.COLLECTION: None,
                STACObjectType.ITEM: None
            })]),
            Extensions.EO: ({
                STACObjectType.ITEM: 'extensions/eo/json-schema/schema.json'
            }, None),
            Extensions.ITEM_ASSETS: ({
                STACObjectType.COLLECTION:
                'extensions/item-assets/json-schema/schema.json'
            }, None),
            Extensions.LABEL: ({
                STACObjectType.ITEM: 'extensions/label/json-schema/schema.json'
            }, [(STACVersionRange(min_version='0.8.0-rc1', max_version='0.8.1'), {
                STACObjectType.ITEM: 'extensions/label/schema.json'
            })]),
            Extensions.POINTCLOUD: (
                {
                    STACObjectType.ITEM: None  # 'extensions/pointcloud/json-schema/schema.json'
                },
                None),
            Extensions.PROJECTION: ({
                STACObjectType.ITEM:
                'extensions/projection/json-schema/schema.json'
            }, None),
            Extensions.SAR: ({
                STACObjectType.ITEM: 'extensions/sar/json-schema/schema.json'
            }, None),
            Extensions.SAT: ({
                STACObjectType.ITEM: 'extensions/sat/json-schema/schema.json'
            }, None),
            Extensions.SCIENTIFIC: ({
                STACObjectType.ITEM:
                'extensions/scientific/json-schema/schema.json',
                STACObjectType.COLLECTION:
                'extensions/scientific/json-schema/schema.json'
            }, None),
            Extensions.SINGLE_FILE_STAC: ({
                STACObjectType.CATALOG:
                'extensions/single-file-stac/json-schema/schema.json'
            }, None),
            Extensions.TILED_ASSETS: ({
                STACObjectType.CATALOG:
                'extensions/tiled-assets/json-schema/schema.json',
                STACObjectType.COLLECTION:
                'extensions/tiled-assets/json-schema/schema.json',
                STACObjectType.ITEM:
                'extensions/tiled-assets/json-schema/schema.json'
            }, None),
            Extensions.TIMESTAMPS: ({
                STACObjectType.ITEM:
                'extensions/timestamps/json-schema/schema.json'
            }, None),
            Extensions.VERSION: ({
                STACObjectType.ITEM:
                'extensions/version/json-schema/schema.json',
                STACObjectType.COLLECTION:
                'extensions/version/json-schema/schema.json'
            }, None),
            Extensions.VIEW: ({
                STACObjectType.ITEM: 'extensions/view/json-schema/schema.json'
            }, None),

            # Removed or renamed extensions.
            'dtr': (None, None),  # Invalid schema
            'asset': (None, [(STACVersionRange(min_version='0.8.0-rc1', max_version='0.9.0'), {
                STACObjectType.COLLECTION: 'extensions/asset/json-schema/schema.json'
            })]),
        }
    }

    @classmethod
    def _append_base_uri_if_needed(cls, uri, stac_version):
        # Only append the base URI if it's not already an absolute URI
        if '://' not in uri:
            base_uri = None
            for version_range, f in cls.BASE_URIS:
                if version_range.contains(stac_version):
                    base_uri = f(stac_version)
                    return '{}/{}'.format(base_uri, uri)

            # We don't have JSON schema validation for this version of PySTAC
            return None
        else:
            return uri

    def get_core_schema_uri(self, object_type, stac_version):
        uri = None
        is_latest = stac_version == pystac.get_stac_version()

        if object_type not in self.DEFAULT_SCHEMA_MAP['core']:
            raise KeyError('Unknown STAC object type {}'.format(object_type))

        uri = self.DEFAULT_SCHEMA_MAP['core'][object_type][0]
        if not is_latest:
            if self.DEFAULT_SCHEMA_MAP['core'][object_type][1]:
                for version_range, range_uri in self.DEFAULT_SCHEMA_MAP['core'][object_type][1]:
                    if version_range.contains(stac_version):
                        uri = range_uri
                        break

        return self._append_base_uri_if_needed(uri, stac_version)

    def get_extension_schema_uri(self, extension_id, object_type, stac_version):
        uri = None

        is_latest = stac_version == pystac.get_stac_version()

        ext_map = self.DEFAULT_SCHEMA_MAP['extension']
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
