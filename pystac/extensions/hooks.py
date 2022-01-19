from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Set, TYPE_CHECKING, Union

import pystac
from pystac.serialization.identify import STACJSONDescription, STACVersionID

if TYPE_CHECKING:
    from pystac.stac_object import STACObject as STACObject_Type


class ExtensionHooks(ABC):
    @property
    @abstractmethod
    def schema_uri(self) -> str:
        """The schema_uri for the current version of this extension"""
        raise NotImplementedError

    @property
    @abstractmethod
    def prev_extension_ids(self) -> Set[str]:
        """A set of previous extension IDs (schema URIs or old short ids)
        that should be migrated to the latest schema URI in the 'stac_extensions'
        property. Override with a class attribute so that the set of previous
        IDs is only created once.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def stac_object_types(self) -> Set[pystac.STACObjectType]:
        """A set of STACObjectType for which migration logic will be applied."""
        raise NotImplementedError

    @lru_cache()
    def _get_stac_object_types(self) -> Set[str]:
        """Translation of stac_object_types to strings, cached"""
        return set([x.value for x in self.stac_object_types])

    def get_object_links(
        self, obj: "STACObject_Type"
    ) -> Optional[List[Union[str, pystac.RelType]]]:
        return None

    def migrate(
        self, obj: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
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
    hooks: Dict[str, ExtensionHooks]

    def __init__(self, hooks: Iterable[ExtensionHooks]):
        self.hooks = dict([(e.schema_uri, e) for e in hooks])

    def add_extension_hooks(self, hooks: ExtensionHooks) -> None:
        e_id = hooks.schema_uri
        if e_id in self.hooks:
            raise pystac.ExtensionAlreadyExistsError(
                "ExtensionDefinition with id '{}' already exists.".format(e_id)
            )

        self.hooks[e_id] = hooks

    def remove_extension_hooks(self, extension_id: str) -> None:
        if extension_id in self.hooks:
            del self.hooks[extension_id]

    def get_extended_object_links(
        self, obj: "STACObject_Type"
    ) -> List[Union[str, pystac.RelType]]:
        result: Optional[List[Union[str, pystac.RelType]]] = None
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
        self, obj: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        for hooks in self.hooks.values():
            if info.object_type in hooks._get_stac_object_types():
                hooks.migrate(obj, version, info)
