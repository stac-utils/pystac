from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import pystac
from pystac.extensions.base import VERSION_REGEX
from pystac.serialization.identify import STACJSONDescription, STACVersionID

if TYPE_CHECKING:
    from pystac.stac_object import STACObject


class ExtensionHooks(ABC):
    @property
    @abstractmethod
    def schema_uri(self) -> str:
        """The schema_uri for the current version of this extension"""
        raise NotImplementedError

    @property
    @abstractmethod
    def prev_extension_ids(self) -> set[str]:
        """A set of previous extension IDs (schema URIs or old short ids)
        that should be migrated to the latest schema URI in the 'stac_extensions'
        property. Override with a class attribute so that the set of previous
        IDs is only created once.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def stac_object_types(self) -> set[pystac.STACObjectType]:
        """A set of STACObjectType for which migration logic will be applied."""
        raise NotImplementedError

    @lru_cache
    def _get_stac_object_types(self) -> set[str]:
        """Translation of stac_object_types to strings, cached"""
        return {x.value for x in self.stac_object_types}

    def get_object_links(self, obj: STACObject) -> list[str | pystac.RelType] | None:
        return None

    def has_extension(self, obj: dict[str, Any]) -> bool:
        schema_startswith = VERSION_REGEX.split(self.schema_uri)[0] + "/"
        return any(
            uri.startswith(schema_startswith) or uri in self.prev_extension_ids
            for uri in obj.get("stac_extensions", [])
        )

    def migrate(
        self, obj: dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        """Migrate a STAC Object in dict format from a previous version.
        The base implementation will update the stac_extensions to the latest
        schema ID. This method will only be called for STAC objects that have been
        identified as a previous version of STAC. Implementations should directly
        manipulate the obj dict. Remember to call super() in order to change out
        the old 'stac_extension' entry with the latest schema URI.
        """
        # Migrate schema versions
        for prev_id in self.prev_extension_ids:
            if prev_id in info.extensions:
                try:
                    i = obj["stac_extensions"].index(prev_id)
                    obj["stac_extensions"][i] = self.schema_uri
                except ValueError:
                    obj["stac_extensions"].append(self.schema_uri)
                break


class RegisteredExtensionHooks:
    hooks: dict[str, ExtensionHooks]

    def __init__(self, hooks: Iterable[ExtensionHooks]):
        self.hooks = {e.schema_uri: e for e in hooks}

    def add_extension_hooks(self, hooks: ExtensionHooks) -> None:
        e_id = hooks.schema_uri
        if e_id in self.hooks:
            raise pystac.ExtensionAlreadyExistsError(
                f"ExtensionDefinition with id '{e_id}' already exists."
            )

        self.hooks[e_id] = hooks

    def remove_extension_hooks(self, extension_id: str) -> None:
        if extension_id in self.hooks:
            del self.hooks[extension_id]

    def get_extended_object_links(self, obj: STACObject) -> list[str | pystac.RelType]:
        result: list[str | pystac.RelType] | None = None
        for ext in obj.stac_extensions:
            if ext in self.hooks:
                ext_result = self.hooks[ext].get_object_links(obj)
                if ext_result is not None:
                    if result is None:
                        result = ext_result
                    else:
                        result.extend(ext_result)
        return result or []

    def migrate(
        self, obj: dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        for hooks in self.hooks.values():
            if info.object_type in hooks._get_stac_object_types():
                hooks.migrate(obj, version, info)
