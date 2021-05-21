from abc import ABC, abstractmethod
from typing import Generic, Iterable, List, Optional, Dict, Any, Type, TypeVar, Union

import pystac


class SummariesExtension:
    """Base class for extending the properties in :attr:`pystac.Collection.summaries`
    to include properties defined by a STAC Extension.

    This class should generally not be instantiated directly. Instead, create an
    extension-specific class that inherits from this class and instantiate that. See
    :class:`~pystac.extensions.eo.SummariesEOExtension` for an example."""

    summaries: pystac.Summaries
    """The summaries for the :class:`~pystac.Collection` being extended."""

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
    """Abstract base class for extending the properties of an :class:`~pystac.Item`
    to include properties defined by a STAC Extension.

    This class should not be instantiated directly. Instead, create an
    extension-specific class that inherits from this class and instantiate that. See
    :class:`~pystac.extensions.eo.PropertiesEOExtension` for an example.
    """

    properties: Dict[str, Any]
    """Additional properties associated with this extension."""

    additional_read_properties: Optional[Iterable[Dict[str, Any]]] = None
    """Additional read-only properties accessible from the extended object. These are
    used when extending a :class:`~pystac.Asset` to give access to the properties of
    the owning :class:`~pystac.Item`."""

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
    """Abstract base class with tools for adding and removing extensions from STAC
    Objects. This class is generic over the type of object being extended (e.g.
    :class:`~pystac.Item`).

    Concrete extension implementations should inherit from this class and either
    provide a concrete type or a bounded type variable.

    See :class:`~pystac.extensions.eo.EOExtension` for an example implementation.
    """

    @classmethod
    @abstractmethod
    def get_schema_uri(cls) -> str:
        """Gets the schema URI associated with this extension."""
        pass

    @classmethod
    def add_to(cls, obj: S) -> None:
        """Add the schema URI for this extension to the
        :attr:`pystac.STACObject.stac_extensions` list for the given object."""
        if obj.stac_extensions is None:
            obj.stac_extensions = [cls.get_schema_uri()]
        else:
            obj.stac_extensions.append(cls.get_schema_uri())

    @classmethod
    def remove_from(cls, obj: S) -> None:
        """Remove the schema URI for this extension from the
        :attr:`pystac.STACObject.stac_extensions` list for the given object."""
        if obj.stac_extensions is not None:
            obj.stac_extensions = [
                uri for uri in obj.stac_extensions if uri != cls.get_schema_uri()
            ]

    @classmethod
    def has_extension(cls, obj: S) -> bool:
        """Check if the given object implements this extension by checking
        :attr:`pystac.STACObject.stac_extensions` for this extension's schema URI."""
        return (
            obj.stac_extensions is not None
            and cls.get_schema_uri() in obj.stac_extensions
        )
