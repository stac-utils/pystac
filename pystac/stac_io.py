import os
import json
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

from urllib.parse import urlparse
from urllib.request import urlopen
from urllib.error import HTTPError

import pystac.serialization

if TYPE_CHECKING:
    from pystac.stac_object import STACObject as STACObjectType
    from pystac.catalog import Catalog as CatalogType


class STAC_IO:
    """Methods used to read and save STAC json.
    Allows users of the library to set their own methods
    (e.g. for reading and writing from cloud storage)
    """
    @staticmethod
    def default_read_text_method(uri: str) -> str:
        """Default method for reading text. Only handles local file paths."""
        parsed = urlparse(uri)
        if parsed.scheme != '':
            try:
                with urlopen(uri) as f:
                    return f.read().decode('utf-8')
            except HTTPError as e:
                raise Exception("Could not read uri {}".format(uri)) from e
        else:
            with open(uri) as f:
                return f.read()

    @staticmethod
    def default_write_text_method(uri: str, txt: str) -> None:
        """Default method for writing text. Only handles local file paths."""
        dirname = os.path.dirname(uri)
        if dirname != '' and not os.path.isdir(dirname):
            os.makedirs(dirname)
        with open(uri, 'w') as f:
            f.write(txt)

    read_text_method: Callable[[str], str] = default_read_text_method
    """Users of PySTAC can replace the read_text_method in order
    to expand the ability of PySTAC to read different file systems.
    For example, a client of the library might replace this class
    member in it's own __init__.py with a method that can read from
    cloud storage.
    """

    write_text_method: Callable[[str, str], None] = default_write_text_method
    """Users of PySTAC can replace the write_text_method in order
    to expand the ability of PySTAC to write to different file systems.
    For example, a client of the library might replace this class
    member in it's own __init__.py with a method that can read from
    cloud storage.
    """

    @staticmethod
    def stac_object_from_dict(d: Dict[str, Any],
                              href: Optional[str] = None,
                              root: Optional["CatalogType"] = None) -> "STACObjectType":
        return pystac.serialization.stac_object_from_dict(d, href, root)

    # This is set in __init__.py
    _STAC_OBJECT_CLASSES = None

    @classmethod
    def read_text(cls, uri: str) -> str:
        """Read text from the given URI.

        Args:
            uri (str): The URI from which to read text.

        Returns:
            str: The text contained in the file at the location specified by the uri.

        Note:
            This method uses the :func:`STAC_IO.read_text_method
            <pystac.STAC_IO.read_text_method>`. If you want to modify the behavior of
            STAC_IO in order to enable additional URI types, replace that member
            with your own implementation.
        """
        return cls.read_text_method(uri)

    @classmethod
    def write_text(cls, uri: str, txt: str) -> None:
        """Write the given text to a file at the given URI.

        Args:
            uri (str): The URI of the file to write the text to.
            txt (str): The text to write.

        Note:
            This method uses the :func:`STAC_IO.write_text_method
            <pystac.STAC_IO.write_text_method>`. If you want to modify the behavior of
            STAC_IO in order to enable additional URI types, replace that member
            with your own implementation.
        """
        cls.write_text_method(uri, txt)

    @classmethod
    def read_json(cls, uri: str) -> Dict[str, Any]:
        """Read a dict from the given URI.

        Args:
            uri (str): The URI from which to read.

        Returns:
            dict: A dict representation of the JSON contained in the file at the
            given uri.

        Note:
            This method uses the :func:`STAC_IO.read_text_method
            <pystac.STAC_IO.read_text_method>`. If you want to modify the behavior of
            STAC_IO in order to enable additional URI types, replace that member
            with your own implementation.
        """
        return json.loads(STAC_IO.read_text(uri))

    @classmethod
    def read_stac_object(cls, uri: str, root: Optional["CatalogType"] = None) -> "STACObjectType":
        """Read a STACObject from a JSON file at the given URI.

        Args:
            uri (str): The URI from which to read.
            root (Catalog or Collection): Optional root of the catalog for this object.
                If provided, the root's resolved object cache can be used to search for
                previously resolved instances of the STAC object.

        Returns:
            STACObject: The deserialized STACObject from the serialized JSON
            contained in the file at the given uri.

        Note:
            This method uses the :func:`STAC_IO.read_text_method
            <pystac.STAC_IO.read_text_method>`. If you want to modify the behavior of
            STAC_IO in order to enable additional URI types, replace that member
            with your own implementation.
        """
        d = cls.read_json(uri)
        return cls.stac_object_from_dict(d, uri, root)

    @classmethod
    def save_json(cls, uri: str, json_dict: Dict[str, Any]) -> None:
        """Write a dict to the given URI as JSON.

        Args:
            uri (str): The URI of the file to write the text to.
            json_dict (dict): The JSON dict to write.

        Note:
            This method uses the :func:`STAC_IO.write_text_method
            <pystac.STAC_IO.write_text_method>`. If you want to modify the behavior of
            STAC_IO in order to enable additional URI types, replace that member
            with your own implementation.
        """
        STAC_IO.write_text(uri, json.dumps(json_dict, indent=4))
