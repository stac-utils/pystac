from abc import (ABC, abstractmethod)
from typing import Any, Callable, Dict, List, Optional, Tuple

import pystac as ps
from pystac.serialization import STACVersionRange
from pystac.stac_object import STACObjectType


class SchemaUriMap(ABC):
    """Abstract class defining schema URIs for STAC core objects and extensions.
    """
    def __init__(self) -> None:
        pass

    @abstractmethod
    def get_object_schema_uri(self, object_type: STACObjectType, stac_version: str) -> Optional[str]:
        """Get the schema URI for the given object type and stac version.

        Args:
            object_type (STACObjectType): STAC object type. One of :class:`~pystac.STACObjectType`
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
    BASE_URIS: List[Tuple[STACVersionRange, Callable[[str], str]]] = [
        (STACVersionRange(min_version='1.0.0-beta.1'),
         lambda version: 'https://schemas.stacspec.org/v{}'.format(version)),
        (STACVersionRange(min_version='0.8.0', max_version='0.9.0'), lambda version:
         'https://raw.githubusercontent.com/radiantearth/stac-spec/v{}'.format(version))
    ]

    # DEFAULT_SCHEMA_MAP contains a structure that matches 'core' or 'extension' schema URIs
    # based on the stac object type and the stac version, using a similar technique as BASE_URIS.
    # Uris are contained in a tuple whose first element represents the URI of the latest
    # version, so that a search through version ranges is avoided if the STAC being validated
    # is the latest version. If it's a previous version, the stac_version that matches
    # the listed version range is used, or else the URI from the latest version is used if
    # there are no overrides for previous versions.
    DEFAULT_SCHEMA_MAP: Dict[str, Any] = {
        STACObjectType.CATALOG: ('catalog-spec/json-schema/catalog.json', None),
        STACObjectType.COLLECTION: ('collection-spec/json-schema/collection.json', None),
        STACObjectType.ITEM: ('item-spec/json-schema/item.json', None),
        STACObjectType.ITEMCOLLECTION: (None, [
            STACVersionRange(min_version='v0.8.0-rc1', max_version='0.9.0'),
            'item-spec/json-schema/itemcollection.json'
        ])
    }

    @classmethod
    def _append_base_uri_if_needed(cls, uri: str, stac_version: str) -> Optional[str]:
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

    def get_object_schema_uri(self, object_type: STACObjectType, stac_version: str) -> Optional[str]:
        uri = None
        is_latest = stac_version == ps.get_stac_version()

        if object_type not in self.DEFAULT_SCHEMA_MAP:
            raise KeyError('Unknown STAC object type {}'.format(object_type))

        uri = self.DEFAULT_SCHEMA_MAP[object_type][0]
        if not is_latest:
            if self.DEFAULT_SCHEMA_MAP[object_type][1]:
                for version_range, range_uri in self.DEFAULT_SCHEMA_MAP[object_type][1]:
                    if version_range.contains(stac_version):
                        uri = range_uri
                        break

        return self._append_base_uri_if_needed(uri, stac_version)
