import json
from abc import (ABC, abstractmethod)

from pystac import STAC_IO
from pystac.validation import STACValidationError
from pystac.validation.schema_uri_map import DefaultSchemaUriMap

try:
    import jsonschema
except ImportError:
    jsonschema = None


class STACValidator(ABC):
    """STACValidator defines methods for validating STAC
    JSON. Implementations define methods for validating core objects and extension.
    By default the JsonSchemaSTACValidator is used by PySTAC; users can define their own
    STACValidator implementation and set that validator to be used by
    pystac by using the :func:`~pystac.validation.set_validator` method.
    """
    @abstractmethod
    def validate_core(self, stac_dict, stac_object_type, stac_version, href=None):
        """Validate a core stac object.

        Return value can be None or specific to the implementation.

        Args:
            stac_dict (dict): Dictionary that is the STAC json of the object.
            stac_object_type (str): The stac object type of the object encoded in stac_dict.
                One of :class:`~pystac.STACObjectType`.
            stac_version (str): The version of STAC to validate the object against.
            href (str): Optional HREF of the STAC object being validated.
        """
        pass

    @abstractmethod
    def validate_extension(self,
                           stac_dict,
                           stac_object_type,
                           stac_version,
                           extension_id,
                           href=None):
        """Validate an extension stac object.

        Return value can be None or specific to the implementation.

        Args:
            stac_dict (dict): Dictionary that is the STAC json of the object.
            stac_object_type (str): The stac object type of the object encoded in stac_dict.
                One of :class:`~pystac.STACObjectType`.
            stac_version (str): The version of STAC to validate the object against.
            extension_id (str): The extension ID of the extension to validate against.
            href (str): Optional HREF of the STAC object being validated.
        """
        pass

    def validate(self, stac_dict, stac_object_type, stac_version, extensions, href=None):
        """Validate a STAC object JSON.

        Args:
            stac_dict (dict): Dictionary that is the STAC json of the object.
            stac_object_type (str): The stac object type of the object encoded in stac_dict.
                One of :class:`~pystac.STACObjectType`.
            stac_version (str): The version of STAC to validate the object against.
            extensions (List[str]): Extension IDs for this stac object.
            href (str): Optional href of the STAC object being validated.

        Returns:
            List[Object]: List of return values from the validation calls for the
               core object and any extensions. Element type is specific to the
               STACValidator implementation.
        """
        results = []

        # Pass the dict through JSON serialization and parsing, otherwise
        # some valid properties can be marked as invalid (e.g. tuples in
        # coordinate sequences for geometries).
        json_dict = json.loads(json.dumps(stac_dict))
        core_result = self.validate_core(json_dict, stac_object_type, stac_version, href)
        if core_result is not None:
            results.append(core_result)

        for extension_id in extensions:
            ext_result = self.validate_extension(json_dict, stac_object_type, stac_version,
                                                 extension_id, href)
            if ext_result is not None:
                results.append(ext_result)

        return results


class JsonSchemaSTACValidator(STACValidator):
    """Validate STAC based on JSON Schemas.

    This validator uses JSON schemas, read from URIs provided by a
    :class:`~pystac.validation.SchemaUriMap`, to validate STAC core
    objects and extensions.

    Args:
        schema_uri_map (SchemaUriMap): The SchemaUriMap that defines where
            the validator will retrieve the JSON schemas for validation.
            Defaults to an instance of
            :class:`~pystac.validation.schema_uri_map.DefaultSchemaUriMap`

    Note:
    This class requires the ``jsonschema`` library to be installed.
    """
    def __init__(self, schema_uri_map=None):
        if jsonschema is None:
            raise Exception('Cannot instantiate, requires jsonschema package')

        if schema_uri_map is not None:
            self.schema_uri_map = schema_uri_map
        else:
            self.schema_uri_map = DefaultSchemaUriMap()

        self.schema_cache = {}

    def get_schema_from_uri(self, schema_uri):
        if schema_uri not in self.schema_cache:
            s = json.loads(STAC_IO.read_text(schema_uri))
            self.schema_cache[schema_uri] = s

        schema = self.schema_cache[schema_uri]

        resolver = jsonschema.validators.RefResolver(base_uri=schema_uri,
                                                     referrer=schema,
                                                     store=self.schema_cache)

        return (schema, resolver)

    def _validate_from_uri(self, stac_dict, schema_uri):
        schema, resolver = self.get_schema_from_uri(schema_uri)
        jsonschema.validate(instance=stac_dict, schema=schema, resolver=resolver)
        for uri in resolver.store:
            if uri not in self.schema_cache:
                self.schema_cache[uri] = resolver.store[uri]

    def _get_error_message(self, schema_uri, stac_object_type, extension_id, href, stac_id):
        s = 'Validation failed for {} '.format(stac_object_type)
        if href is not None:
            s += 'at {} '.format(href)
        if stac_id is not None:
            s += 'with ID {} '.format(stac_id)
        s += 'against schema at {}'.format(schema_uri)
        if extension_id is not None:
            s += " for STAC extension '{}'".format(extension_id)

        return s

    def validate_core(self, stac_dict, stac_object_type, stac_version, href=None):
        """Validate a core stac object.

        Return value can be None or specific to the implementation.

        Args:
            stac_dict (dict): Dictionary that is the STAC json of the object.
            stac_object_type (str): The stac object type of the object encoded in stac_dict.
                One of :class:`~pystac.STACObjectType`.
            stac_version (str): The version of STAC to validate the object against.
            href (str): Optional HREF of the STAC object being validated.

        Returns:
           str: URI for the JSON schema that was validated against, or None if
               no validation occurred.
        """
        schema_uri = self.schema_uri_map.get_core_schema_uri(stac_object_type, stac_version)

        if schema_uri is None:
            return None

        try:
            self._validate_from_uri(stac_dict, schema_uri)
            return schema_uri
        except jsonschema.exceptions.ValidationError as e:
            msg = self._get_error_message(schema_uri, stac_object_type, None, href,
                                          stac_dict.get('id'))
            raise STACValidationError(msg, source=e) from e

    def validate_extension(self,
                           stac_dict,
                           stac_object_type,
                           stac_version,
                           extension_id,
                           href=None):
        """Validate an extension stac object.

        Return value can be None or specific to the implementation.

        Args:
            stac_dict (dict): Dictionary that is the STAC json of the object.
            stac_object_type (str): The stac object type of the object encoded in stac_dict.
                One of :class:`~pystac.STACObjectType`.
            stac_version (str): The version of STAC to validate the object against.
            extension_id (str): The extension ID to validate against.
            href (str): Optional HREF of the STAC object being validated.

        Returns:
           str: URI for the JSON schema that was validated against, or None if
               no validation occurred.
        """
        schema_uri = self.schema_uri_map.get_extension_schema_uri(extension_id, stac_object_type,
                                                                  stac_version)

        if schema_uri is None:
            return None

        try:
            self._validate_from_uri(stac_dict, schema_uri)
            return schema_uri
        except jsonschema.exceptions.ValidationError as e:
            msg = self._get_error_message(schema_uri, stac_object_type, extension_id, href,
                                          stac_dict.get('id'))
            raise STACValidationError(msg, source=e) from e
