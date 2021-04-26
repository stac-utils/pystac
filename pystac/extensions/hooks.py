from abc import ABC, abstractmethod
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from typing import Any, Dict, Iterable, List, Optional, TYPE_CHECKING

from pystac.extensions import ExtensionError

if TYPE_CHECKING:
    from pystac.stac_object import STACObject as STACObject_Type


class ExtensionHooks(ABC):
    """

    Args:
        extension_schema_uri: The Schema URI that is used to validate the extension,
            but also act as the ID for the extension.
    """
    @property
    @abstractmethod
    def schema_uri(self) -> str:
        pass

    def get_object_links(self, obj: "STACObject_Type") -> Optional[List[str]]:
        return None

    def migrate(self, obj: Dict[str, Any], version: STACVersionID,
                      info: STACJSONDescription) -> None:
        pass

class RegisteredExtensionHooks:
    def __init__(self, hooks: Iterable[ExtensionHooks]):
        self.hooks = dict([(e.schema_uri, e) for e in hooks])

    def add_extension_hooks(self, hooks: ExtensionHooks) -> None:
        e_id = hooks.schema_uri
        if e_id in self.hooks:
            raise ExtensionError("ExtensionDefinition with id '{}' already exists.".format(e_id))

        self.hooks[e_id] = hooks

    def get_extended_object_links(self, obj: "STACObject_Type") -> List[str]:
        result: Optional[List[str]] = None
        for ext in obj.stac_extensions:
            if ext in self.hooks:
                ext_result = self.hooks[ext].get_object_links(obj)
                if ext_result is not None:
                    if result is None:
                        result = ext_result
                    else:
                        result.extend(ext_result)
        return result or []

    def migrate(self, obj: Dict[str, Any], version: STACVersionID,
                    info: STACJSONDescription) -> None:
        for hooks in self.hooks.values():
            hooks.migrate(obj, version, info)
