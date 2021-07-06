from typing import Dict, List, Any, Optional, cast, TYPE_CHECKING

import pystac
from pystac.serialization.identify import STACVersionID, identify_stac_object
from pystac.validation.schema_uri_map import OldExtensionSchemaUriMap
from pystac.utils import make_absolute_href

if TYPE_CHECKING:
    from pystac.stac_object import STACObject as STACObject_Type
    from pystac.stac_object import STACObjectType as STACObjectType_Type


# Import after above class definition
from pystac.validation.stac_validator import STACValidator, JsonSchemaSTACValidator


def validate(stac_object: "STACObject_Type") -> List[Any]:
    """Validates a :class:`~pystac.STACObject`.

    Args:
        stac_object : The stac object to validate.

    Returns:
        List[Object]: List of return values from the validation calls for the
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
    )


def validate_dict(
    stac_dict: Dict[str, Any],
    stac_object_type: Optional["STACObjectType_Type"] = None,
    stac_version: Optional[str] = None,
    extensions: Optional[List[str]] = None,
    href: Optional[str] = None,
) -> List[Any]:
    """Validate a stac object serialized as JSON into a dict.

    This method delegates to the call to
    :meth:`pystac.validation.STACValidator.validate` for the STACValidator registered
    via :meth:`~pystac.validation.set_validator` or
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
        stac_version = str(info.version_range.latest_valid_version())
    if extensions is None:
        if info is None:
            info = identify_stac_object(stac_dict)
        extensions = list(info.extensions)

    stac_version_id = STACVersionID(stac_version)

    # If the version is before 1.0.0-rc.2, substitute extension short IDs for
    # their schemas.
    if stac_version_id < "1.0.0-rc.2":

        def _get_uri(ext: str) -> Optional[str]:
            return OldExtensionSchemaUriMap.get_extension_schema_uri(
                ext,
                stac_object_type,  # type:ignore
                stac_version_id,
            )

        extensions = [uri for uri in map(_get_uri, extensions) if uri is not None]

    return RegisteredValidator.get_validator().validate(
        stac_dict, stac_object_type, stac_version, extensions, href
    )


def validate_all(
    stac_dict: Dict[str, Any], href: str, stac_io: Optional[pystac.StacIO] = None
) -> None:
    """Validate STAC JSON and all contained catalogs, collections and items.

    If this stac_dict represents a catalog or collection, this method will
    recursively be called for each child link and all contained items.

    Args:

        stac_dict : Dictionary that is the STAC json of the object.
        href : HREF of the STAC object being validated. Used for error
            reporting and resolving relative links.
        stac_io: Optional StacIO instance to use for reading hrefs. If None,
            the StacIO.default() instance is used.

    Raises:
        STACValidationError: This will raise a STACValidationError if this or any
            contained catalog, collection or item has a validation error.
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

    if info.object_type != pystac.STACObjectType.ITEM:
        if "links" in stac_dict:
            # Account for 0.6 links
            if isinstance(stac_dict["links"], dict):
                links: List[Dict[str, Any]] = list(stac_dict["links"].values())
            else:
                links = cast(List[Dict[str, Any]], stac_dict.get("links"))
            for link in links:
                rel = link.get("rel")
                if rel in [pystac.RelType.ITEM, pystac.RelType.CHILD]:
                    link_href = make_absolute_href(
                        cast(str, link.get("href")), start_href=href
                    )
                    if link_href is not None:
                        d = stac_io.read_json(link_href)
                        validate_all(d, link_href)


class RegisteredValidator:
    _validator: Optional[STACValidator] = None

    @classmethod
    def get_validator(cls) -> STACValidator:
        if cls._validator is None:
            try:
                import jsonschema
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
            raise Exception("Validator must be a subclass of {}".format(STACValidator))
        cls._validator = validator


def set_validator(validator: STACValidator) -> None:
    """Sets the STACValidator to use in PySTAC.

    Args:
        validator : The STACValidator implementation to use for
            validation.
    """
    RegisteredValidator.set_validator(validator)
