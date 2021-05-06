from abc import ABC, abstractmethod
from typing import Generic, Iterable, List, Optional, Dict, Any, Type, TypeVar, Union

import pystac


class SummariesExtension:
    def __init__(self, collection: pystac.Collection) -> None:
        self.summaries = collection.summaries

    def _set_summary(
        self,
        prop_key: str,
        v: Optional[Union[List[Any], pystac.RangeSummary[Any], Dict[str, Any]]],
    ) -> None:
        if v is None:
            self.summaries.remove(prop_key)
        else:
            self.summaries.add(prop_key, v)


P = TypeVar("P")


class PropertiesExtension(ABC):
    properties: Dict[str, Any]
    additional_read_properties: Optional[Iterable[Dict[str, Any]]] = None

    def _get_property(self, prop_name: str, typ: Type[P] = Type[Any]) -> Optional[P]:
        result: Optional[typ] = self.properties.get(prop_name)
        if result is not None:
            return result
        if self.additional_read_properties is not None:
            for props in self.additional_read_properties:
                result = props.get(prop_name)
                if result is not None:
                    return result
        return None

    def _set_property(
        self, prop_name: str, v: Optional[Any], pop_if_none: bool = True
    ) -> None:
        if v is None and pop_if_none:
            self.properties.pop(prop_name, None)
        else:
            self.properties[prop_name] = v


S = TypeVar("S", bound=pystac.STACObject)


class ExtensionManagementMixin(Generic[S], ABC):
    @classmethod
    @abstractmethod
    def get_schema_uri(cls) -> str:
        pass

    @classmethod
    def add_to(cls, obj: S) -> None:
        if obj.stac_extensions is None:
            obj.stac_extensions = [cls.get_schema_uri()]
        else:
            obj.stac_extensions.append(cls.get_schema_uri())

    @classmethod
    def remove_from(cls, obj: S) -> None:
        if obj.stac_extensions is not None:
            obj.stac_extensions = [
                uri for uri in obj.stac_extensions if uri != cls.get_schema_uri()
            ]

    @classmethod
    def has_extension(cls, obj: S) -> bool:
        return (
            obj.stac_extensions is not None
            and cls.get_schema_uri() in obj.stac_extensions
        )
