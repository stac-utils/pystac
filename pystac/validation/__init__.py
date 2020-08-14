# flake8: noqa
import pystac
from pystac.serialization.identify import identify_stac_object

from pystac.validation.schema_uri_map import (SchemaUriMap)


class STACValidationError(Exception):
    """Represents a validation error. Thrown by validation calls if the STAC JSON
    is invalid.

    Args:
        source (object): Source of the exception. Type will be determined by the
            validation implementation. For the default JsonSchemaValidator this will a
            the ``jsonschema.ValidationError``.
    """
    def __init__(self, message, source=None):
        super().__init__(message)
        self.source = source


# Import after above class definition
from pystac.validation.stac_validator import (STACValidator, JsonSchemaSTACValidator)


def validate(stac_object):
    """Validates a :class:`~pystac.STACObject`.

    Args:
        stac_object (STACObject): The stac object to validate.

    Returns:
        List[Object]: List of return values from the validation calls for the
           core object and any extensions. Element type is specific to the
           STACValidator implementation.

    Raises:
        STACValidationError
    """
    return validate_dict(stac_dict=stac_object.to_dict(),
                         stac_object_type=stac_object.STAC_OBJECT_TYPE,
                         stac_version=pystac.get_stac_version(),
                         extensions=stac_object.stac_extensions)


def validate_dict(stac_dict, stac_object_type=None, stac_version=None, extensions=None):
    """Validate a stac object serialized as JSON into a dict.

    This method delegates to the call to :meth:`pystac.validation.STACValidator.validate`
    for the STACValidator registered via :meth:`~pystac.validation.set_validator` or
    :class:`~pystac.validation.JsonSchemaSTACValidator` by default.

    Args:
        stac_dict (dict): Dictionary that is the STAC json of the object.
        stac_object_type (str): The stac object type of the object encoded in stac_dict.
            One of :class:`~pystac.STACObjectType`. If not supplied, this will use
            PySTAC's identification logic to identify the object type.
        stac_version (str): The version of STAC to validate the object against. If not supplied,
            this will use PySTAC's identification logic to identify the stac version
        extensions (List[str]): Extension IDs for this stac object. If not supplied,
            PySTAC's identification logic to identify the extensions.

    Returns:
        List[Object]: List of return values from the validation calls for the
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
        stac_version = info.version_range.latest_valid_version()
    if extensions is None:
        if info is None:
            info = identify_stac_object(stac_dict)
        extensions = info.common_extensions

    return RegisteredValidator.get_validator().validate(stac_dict, stac_object_type, stac_version,
                                                        extensions)


class RegisteredValidator:
    _validator = None

    @classmethod
    def get_validator(cls):
        if cls._validator is None:
            try:
                import jsonschema
            except ImportError:
                raise Exception(
                    'Cannot validate with default validator because package "jsonschema" '
                    'is not installed. Install pystac with the validation optional requirements '
                    '(e.g. pip install pystac[validation]) to install jsonschema')
            cls._validator = JsonSchemaSTACValidator()

        return cls._validator

    @classmethod
    def set_validator(cls, validator):
        if not issubclass(type(validator), STACValidator):
            raise Exception('Validator must be a subclass of {}'.format(STACValidator))
        cls._validator = validator


def set_validator(validator):
    """Sets the STACValidator to use in PySTAC.

    TKTK

    Args:
        validator (STACValidator): The STACVlidator implementation to use for
            validation.
    """
    RegisteredValidator.set_validator(validator)
