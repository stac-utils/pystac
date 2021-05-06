from abc import ABC, abstractmethod
import os
import json
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
    Tuple,
    Type,
    Union,
)
import warnings

from urllib.parse import urlparse
from urllib.request import urlopen
from urllib.error import HTTPError

import pystac
import pystac.serialization

# Use orjson if available
try:
    import orjson
except ImportError:
    orjson = None

if TYPE_CHECKING:
    from pystac.stac_object import STACObject as STACObject_Type
    from pystac.catalog import Catalog as Catalog_Type
    from pystac.link import Link as Link_Type


class StacIO(ABC):
    _default_io: Optional[Type["StacIO"]] = None

    @abstractmethod
    def read_text(
        self, source: Union[str, "Link_Type"], *args: Any, **kwargs: Any
    ) -> str:
        """Read text from the given URI.

        The source to read from can be specified
        as a string or a Link. If it's a string, it's the URL of the HREF from which to
        read. When reading links, PySTAC will pass in the entire link body.
        This enables implementations to utilize additional link information,
        e.g. the "post" information in a pagination link from a STAC API search.

        Args:
            source (str or pystac.Link): The source to read from.

        Returns:
            str: The text contained in the file at the location specified by the uri.
        """
        raise NotImplementedError("read_text not implemented")

    @abstractmethod
    def write_text(
        self, dest: Union[str, "Link_Type"], txt: str, *args: Any, **kwargs: Any
    ) -> None:
        """Write the given text to a file at the given URI.

        The destination to write to from can be specified
        as a string or a Link. If it's a string, it's the URL of the HREF from which to
        read. When writing based on links links, PySTAC will pass in the entire
        link body.

        Args:
            dest (str or pystac.Link): The destination to write to.
            txt (str): The text to write.
        """
        raise NotImplementedError("write_text not implemented")

    def _json_loads(self, txt: str, source: Union[str, "Link_Type"]) -> Dict[str, Any]:
        if orjson is not None:
            return orjson.loads(txt)
        else:
            return json.loads(self.read_text(txt))

    def _json_dumps(
        self, json_dict: Dict[str, Any], source: Union[str, "Link_Type"]
    ) -> str:
        if orjson is not None:
            return orjson.dumps(json_dict, option=orjson.OPT_INDENT_2).decode("utf-8")
        else:
            return json.dumps(json_dict, indent=2)

    def stac_object_from_dict(
        self,
        d: Dict[str, Any],
        href: Optional[str] = None,
        root: Optional["Catalog_Type"] = None,
    ) -> "STACObject_Type":
        result = pystac.serialization.stac_object_from_dict(d, href, root)
        if isinstance(result, pystac.Catalog):
            # Set the stac_io instance for usage by io operations
            # where this catalog is the root.
            result._stac_io = self
        return result

    def read_json(self, source: Union[str, "Link_Type"]) -> Dict[str, Any]:
        """Read a dict from the given source.

        See :func:`StacIO.read_text <pystac.StacIO.read_text>` for usage of
        str vs Link as a parameter.

        Args:
            source (str or Link): The source from which to read.

        Returns:
            dict: A dict representation of the JSON contained in the file at the
            given source.
        """
        txt = self.read_text(source)
        return self._json_loads(txt, source)

    def read_stac_object(
        self, source: Union[str, "Link_Type"], root: Optional["Catalog_Type"] = None
    ) -> "STACObject_Type":
        """Read a STACObject from a JSON file at the given source.

        See :func:`StacIO.read_text <pystac.StacIO.read_text>` for usage of
        str vs Link as a parameter.

        Args:
            source (str or pystac.Link): The source from which to read.
            root (Catalog or Collection): Optional root of the catalog for this object.
                If provided, the root's resolved object cache can be used to search for
                previously resolved instances of the STAC object.

        Returns:
            STACObject: The deserialized STACObject from the serialized JSON
            contained in the file at the given uri.
        """
        d = self.read_json(source)
        href = source if isinstance(source, str) else source.get_absolute_href()
        return self.stac_object_from_dict(d, href=href, root=root)

    def save_json(
        self, dest: Union[str, "Link_Type"], json_dict: Dict[str, Any]
    ) -> None:
        """Write a dict to the given URI as JSON.

        See :func:`StacIO.write_text <pystac.StacIO.write_text>` for usage of
        str vs Link as a parameter.

        Args:
            dest (str or pystac.Link): The destination file to write the text to.
            json_dict (dict): The JSON dict to write.
        """
        txt = self._json_dumps(json_dict, dest)
        self.write_text(dest, txt)

    @classmethod
    def set_default(cls, stac_io_class: Type["StacIO"]) -> None:
        """Set the default StacIO instance to use."""
        cls._default_io = stac_io_class

    @classmethod
    def default(cls) -> "StacIO":
        if cls._default_io is None:
            cls._default_io = DefaultStacIO

        return cls._default_io()


class DefaultStacIO(StacIO):
    def read_text(
        self, source: Union[str, "Link_Type"], *args: Any, **kwargs: Any
    ) -> str:
        if isinstance(source, str):
            href = source
        else:
            href = source.get_absolute_href()
            if href is None:
                raise IOError(f"Could not get an absolute HREF from link {source}")

        parsed = urlparse(href)
        if parsed.scheme != "":
            try:
                with urlopen(href) as f:
                    return f.read().decode("utf-8")
            except HTTPError as e:
                raise Exception("Could not read uri {}".format(href)) from e
        else:
            with open(href) as f:
                return f.read()

    def write_text(
        self, dest: Union[str, "Link_Type"], txt: str, *args: Any, **kwargs: Any
    ) -> None:
        if isinstance(dest, str):
            href = dest
        else:
            href = dest.get_absolute_href()
            if href is None:
                raise IOError(f"Could not get an absolute HREF from link {dest}")

        dirname = os.path.dirname(href)
        if dirname != "" and not os.path.isdir(dirname):
            os.makedirs(dirname)
        with open(href, "w") as f:
            f.write(txt)


class DuplicateObjectKeyError(Exception):
    pass


class DuplicateKeyReportingMixin(StacIO):
    """A mixin for StacIO implementations that will report
    on duplicate keys in the JSON being read in.

    See https://github.com/stac-utils/pystac/issues/313
    """

    def _json_loads(self, txt: str, source: Union[str, "Link_Type"]) -> Dict[str, Any]:
        return json.loads(
            txt, object_pairs_hook=self.duplicate_object_names_report_builder(source)
        )

    @staticmethod
    def duplicate_object_names_report_builder(
        source: Union[str, "Link_Type"]
    ) -> Callable[[List[Tuple[str, Any]]], Dict[str, Any]]:
        def report_duplicate_object_names(
            object_pairs: List[Tuple[str, Any]]
        ) -> Dict[str, Any]:
            result: Dict[str, Any] = {}
            for key, value in object_pairs:
                if key in result:
                    url = (
                        source
                        if isinstance(source, str)
                        else source.get_absolute_href()
                    )
                    raise DuplicateObjectKeyError(
                        f"Found duplicate object name “{key}” in “{url}”"
                    )
                else:
                    result[key] = value
            return result

        return report_duplicate_object_names


class STAC_IO:
    """DEPRECATED: Methods used to read and save STAC json.
    Allows users of the library to set their own methods
    (e.g. for reading and writing from cloud storage)

    Note: The static methods of this class are deprecated. Move to using
    instance methods of a specific instance of StacIO.
    """

    @staticmethod
    def read_text_method(uri: str) -> str:
        warnings.warn(
            "STAC_IO is deprecated. "
            "Please use instances of StacIO (e.g. StacIO.default()).",
            DeprecationWarning,
        )
        return StacIO.default().read_text(uri)

    @staticmethod
    def write_text_method(uri: str, txt: str) -> None:
        """Default method for writing text."""
        warnings.warn(
            "STAC_IO is deprecated. "
            "Please use instances of StacIO (e.g. StacIO.default()).",
            DeprecationWarning,
        )
        return StacIO.default().write_text(uri, txt)

    @staticmethod
    def stac_object_from_dict(
        d: Dict[str, Any],
        href: Optional[str] = None,
        root: Optional["Catalog_Type"] = None,
    ) -> "STACObject_Type":
        warnings.warn(
            "STAC_IO is deprecated. "
            "Please use instances of StacIO (e.g. StacIO.default()).",
            DeprecationWarning,
        )
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
            <STAC_IO.read_text_method>`. If you want to modify the behavior of
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
            <STAC_IO.write_text_method>`. If you want to modify the behavior of
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
            <STAC_IO.read_text_method>`. If you want to modify the behavior of
            STAC_IO in order to enable additional URI types, replace that member
            with your own implementation.
        """
        return json.loads(STAC_IO.read_text(uri))

    @classmethod
    def read_stac_object(
        cls, uri: str, root: Optional["Catalog_Type"] = None
    ) -> "STACObject_Type":
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
            <STAC_IO.read_text_method>`. If you want to modify the behavior of
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
            <STAC_IO.write_text_method>`. If you want to modify the behavior of
            STAC_IO in order to enable additional URI types, replace that member
            with your own implementation.
        """
        STAC_IO.write_text(uri, json.dumps(json_dict, indent=4))
