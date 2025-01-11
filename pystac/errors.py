from typing import Any


class TemplateError(Exception):
    """Exception thrown when an error occurs during converting a template
    string into data for :class:`~pystac.layout.LayoutTemplate`
    """

    pass


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

    def __init__(
        self,
        bad_dict: dict[str, Any],
        expected: type,
        extra_message: str | None = "",
    ):
        """
        Construct an exception with an appropriate error message from bad_dict and the
        expected that it didn't align with.

        Args:
            bad_dict: Dictionary that did not match the expected type
            expected: The expected type.
            extra_message: message that will be appended to the exception message.
        """
        message = (
            f"JSON (id = {bad_dict.get('id', 'unknown')}) does not represent"
            f" a {expected.__name__} instance."
        )
        if extra_message:
            message += " " + extra_message
        super().__init__(message)


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

    def __init__(self, obj: str | Any, prop: str, msg: str | None = None) -> None:
        msg = msg or f"{repr(obj)} does not have required property {prop}"
        super().__init__(msg)


class STACLocalValidationError(Exception):
    """Schema not available locally"""


class STACValidationError(Exception):
    """Represents a validation error. Thrown by validation calls if the STAC JSON
    is invalid.

    Args:
        source : Source of the exception. Type will be determined by the
            validation implementation. For the default JsonSchemaValidator this will a
            the ``jsonschema.ValidationError``.
    """

    def __init__(self, message: str, source: Any | None = None):
        super().__init__(message)
        self.source = source


class DeprecatedWarning(FutureWarning):
    """Issued when converting a dictionary to a STAC Item or Collection and the
    version extension ``deprecated`` field is present and set to ``True``."""

    pass
