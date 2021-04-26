from abc import ABC
from typing import Generic, Iterable, Optional, Dict, Any, Type, TypeVar

import pystac as ps


class ExtensionException(Exception):
    pass


P = TypeVar('P')

class PropertiesExtension(ABC):
    properties: Dict[str, Any]
    additional_read_properties: Optional[Iterable[Dict[str, Any]]] = None

    def _get_property(self, prop_name: str, typ: Type[P] = Any) -> Optional[P]:
        result: Optional[typ] = self.properties.get(prop_name)
        if result is not None:
            return result
        if self.additional_read_properties is not None:
            for props in self.additional_read_properties:
                result = props.get(prop_name)
                if result is not None:
                    return result
        return None

    def _set_property(self, prop_name: str, v: Optional[Any], pop_if_none: bool = True) -> None:
        if v is None and pop_if_none:
            self.properties.pop(prop_name, None)
        else:
            self.properties[prop_name] = v


S = TypeVar('S', bound=ps.STACObject)


class EnableExtensionMixin(Generic[S]):
    obj: S
    schema_uri: str

    def add_extension(self) -> None:
        if self.obj.stac_extensions is None:
            self.obj.stac_extensions = [self.schema_uri]
        else:
            self.obj.stac_extensions.append(self.schema_uri)

    def remove_extension(self) -> None:
        if self.obj.stac_extensions is not None:
            self.obj.stac_extensions = [
                uri for uri in self.obj.stac_extensions if uri != self.schema_uri
            ]

    @property
    def has_extension(self) -> bool:
        return (self.obj.stac_extensions is not None
                and self.schema_uri in self.obj.stac_extensions)
