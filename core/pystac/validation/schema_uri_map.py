from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import lru_cache
from typing import Any

import pystac
from pystac.serialization import STACVersionRange
from pystac.serialization.identify import OldExtensionShortIDs, STACVersionID
from pystac.stac_object import STACObjectType


class SchemaUriMap(ABC):
    """Abstract class defining schema URIs for STAC core objects and extensions."""

    def __init__(self) -> None:
        pass

    @abstractmethod
    def get_object_schema_uri(
        self, object_type: STACObjectType, stac_version: str
    ) -> str | None:
        """Get the schema URI for the given object type and stac version.

        Args:
            object_type : STAC object type. One of
                :class:`~pystac.STACObjectType`
            stac_version : The STAC version of the schema to return.

        Returns:
            str: The URI of the schema, or None if not found.
        """
        raise NotImplementedError


class DefaultSchemaUriMap(SchemaUriMap):
    """Implementation of SchemaUriMap that uses schemas hosted by stacspec.org

    For STAC Versions 0.9.0 or earlier this will use the schemas hosted on the
    radiantearth/stac-spec GitHub repo.
    """

    # BASE_URIS contains a list of tuples, the first element is a version range and the
    # second being the base URI for schemas for that range. The schema URI of a STAC
    # for a particular version uses the base URI associated with the version range which
    # contains it. If the version it outside of any VersionRange, there is no URI for
    # the schema.
    BASE_URIS: list[tuple[STACVersionRange, Callable[[str], str]]] = [
        (
            STACVersionRange(min_version="1.0.0-beta.2"),
            lambda version: f"https://schemas.stacspec.org/v{version}",
        ),
        (
            STACVersionRange(min_version="0.8.0", max_version="1.0.0-beta.1"),
            lambda version: (
                f"https://raw.githubusercontent.com/radiantearth/stac-spec/v{version}"
            ),
        ),
    ]

    # DEFAULT_SCHEMA_MAP contains a structure that matches 'core' or 'extension' schema
    # URIs based on the stac object type and the stac version, using a similar
    # technique as BASE_URIS. Uris are contained in a tuple whose first element
    # represents the URI of the latest version, so that a search through version
    # ranges is avoided if the STAC being validated
    # is the latest version. If it's a previous version, the stac_version that matches
    # the listed version range is used, or else the URI from the latest version is used
    # if there are no overrides for previous versions.
    DEFAULT_SCHEMA_MAP: dict[str, Any] = {
        STACObjectType.CATALOG: ("catalog-spec/json-schema/catalog.json", None),
        STACObjectType.COLLECTION: (
            "collection-spec/json-schema/collection.json",
            None,
        ),
        STACObjectType.ITEM: ("item-spec/json-schema/item.json", None),
    }

    @classmethod
    def _append_base_uri_if_needed(cls, uri: str, stac_version: str) -> str | None:
        # Only append the base URI if it's not already an absolute URI
        if "://" not in uri:
            for version_range, f in cls.BASE_URIS:
                if version_range.contains(stac_version):
                    base_uri = f(stac_version)
                    return f"{base_uri}/{uri}"

            # We don't have JSON schema validation for this version of PySTAC
            return None
        else:
            return uri

    def get_object_schema_uri(
        self, object_type: STACObjectType, stac_version: str
    ) -> str | None:
        is_latest = stac_version == pystac.get_stac_version()

        if object_type not in self.DEFAULT_SCHEMA_MAP:
            raise KeyError(f"Unknown STAC object type {object_type}")
        uri = self.DEFAULT_SCHEMA_MAP[object_type][0]
        if not is_latest:
            if self.DEFAULT_SCHEMA_MAP[object_type][1]:
                for version_range, range_uri in self.DEFAULT_SCHEMA_MAP[object_type][1]:
                    if version_range.contains(stac_version):
                        uri = range_uri
                        break

        return self._append_base_uri_if_needed(uri, stac_version)


class OldExtensionSchemaUriMap:
    """Ties old extension IDs to schemas hosted by https://schemas.stacspec.org.

    For STAC Versions 0.9.0 or earlier this will use the schemas hosted on the
    radiantearth/stac-spec GitHub repo.
    """

    # BASE_URIS contains a list of tuples, the first element is a version range and the
    # second being the base URI for schemas for that range. The schema URI of a STAC
    # for a particular version uses the base URI associated with the version range which
    # contains it. If the version it outside of any VersionRange, there is no URI for
    # the schema.
    @classmethod
    @lru_cache
    def get_base_uris(
        cls,
    ) -> list[tuple[STACVersionRange, Callable[[STACVersionID], str]]]:
        return [
            (
                STACVersionRange(min_version="1.0.0-beta.2"),
                lambda version: f"https://schemas.stacspec.org/v{version}",
            ),
            (
                STACVersionRange(min_version="0.8.0", max_version="1.0.0-beta.1"),
                lambda version: (
                    "https://raw.githubusercontent.com/"
                    f"radiantearth/stac-spec/v{version}"
                ),
            ),
        ]

    # DEFAULT_SCHEMA_MAP contains a structure that matches extension schema URIs
    # based on the stac object type, extension ID and the stac version.
    # Uris are contained in a tuple whose first element represents the URI of the latest
    # version, so that a search through version ranges is avoided if the STAC being
    # validated is the latest version. If it's a previous version, the stac_version
    # that matches the listed version range is used, or else the URI from the latest
    # version is used if there are no overrides for previous versions.
    @classmethod
    @lru_cache
    def get_schema_map(cls) -> dict[str, Any]:
        return {
            OldExtensionShortIDs.CHECKSUM.value: (
                {
                    pystac.STACObjectType.CATALOG: (
                        "extensions/checksum/json-schema/schema.json"
                    ),
                    pystac.STACObjectType.COLLECTION: (
                        "extensions/checksum/json-schema/schema.json"
                    ),
                    pystac.STACObjectType.ITEM: (
                        "extensions/checksum/json-schema/schema.json"
                    ),
                },
                None,
            ),
            OldExtensionShortIDs.COLLECTION_ASSETS.value: (
                {
                    pystac.STACObjectType.COLLECTION: (
                        "extensions/collection-assets/json-schema/schema.json"
                    )
                },
                None,
            ),
            OldExtensionShortIDs.DATACUBE.value: (
                {
                    pystac.STACObjectType.COLLECTION: (
                        "extensions/datacube/json-schema/schema.json"
                    ),
                    pystac.STACObjectType.ITEM: (
                        "extensions/datacube/json-schema/schema.json"
                    ),
                },
                [
                    (
                        STACVersionRange(min_version="0.5.0", max_version="0.9.0"),
                        {
                            pystac.STACObjectType.COLLECTION: None,
                            pystac.STACObjectType.ITEM: None,
                        },
                    )
                ],
            ),
            OldExtensionShortIDs.EO.value: (
                {pystac.STACObjectType.ITEM: "extensions/eo/json-schema/schema.json"},
                None,
            ),
            OldExtensionShortIDs.ITEM_ASSETS.value: (
                {
                    pystac.STACObjectType.COLLECTION: (
                        "extensions/item-assets/json-schema/schema.json"
                    )
                },
                None,
            ),
            OldExtensionShortIDs.LABEL.value: (
                {
                    pystac.STACObjectType.ITEM: (
                        "extensions/label/json-schema/schema.json"
                    )
                },
                [
                    (
                        STACVersionRange(min_version="0.8.0-rc1", max_version="0.8.1"),
                        {pystac.STACObjectType.ITEM: "extensions/label/schema.json"},
                    )
                ],
            ),
            OldExtensionShortIDs.POINTCLOUD.value: (
                # Invalid schema
                None,
                None,
            ),
            OldExtensionShortIDs.PROJECTION.value: (
                {
                    pystac.STACObjectType.ITEM: (
                        "extensions/projection/json-schema/schema.json"
                    )
                },
                None,
            ),
            OldExtensionShortIDs.SAR.value: (
                {pystac.STACObjectType.ITEM: "extensions/sar/json-schema/schema.json"},
                None,
            ),
            OldExtensionShortIDs.SAT.value: (
                {pystac.STACObjectType.ITEM: "extensions/sat/json-schema/schema.json"},
                None,
            ),
            OldExtensionShortIDs.SCIENTIFIC.value: (
                {
                    pystac.STACObjectType.ITEM: (
                        "extensions/scientific/json-schema/schema.json"
                    ),
                    pystac.STACObjectType.COLLECTION: (
                        "extensions/scientific/json-schema/schema.json"
                    ),
                },
                None,
            ),
            OldExtensionShortIDs.SINGLE_FILE_STAC.value: (
                {
                    pystac.STACObjectType.CATALOG: (
                        "extensions/single-file-stac/json-schema/schema.json"
                    )
                },
                None,
            ),
            OldExtensionShortIDs.TILED_ASSETS.value: (
                {
                    pystac.STACObjectType.CATALOG: (
                        "extensions/tiled-assets/json-schema/schema.json"
                    ),
                    pystac.STACObjectType.COLLECTION: (
                        "extensions/tiled-assets/json-schema/schema.json"
                    ),
                    pystac.STACObjectType.ITEM: (
                        "extensions/tiled-assets/json-schema/schema.json"
                    ),
                },
                None,
            ),
            OldExtensionShortIDs.TIMESTAMPS.value: (
                {
                    pystac.STACObjectType.ITEM: (
                        "extensions/timestamps/json-schema/schema.json"
                    )
                },
                None,
            ),
            OldExtensionShortIDs.VERSION.value: (
                {
                    pystac.STACObjectType.ITEM: (
                        "extensions/version/json-schema/schema.json"
                    ),
                    pystac.STACObjectType.COLLECTION: (
                        "extensions/version/json-schema/schema.json"
                    ),
                },
                None,
            ),
            OldExtensionShortIDs.VIEW.value: (
                {pystac.STACObjectType.ITEM: "extensions/view/json-schema/schema.json"},
                None,
            ),
            # Removed or renamed extensions.
            "dtr": (None, None),  # Invalid schema
            "asset": (
                None,
                [
                    (
                        STACVersionRange(min_version="0.8.0-rc1", max_version="0.9.0"),
                        {
                            pystac.STACObjectType.COLLECTION: (
                                "extensions/asset/json-schema/schema.json"
                            )
                        },
                    )
                ],
            ),
        }

    @classmethod
    def _append_base_uri_if_needed(
        cls, uri: str, stac_version: STACVersionID
    ) -> str | None:
        # Only append the base URI if it's not already an absolute URI
        if "://" not in uri:
            for version_range, f in cls.get_base_uris():
                if version_range.contains(stac_version):
                    base_uri = f(stac_version)
                    return f"{base_uri}/{uri}"

            # No JSON Schema for the old extension
            return None
        else:
            return uri

    @classmethod
    def get_extension_schema_uri(
        cls, extension_id: str, object_type: STACObjectType, stac_version: STACVersionID
    ) -> str | None:
        uri = None

        is_latest = stac_version == pystac.get_stac_version()

        ext_map = cls.get_schema_map()
        if extension_id in ext_map:
            if ext_map[extension_id][0] and object_type in ext_map[extension_id][0]:
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
