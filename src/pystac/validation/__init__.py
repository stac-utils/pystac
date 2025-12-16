from __future__ import annotations

import warnings
from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Any, cast

import pystac
from pystac.serialization.identify import STACVersionID, identify_stac_object
from pystac.stac_object import STACObjectType
from pystac.utils import make_absolute_href
from pystac.validation.schema_uri_map import OldExtensionSchemaUriMap
from pystac.validation.stac_validator import GetSchemaError

if TYPE_CHECKING:
    from pystac.stac_object import STACObject


# Import after above class definition
from pystac.validation.stac_validator import JsonSchemaSTACValidator, STACValidator

__all__ = [
    "GetSchemaError",
    "JsonSchemaSTACValidator",
    "RegisteredValidator",
    "validate",
    "validate_all",
    "validate_dict",
    "validate_all_dict",
    "set_validator",
]


def validate(
    stac_object: STACObject,
    validator: STACValidator | None = None,
) -> list[Any]:
    """Validates a :class:`~pystac.STACObject`.

    Args:
        stac_object : The stac object to validate.
        validator : A custom validator to use for validation of the STAC object.
            If omitted, the default validator from
            :class:`~pystac.validation.RegisteredValidator`
            will be used instead.

    Returns:
        List[Any]: List of return values from the validation calls for the
           core object and any extensions. Element type is specific to the
           STACValidator implementation.

    Raises:
        STACValidationError
    """
    return validate_dict(
        stac_dict=stac_object.to_dict(),
        stac_object_type=stac_object.STAC_OBJECT_TYPE,
        stac_version=pystac.get_stac_version(),
        extensions=stac_object.stac_extensions,
        href=stac_object.get_self_href(),
        validator=validator,
    )


def validate_dict(
    stac_dict: dict[str, Any],
    stac_object_type: STACObjectType | None = None,
    stac_version: str | None = None,
    extensions: list[str] | None = None,
    href: str | None = None,
    validator: STACValidator | None = None,
) -> list[Any]:
    """Validate a stac object serialized as JSON into a dict.

    This method delegates to the call to
    :meth:`~pystac.validation.stac_validator.STACValidator.validate` for the
    :class:`~pystac.validation.stac_validator.STACValidator` registered
    via :func:`~pystac.validation.set_validator` or
    :class:`~pystac.validation.JsonSchemaSTACValidator` by default.

    Args:
        stac_dict : Dictionary that is the STAC json of the object.
        stac_object_type : The stac object type of the object encoded in stac_dict.
            One of :class:`~pystac.STACObjectType`. If not supplied, this will use
            PySTAC's identification logic to identify the object type.
        stac_version : The version of STAC to validate the object against. If not
            supplied, this will use PySTAC's identification logic to identify the stac
            version
        extensions : Extension IDs for this stac object. If not supplied,
            PySTAC's identification logic to identify the extensions.
        href : Optional HREF of the STAC object being validated.
        validator : A custom validator to use for validation of the STAC dictionary.
            If omitted, the default validator from
            :class:`~pystac.validation.RegisteredValidator`
            will be used instead.

    Returns:
        List[Any]: List of return values from the validation calls for the
           core object and any extensions. Element type is specific to the
           STACValidator implementation.

    Raises:
        STACValidationError
    """
    info = None
    if stac_object_type is None:
        info = identify_stac_object(stac_dict)
        stac_object_type = info.object_type
    if stac_version is None:
        if info is None:
            info = identify_stac_object(stac_dict)
        stac_version = str(info.version_range.latest_valid_version())
    if extensions is None:
        if info is None:
            info = identify_stac_object(stac_dict)
        extensions = list(info.extensions)

    stac_version_id = STACVersionID(stac_version)

    # If the version is before 1.0.0-rc.2, substitute extension short IDs for
    # their schemas.
    if stac_version_id < "1.0.0-rc.2":

        def _get_uri(ext: str) -> str | None:
            return OldExtensionSchemaUriMap.get_extension_schema_uri(
                ext,
                stac_object_type,
                stac_version_id,
            )

        extensions = [uri for uri in map(_get_uri, extensions) if uri is not None]

    validator = validator or RegisteredValidator.get_validator()
    return validator.validate(
        stac_dict, stac_object_type, stac_version, extensions, href
    )


def validate_all(
    stac_object: STACObject | dict[str, Any],
    href: str | None = None,
    stac_io: pystac.StacIO | None = None,
) -> None:
    """Validate a :class:`~pystac.STACObject`, or a STAC object serialized as
    JSON into a dict.

    If the STAC object represents a catalog or collection, this function will be
    called recursively for each child link and all contained items.

    Args:
        stac_object : STAC object to validate
        href : HREF of the STAC object being validated. Used for error
            reporting and resolving relative links.
        stac_io : Optional StacIO instance to use for reading hrefs. If None,
            the StacIO.default() instance is used.

    Raises:
        STACValidationError or ValueError: STACValidationError is raised
            if the STAC object or any contained catalog, collection,
            or item has a validation error. ValueError is raised
            if stac_object is a STACObject and href is not None, or if
            stac_object is a dict and href is None.
    """
    if stac_io is None:
        stac_io = pystac.StacIO.default()

    if isinstance(stac_object, dict):
        warnings.warn(
            "validating a STAC object as a dict is deprecated;"
            " use validate_all_dict instead",
            DeprecationWarning,
        )

        if href is None:
            raise ValueError(
                "href must be set if stac_object is a dict; it will be removed"
                " once support for validating a STAC object as a dict is removed from"
                " validate_all, due to the introduction of validate_all_dict"
            )

        validate_all_dict(stac_object, href, stac_io)
    elif href is not None:
        raise ValueError(
            "href must be None if stac_object is a STACObject; it will be removed"
            " once support for validating a STAC object as a dict is removed from"
            " validate_all, due to the introduction of validate_all_dict"
        )
    else:
        validate_all_dict(stac_object.to_dict(), stac_object.get_self_href(), stac_io)


def validate_all_dict(
    stac_dict: dict[str, Any],
    href: str | None,
    stac_io: pystac.StacIO | None = None,
) -> None:
    """Validate a stac object serialized as JSON into a dict.

    If the STAC object represents a catalog or collection, this function will be
    called recursively for each child link and all contained items.

    Args:
        stac_dict : Dictionary that is the STAC json of the object.
        href : HREF of the STAC object being validated. Used for error
            reporting and resolving relative links.
        stac_io : Optional StacIO instance to use for reading hrefs. If None,
            the StacIO.default() instance is used.

    Raises:
        STACValidationError: if the STAC object or any contained catalog, collection,
            or item has a validation error
    """
    if stac_io is None:
        stac_io = pystac.StacIO.default()

    info = identify_stac_object(stac_dict)

    # Validate this object
    validate_dict(
        stac_dict,
        stac_object_type=info.object_type,
        stac_version=str(info.version_range.latest_valid_version()),
        extensions=list(info.extensions),
        href=href,
    )

    if info.object_type != pystac.STACObjectType.ITEM and "links" in stac_dict:
        links = (
            # Account for 0.6 links
            stac_dict["links"].values()
            if isinstance(stac_dict["links"], dict)
            else stac_dict.get("links")
        )

        for link in cast(Iterable[Mapping[str, Any]], links):
            if link.get("rel") in [pystac.RelType.ITEM, pystac.RelType.CHILD]:
                link_href = make_absolute_href(
                    cast(str, link.get("href")), start_href=href
                )
                validate_all_dict(stac_io.read_json(link_href), link_href, stac_io)


class RegisteredValidator:
    _validator: STACValidator | None = None

    @classmethod
    def get_validator(cls) -> STACValidator:
        if cls._validator is None:
            try:
                import jsonschema as _  # noqa
            except ImportError:
                raise Exception(
                    "Cannot validate with default validator because package"
                    ' "jsonschema" is not installed. Install pystac with the validation'
                    " optional requirements (e.g. pip install pystac[validation]) to"
                    " install jsonschema"
                )
            cls._validator = JsonSchemaSTACValidator()

        return cls._validator

    @classmethod
    def set_validator(cls, validator: STACValidator) -> None:
        if not issubclass(type(validator), STACValidator):
            raise Exception(f"Validator must be a subclass of {STACValidator}")
        cls._validator = validator


def set_validator(validator: STACValidator) -> None:
    """Sets the STACValidator to use in PySTAC.

    Args:
        validator : The STACValidator implementation to use for
            validation.
    """
    RegisteredValidator.set_validator(validator)
