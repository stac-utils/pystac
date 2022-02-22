from abc import ABC, abstractmethod
from typing import (
    cast,
    Generic,
    Iterable,
    List,
    Optional,
    Dict,
    Any,
    Type,
    TypeVar,
    Union,
)

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
    """The properties that this extension wraps.

    The extension which implements PropertiesExtension can use ``_get_property`` and
    ``_set_property`` to get and set values on this instance. Note that _set_properties
    mutates the properties directly."""

    additional_read_properties: Optional[Iterable[Dict[str, Any]]] = None
    """Additional read-only properties accessible from the extended object.

    These are used when extending an :class:`~pystac.Asset` to give access to the
    properties of the owning :class:`~pystac.Item`. If a property exists in both
    ``additional_read_properties`` and ``properties``, the value in
    ``additional_read_properties`` will take precedence.
    """

    def _get_property(self, prop_name: str, _typ: Type[P]) -> Optional[P]:
        maybe_property: Optional[P] = self.properties.get(prop_name)
        if maybe_property is not None:
            return maybe_property
        if self.additional_read_properties is not None:
            for props in self.additional_read_properties:
                maybe_additional_property: Optional[P] = props.get(prop_name)
                if maybe_additional_property is not None:
                    return maybe_additional_property
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
    """Abstract base class with methods for adding and removing extensions from STAC
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
        raise NotImplementedError

    @classmethod
    def add_to(cls, obj: S) -> None:
        """Add the schema URI for this extension to the
        :attr:`~pystac.STACObject.stac_extensions` list for the given object, if it is
        not already present."""
        if obj.stac_extensions is None:
            obj.stac_extensions = [cls.get_schema_uri()]
        elif cls.get_schema_uri() not in obj.stac_extensions:
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

    @classmethod
    def validate_owner_has_extension(
        cls, asset: pystac.Asset, add_if_missing: bool
    ) -> None:
        """Given an :class:`~pystac.Asset`, checks if the asset's owner has this
        extension's schema URI in its :attr:`~pystac.STACObject.stac_extensions` list.
        If ``add_if_missing`` is ``True``, the schema URI will be added to the owner.

        Raises:
            STACError : If ``add_if_missing`` is ``True`` and ``asset.owner`` is
                ``None``.
        """
        if asset.owner is None:
            if add_if_missing:
                raise pystac.STACError(
                    "Attempted to use add_if_missing=True for an Asset with no owner. "
                    "Use Asset.set_owner or set add_if_missing=False."
                )
            else:
                return
        return cls.validate_has_extension(cast(S, asset.owner), add_if_missing)

    @classmethod
    def validate_has_extension(cls, obj: S, add_if_missing: bool) -> None:
        """Given a :class:`~pystac.STACObject`, checks if the object has this
        extension's schema URI in its :attr:`~pystac.STACObject.stac_extensions` list.
        If ``add_if_missing`` is ``True``, the schema URI will be added to the object.

        Args:
            obj : The object to validate.
            add_if_missing : Whether to add the schema URI to the object if it is
                not already present.
        """
        if add_if_missing:
            cls.add_to(obj)

        if cls.get_schema_uri() not in obj.stac_extensions:
            raise pystac.ExtensionNotImplemented(
                f"Could not find extension schema URI {cls.get_schema_uri()} in object."
            )
