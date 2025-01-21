from __future__ import annotations

import re
import warnings
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import (
    Any,
    Generic,
    TypeVar,
    cast,
)

import pystac
from pystac.stac_object import S

VERSION_REGEX = re.compile("/v[0-9].[0-9].*/")


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
        v: list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None,
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
    :class:`~pystac.extensions.eo.EOExtension` for an example.
    """

    properties: dict[str, Any]
    """The properties that this extension wraps.

    The extension which implements PropertiesExtension can use ``_get_property`` and
    ``_set_property`` to get and set values on this instance. Note that _set_properties
    mutates the properties directly."""

    additional_read_properties: Iterable[dict[str, Any]] | None = None
    """Additional read-only properties accessible from the extended object.

    These are used when extending an :class:`~pystac.Asset` to give access to the
    properties of the owning :class:`~pystac.Item`. If a property exists in both
    ``additional_read_properties`` and ``properties``, the value in
    ``additional_read_properties`` will take precedence.
    """

    def _get_property(self, prop_name: str, _typ: type[P]) -> P | None:
        maybe_property: P | None = self.properties.get(prop_name)
        if maybe_property is not None:
            return maybe_property
        if self.additional_read_properties is not None:
            for props in self.additional_read_properties:
                maybe_additional_property: P | None = props.get(prop_name)
                if maybe_additional_property is not None:
                    return maybe_additional_property
        return None

    def _set_property(
        self, prop_name: str, v: Any | None, pop_if_none: bool = True
    ) -> None:
        if v is None and pop_if_none:
            self.properties.pop(prop_name, None)
        elif isinstance(v, list):
            self.properties[prop_name] = [
                x.to_dict() if hasattr(x, "to_dict") else x for x in v
            ]
        else:
            self.properties[prop_name] = v


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
    def get_schema_uris(cls) -> list[str]:
        """Gets a list of schema URIs associated with this extension."""
        warnings.warn(
            "get_schema_uris is deprecated and will be removed in v2",
            DeprecationWarning,
        )
        return [cls.get_schema_uri()]

    @classmethod
    def add_to(cls, obj: S) -> None:
        """Add the schema URI for this extension to the
        :attr:`~pystac.STACObject.stac_extensions` list for the given object, if it is
        not already present."""
        if obj.stac_extensions is None:
            obj.stac_extensions = [cls.get_schema_uri()]
        elif not cls.has_extension(obj):
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
        schema_startswith = VERSION_REGEX.split(cls.get_schema_uri())[0] + "/"

        return obj.stac_extensions is not None and any(
            uri.startswith(schema_startswith) for uri in obj.stac_extensions
        )

    @classmethod
    def validate_owner_has_extension(
        cls,
        asset: pystac.Asset | pystac.ItemAssetDefinition,
        add_if_missing: bool = False,
    ) -> None:
        """
        DEPRECATED

        .. deprecated:: 1.9
            Use :meth:`ensure_owner_has_extension` instead.

        Given an :class:`~pystac.Asset`, checks if the asset's owner has this
        extension's schema URI in its :attr:`~pystac.STACObject.stac_extensions` list.
        If ``add_if_missing`` is ``True``, the schema URI will be added to the owner.

        Args:
            asset : The asset whose owner should be validated.
            add_if_missing : Whether to add the schema URI to the owner if it is
                not already present. Defaults to False.

        Raises:
            STACError : If ``add_if_missing`` is ``True`` and ``asset.owner`` is
                ``None``.
        """
        warnings.warn(
            "ensure_owner_has_extension is deprecated. "
            "Use ensure_owner_has_extension instead",
            DeprecationWarning,
        )
        return cls.ensure_owner_has_extension(asset, add_if_missing)

    @classmethod
    def ensure_owner_has_extension(
        cls,
        asset_or_link: pystac.Asset | pystac.ItemAssetDefinition | pystac.Link,
        add_if_missing: bool = False,
    ) -> None:
        """Given an :class:`~pystac.Asset`, checks if the asset's owner has this
        extension's schema URI in its :attr:`~pystac.STACObject.stac_extensions` list.
        If ``add_if_missing`` is ``True``, the schema URI will be added to the owner.

        Args:
            asset : The asset whose owner should be validated.
            add_if_missing : Whether to add the schema URI to the owner if it is
                not already present. Defaults to False.

        Raises:
            STACError : If ``add_if_missing`` is ``True`` and ``asset.owner`` is
                ``None``.
        """
        if asset_or_link.owner is None:
            if add_if_missing:
                raise pystac.STACError(
                    f"Attempted to use add_if_missing=True for a {type(asset_or_link)} "
                    "with no owner. Use .set_owner or set add_if_missing=False."
                )
            else:
                return
        return cls.ensure_has_extension(cast(S, asset_or_link.owner), add_if_missing)

    @classmethod
    def validate_has_extension(cls, obj: S, add_if_missing: bool = False) -> None:
        """
        DEPRECATED

        .. deprecated:: 1.9
            Use :meth:`ensure_has_extension` instead.

        Given a :class:`~pystac.STACObject`, checks if the object has this
        extension's schema URI in its :attr:`~pystac.STACObject.stac_extensions` list.
        If ``add_if_missing`` is ``True``, the schema URI will be added to the object.

        Args:
            obj : The object to validate.
            add_if_missing : Whether to add the schema URI to the object if it is
                not already present. Defaults to False.
        """
        warnings.warn(
            "validate_has_extension is deprecated. Use ensure_has_extension instead",
            DeprecationWarning,
        )

        return cls.ensure_has_extension(obj, add_if_missing)

    @classmethod
    def ensure_has_extension(cls, obj: S, add_if_missing: bool = False) -> None:
        """Given a :class:`~pystac.STACObject`, checks if the object has this
        extension's schema URI in its :attr:`~pystac.STACObject.stac_extensions` list.
        If ``add_if_missing`` is ``True``, the schema URI will be added to the object.

        Args:
            obj : The object to validate.
            add_if_missing : Whether to add the schema URI to the object if it is
                not already present. Defaults to False.
        """
        if add_if_missing:
            cls.add_to(obj)

        if not cls.has_extension(obj):
            name = getattr(cls, "name", cls.__name__)
            suggestion = (
                f"``obj.ext.add('{name}')"
                if hasattr(cls, "name")
                else f"``{name}.add_to(obj)``"
            )

            raise pystac.ExtensionNotImplemented(
                f"Extension '{name}' is not implemented on object."
                f"STAC producers can add the extension using {suggestion}"
            )

    @classmethod
    def _ext_error_message(cls, obj: Any) -> str:
        contents = [f"{cls.__name__} does not apply to type '{type(obj).__name__}'"]
        if hasattr(cls, "summaries") and isinstance(obj, pystac.Collection):
            hint = f"Hint: Did you mean to use `{cls.__name__}.summaries` instead?"
            contents.append(hint)
        return ". ".join(contents)
