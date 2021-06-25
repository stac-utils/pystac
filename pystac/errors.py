from typing import Any, Optional, Union


class STACError(Exception):
    """A STACError is raised for errors relating to STAC, e.g. for
    invalid formats or trying to operate on a STAC that does not have
    the required information available.
    """

    pass


class STACTypeError(Exception):
    """A STACTypeError is raised when encountering a representation of
    a STAC entity that is not correct for the context; for example, if
    a Catalog JSON was read in as an Item.
    """

    pass


class DuplicateObjectKeyError(Exception):
    """Raised when deserializing a JSON object containing a duplicate key."""

    pass


class ExtensionTypeError(Exception):
    """An ExtensionTypeError is raised when an extension is used against
    an object that the extension does not apply to
    """

    pass


class ExtensionAlreadyExistsError(Exception):
    """An ExtensionAlreadyExistsError is raised when extension hooks
    are registered with PySTAC if there are already hooks registered
    for an extension with the same ID."""

    pass


class ExtensionNotImplemented(Exception):
    """Attempted to extend a STAC object that does not implement the given
    extension."""


class RequiredPropertyMissing(Exception):
    """This error is raised when a required value was expected
    to be there but was missing or None. This will happen, for example,
    in an extension that has required properties, where the required
    property is missing from the extended object

    Args:
        obj: Description of the object that will have a property missing.
            Should include a __repr__ that identifies the object for the
            error message, or be a string that describes the object.
        prop: The property that is missing
    """

    def __init__(
        self, obj: Union[str, Any], prop: str, msg: Optional[str] = None
    ) -> None:
        msg = msg or f"{repr(obj)} does not have required property {prop}"
        super().__init__(msg)


class STACValidationError(Exception):
    """Represents a validation error. Thrown by validation calls if the STAC JSON
    is invalid.

    Args:
        source : Source of the exception. Type will be determined by the
            validation implementation. For the default JsonSchemaValidator this will a
            the ``jsonschema.ValidationError``.
    """

    def __init__(self, message: str, source: Optional[Any] = None):
        super().__init__(message)
        self.source = source
