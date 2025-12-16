import json
import logging
import warnings
from abc import ABC, abstractmethod
from typing import Any

import pystac
import pystac.utils
from pystac.errors import STACValidationError
from pystac.stac_object import STACObjectType
from pystac.validation.schema_uri_map import DefaultSchemaUriMap, SchemaUriMap

try:
    import jsonschema
    import jsonschema.exceptions
    import jsonschema.validators
    from referencing import Registry, Resource

    from pystac.validation.local_validator import get_local_schema_cache

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

logger = logging.getLogger(__name__)


class GetSchemaError(Exception):
    """Raised when unable to fetch a schema."""

    def __init__(self, href: str, error: Exception) -> None:
        super().__init__(f"Error when fetching schema {href}: {error}")


class STACValidator(ABC):
    """STACValidator defines methods for validating STAC
    JSON. Implementations define methods for validating core objects and extension.
    By default the JsonSchemaSTACValidator is used by PySTAC; users can define their own
    STACValidator implementation and set that validator to be used by
    pystac by using the :func:`~pystac.validation.set_validator` method.
    """

    @abstractmethod
    def validate_core(
        self,
        stac_dict: dict[str, Any],
        stac_object_type: STACObjectType,
        stac_version: str,
        href: str | None = None,
    ) -> Any:
        """Validate a core stac object.

        Return value can be None or specific to the implementation.

        Args:
            stac_dict : Dictionary that is the STAC json of the object.
            stac_object_type : The stac object type of the object encoded
                in stac_dict. One of :class:`~pystac.STACObjectType`.
            stac_version : The version of STAC to validate the object against.
            href : Optional HREF of the STAC object being validated.
        """
        raise NotImplementedError

    @abstractmethod
    def validate_extension(
        self,
        stac_dict: dict[str, Any],
        stac_object_type: STACObjectType,
        stac_version: str,
        extension_id: str,
        href: str | None = None,
    ) -> Any:
        """Validate an extension stac object.

        Return value can be None or specific to the implementation.

        Args:
            stac_dict : Dictionary that is the STAC json of the object.
            stac_object_type : The stac object type of the object encoded in
                stac_dict. One of :class:`~pystac.STACObjectType`.
            stac_version : The version of STAC to validate the object against.
            extension_id : The extension ID of the extension to validate against.
            href : Optional HREF of the STAC object being validated.
        """
        raise NotImplementedError

    def validate(
        self,
        stac_dict: dict[str, Any],
        stac_object_type: STACObjectType,
        stac_version: str,
        extensions: list[str],
        href: str | None = None,
    ) -> list[Any]:
        """Validate a STAC object JSON.

        Args:
            stac_dict : Dictionary that is the STAC json of the object.
            stac_object_type : The stac object type of the object encoded in
                stac_dict. One of :class:`~pystac.STACObjectType`.
            stac_version : The version of STAC to validate the object against.
            extensions : Extension IDs for this stac object.
            href : Optional href of the STAC object being validated.

        Returns:
            List[Any]: List of return values from the validation calls for the
               core object and any extensions. Element type is specific to the
               STACValidator implementation.
        """
        results: list[Any] = []

        # Pass the dict through JSON serialization and parsing, otherwise
        # some valid properties can be marked as invalid (e.g. tuples in
        # coordinate sequences for geometries).
        json_dict = json.loads(json.dumps(stac_dict))
        core_result = self.validate_core(
            json_dict, stac_object_type, stac_version, href
        )
        if core_result is not None:
            results.append(core_result)

        for extension_id in extensions:
            ext_result = self.validate_extension(
                json_dict, stac_object_type, stac_version, extension_id, href
            )
            if ext_result is not None:
                results.append(ext_result)

        return results


class JsonSchemaSTACValidator(STACValidator):
    """Validate STAC based on JSON Schemas.

    This validator uses JSON schemas, read from URIs provided by a
    :class:`~pystac.validation.schema_uri_map.SchemaUriMap`, to validate STAC core
    objects and extensions.

    Args:
        schema_uri_map : The :class:`~pystac.validation.schema_uri_map.SchemaUriMap`
            that defines where
            the validator will retrieve the JSON schemas for validation.
            Defaults to an instance of
            :class:`~pystac.validation.schema_uri_map.DefaultSchemaUriMap`

    Note:
    This class requires the ``jsonschema`` library to be installed.
    """

    schema_uri_map: SchemaUriMap
    schema_cache: dict[str, dict[str, Any]]

    def __init__(self, schema_uri_map: SchemaUriMap | None = None) -> None:
        if not HAS_JSONSCHEMA:
            raise ImportError("Cannot instantiate, requires jsonschema package")

        if schema_uri_map is not None:
            self.schema_uri_map = schema_uri_map
        else:
            self.schema_uri_map = DefaultSchemaUriMap()

        self.schema_cache = get_local_schema_cache()

    def _get_schema(self, schema_uri: str) -> dict[str, Any]:
        if schema_uri not in self.schema_cache:
            try:
                s = json.loads(pystac.StacIO.default().read_text(schema_uri))
            except Exception as error:
                raise GetSchemaError(schema_uri, error) from error
            self.schema_cache[schema_uri] = s
            id_field = "$id" if "$id" in s else "id"
            if not s[id_field].startswith("http"):
                s[id_field] = schema_uri
        return self.schema_cache[schema_uri]

    @property
    def registry(self) -> Any:
        def retrieve(schema_uri: str) -> Resource[dict[str, Any]]:
            return Resource.from_contents(self._get_schema(schema_uri))

        return Registry(retrieve=retrieve).with_resources(  # type: ignore
            [(k, Resource.from_contents(v)) for k, v in self.schema_cache.items()]
        )

    def get_schema_from_uri(self, schema_uri: str) -> tuple[dict[str, Any], Any]:
        """DEPRECATED"""
        warnings.warn(
            "get_schema_from_uri is deprecated and will be removed in v2.",
            DeprecationWarning,
        )
        return self._get_schema(schema_uri), self.registry

    def _validate_from_uri(
        self,
        stac_dict: dict[str, Any],
        stac_object_type: STACObjectType,
        schema_uri: str,
        href: str | None = None,
    ) -> None:
        try:
            schema = self._get_schema(schema_uri)
            # This block is cribbed (w/ change in error handling) from
            # jsonschema.validate
            cls = jsonschema.validators.validator_for(schema)
            cls.check_schema(schema)
            validator = cls(schema, registry=self.registry)
            errors = list(validator.iter_errors(stac_dict))
        except Exception as e:
            logger.error(f"Exception while validating {stac_object_type} href: {href}")
            logger.exception(e)
            raise
        if errors:
            stac_id = stac_dict.get("id", None)
            msg = f"Validation failed for {stac_object_type} "
            if href is not None:
                msg += f"at {href} "
            if stac_id is not None:
                msg += f"with ID {stac_id} "
            msg += f"against schema at {schema_uri}"

            best = jsonschema.exceptions.best_match(errors)
            if best:
                msg += "\n" + str(best)
            raise STACValidationError(msg, source=errors) from best

    def validate_core(
        self,
        stac_dict: dict[str, Any],
        stac_object_type: STACObjectType,
        stac_version: str,
        href: str | None = None,
    ) -> str | None:
        """Validate a core stac object.

        Return value can be None or specific to the implementation.

        Args:
            stac_dict : Dictionary that is the STAC json of the object.
            stac_object_type : The stac object type of the object encoded in
                stac_dict. One of :class:`~pystac.STACObjectType`.
            stac_version : The version of STAC to validate the object against.
            href : Optional HREF of the STAC object being validated.

        Returns:
           str: URI for the JSON schema that was validated against, or None if
               no validation occurred.

        Raises:
           STACValidationError:  if stac_dict is not valid. The exception is raised from
               the "best" error, as determined by the jsonschema library. To access all
               jsonschema validation errors, use ``STACValidationError.source``.

        """
        schema_uri = self.schema_uri_map.get_object_schema_uri(
            stac_object_type, stac_version
        )

        if schema_uri is None:
            return None

        self._validate_from_uri(stac_dict, stac_object_type, schema_uri, href=href)

        return schema_uri

    def validate_extension(
        self,
        stac_dict: dict[str, Any],
        stac_object_type: STACObjectType,
        stac_version: str,
        extension_id: str,
        href: str | None = None,
    ) -> str | None:
        """Validate an extension stac object.

        Return value can be None or specific to the implementation.

        Args:
            stac_dict : Dictionary that is the STAC json of the object.
            stac_object_type : The stac object type of the object encoded in
                stac_dict. One of :class:`~pystac.STACObjectType`.
            stac_version : The version of STAC to validate the object against.
            extension_id : The extension ID to validate against.
            href : Optional HREF of the STAC object being validated.

        Returns:
           str: URI for the JSON schema that was validated against, or None if
               no validation occurred.

        Raises:
           STACValidationError: if stac_dict is not valid. The exception is raised from
               the "best" error, as determined by the jsonschema library. To access all
               jsonschema validation errors, use ``STACValidationError.source``.

        """
        schema_uri = extension_id

        if schema_uri is None:
            return None

        schema_uri = pystac.utils.make_absolute_href(schema_uri, href)

        self._validate_from_uri(stac_dict, stac_object_type, schema_uri, href)

        return schema_uri
