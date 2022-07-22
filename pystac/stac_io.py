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
)

from urllib.request import urlopen
from urllib.error import HTTPError

import pystac
from pystac.link import HREF
from pystac.utils import safe_urlparse
from pystac.serialization import (
    merge_common_properties,
    identify_stac_object_type,
    identify_stac_object,
    migrate_to_latest,
)

# Use orjson if available
try:
    import orjson
except ImportError:
    orjson = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from pystac.stac_object import STACObject as STACObject_Type
    from pystac.catalog import Catalog as Catalog_Type


class StacIO(ABC):
    _default_io: Optional[Callable[[], "StacIO"]] = None

    @abstractmethod
    def read_text(self, source: HREF, *args: Any, **kwargs: Any) -> str:
        """Read text from the given URI.

        The source to read from can be specified as a string or :class:`os.PathLike`
        object (:class:`~pystac.Link` is a path-like object). If it is a string, it
        must be a URI or local path from which to read. Using a :class:`~pystac.Link`
        enables implementations to use additional link information, such as paging
        information contained in the extended links described in the `STAC API spec
        <https://github.com/radiantearth/stac-api-spec/tree/master/item-search#paging>`__.

        Args:
            source : The source to read from.
            *args : Arbitrary positional arguments that may be utilized by the concrete
                implementation.
            **kwargs : Arbitrary keyword arguments that may be utilized by the concrete
                implementation.

        Returns:
            str: The text contained in the file at the location specified by the uri.
        """
        raise NotImplementedError

    @abstractmethod
    def write_text(
        self,
        dest: HREF,
        txt: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Write the given text to a file at the given URI.

        The destination to write to can be specified as a string or
        :class:`os.PathLike` object (:class:`~pystac.Link` is a path-like object). If
        it is a string, it must be a URI or local path from which to read. Using a
        :class:`~pystac.Link` enables implementations to use additional link
        information.

        Args:
            dest : The destination to write to.
            txt : The text to write.
        """
        raise NotImplementedError

    def json_loads(self, txt: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Method used internally by :class:`StacIO` instances to deserialize a
        dictionary from a JSON string.

        This method may be overwritten in :class:`StacIO` sub-classes to provide custom
        deserialization logic. The method accepts arbitrary keyword arguments. These are
        not used by the default implementation, but may be used by sub-class
        implementations.

        Args:

            txt : The JSON string to deserialize to a dictionary.
        """
        result: Dict[str, Any]
        if orjson is not None:
            result = orjson.loads(txt)
        else:
            result = json.loads(txt, *args, **kwargs)
        return result

    def json_dumps(self, json_dict: Dict[str, Any], *args: Any, **kwargs: Any) -> str:
        """Method used internally by :class:`StacIO` instances to serialize a dictionary
        to a JSON string.

        This method may be overwritten in :class:`StacIO` sub-classes to provide custom
        serialization logic. The method accepts arbitrary keyword arguments. These are
        not used by the default implementation, but may be used by sub-class
        implementations.

        Args:

            json_dict : The dictionary to serialize
        """
        if orjson is not None:
            return orjson.dumps(json_dict, option=orjson.OPT_INDENT_2, **kwargs).decode(
                "utf-8"
            )
        else:
            return json.dumps(json_dict, *args, indent=2, **kwargs)

    def stac_object_from_dict(
        self,
        d: Dict[str, Any],
        href: Optional[HREF] = None,
        root: Optional["Catalog_Type"] = None,
        preserve_dict: bool = True,
    ) -> "STACObject_Type":
        """Deserializes a :class:`~pystac.STACObject` sub-class instance from a
        dictionary.

        Args:

            d : The dictionary to deserialize
            href : Optional href to associate with the STAC object
            root : Optional root :class:`~pystac.Catalog` to associate with the
                STAC object.
            preserve_dict: If ``False``, the dict parameter ``d`` may be modified
                during this method call. Otherwise the dict is not mutated.
                Defaults to ``True``, which results results in a deepcopy of the
                parameter. Set to ``False`` when possible to avoid the performance
                hit of a deepcopy.
        """
        href_str = None if href is None else str(os.fspath(href))
        if identify_stac_object_type(d) == pystac.STACObjectType.ITEM:
            collection_cache = None
            if root is not None:
                collection_cache = root._resolved_objects.as_collection_cache()

            # Merge common properties in case this is an older STAC object.
            merge_common_properties(
                d, json_href=href_str, collection_cache=collection_cache
            )

        info = identify_stac_object(d)
        d = migrate_to_latest(d, info)

        if info.object_type == pystac.STACObjectType.CATALOG:
            result = pystac.Catalog.from_dict(
                d, href=href_str, root=root, migrate=False, preserve_dict=preserve_dict
            )
            result._stac_io = self
            return result

        if info.object_type == pystac.STACObjectType.COLLECTION:
            return pystac.Collection.from_dict(
                d, href=href_str, root=root, migrate=False, preserve_dict=preserve_dict
            )

        if info.object_type == pystac.STACObjectType.ITEM:
            return pystac.Item.from_dict(
                d, href=href_str, root=root, migrate=False, preserve_dict=preserve_dict
            )

        raise ValueError(f"Unknown STAC object type {info.object_type}")

    def read_json(self, source: HREF, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Read a dict from the given source.

        See :func:`StacIO.read_text <pystac.StacIO.read_text>` for usage of
        str vs Link as a parameter.

        Args:
            source : The source from which to read.
            *args : Additional positional arguments to be passed to
                :meth:`StacIO.read_text`.
            **kwargs : Additional keyword arguments to be passed to
                :meth:`StacIO.read_text`.

        Returns:
            dict: A dict representation of the JSON contained in the file at the
            given source.
        """
        txt = self.read_text(source, *args, **kwargs)
        return self.json_loads(txt)

    def read_stac_object(
        self,
        source: HREF,
        root: Optional["Catalog_Type"] = None,
        *args: Any,
        **kwargs: Any,
    ) -> "STACObject_Type":
        """Read a STACObject from a JSON file at the given source.

        See :func:`StacIO.read_text <pystac.StacIO.read_text>` for usage of
        str vs Link as a parameter.

        Args:
            source : The source from which to read.
            root : Optional root of the catalog for this object.
                If provided, the root's resolved object cache can be used to search for
                previously resolved instances of the STAC object.
            *args : Additional positional arguments to be passed to
                :meth:`StacIO.read_json`.
            **kwargs : Additional keyword arguments to be passed to
                :meth:`StacIO.read_json`.

        Returns:
            STACObject: The deserialized STACObject from the serialized JSON
            contained in the file at the given uri.
        """
        d = self.read_json(source, *args, **kwargs)
        return self.stac_object_from_dict(
            d, href=source, root=root, preserve_dict=False
        )

    def save_json(
        self,
        dest: HREF,
        json_dict: Dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Write a dict to the given URI as JSON.

        See :func:`StacIO.write_text <pystac.StacIO.write_text>` for usage of
        str vs Link as a parameter.

        Args:
            dest : The destination file to write the text to.
            json_dict : The JSON dict to write.
            *args : Additional positional arguments to be passed to
                :meth:`StacIO.json_dumps`.
            **kwargs : Additional keyword arguments to be passed to
                :meth:`StacIO.json_dumps`.
        """
        txt = self.json_dumps(json_dict, *args, **kwargs)
        self.write_text(dest, txt)

    @classmethod
    def set_default(cls, stac_io_class: Callable[[], "StacIO"]) -> None:
        """Set the default StacIO instance to use."""
        cls._default_io = stac_io_class

    @classmethod
    def default(cls) -> "StacIO":
        if cls._default_io is None:
            cls._default_io = DefaultStacIO

        return cls._default_io()


class DefaultStacIO(StacIO):
    def read_text(self, source: HREF, *_: Any, **__: Any) -> str:
        """A concrete implementation of :meth:`StacIO.read_text
        <pystac.StacIO.read_text>`. Converts the ``source`` argument to a string (if it
        is not already) and delegates to :meth:`DefaultStacIO.read_text_from_href` for
        opening and reading the file."""
        href = str(os.fspath(source))
        return self.read_text_from_href(href)

    def read_text_from_href(self, href: str) -> str:
        """Reads file as a UTF-8 string.

        If ``href`` has a "scheme" (e.g. if it starts with "https://") then this will
        use :func:`urllib.request.urlopen` to open the file and read the contents;
        otherwise, :func:`open` will be used to open a local file.

        Args:

            href : The URI of the file to open.
        """
        parsed = safe_urlparse(href)
        href_contents: str
        if parsed.scheme != "":
            try:
                with urlopen(href) as f:
                    href_contents = f.read().decode("utf-8")
            except HTTPError as e:
                raise Exception("Could not read uri {}".format(href)) from e
        else:
            with open(href, encoding="utf-8") as f:
                href_contents = f.read()
        return href_contents

    def write_text(self, dest: HREF, txt: str, *_: Any, **__: Any) -> None:
        """A concrete implementation of :meth:`StacIO.write_text
        <pystac.StacIO.write_text>`. Converts the ``dest`` argument to a string (if it
        is not already) and delegates to :meth:`DefaultStacIO.write_text_from_href` for
        opening and reading the file."""
        href = str(os.fspath(dest))
        return self.write_text_to_href(href, txt)

    def write_text_to_href(self, href: str, txt: str) -> None:
        """Writes text to file using UTF-8 encoding.

        This implementation uses :func:`open` and therefore can only write to the local
        file system.

        Args:

            href : The path to which the file will be written.
            txt : The string content to write to the file.
        """
        href = os.fspath(href)
        dirname = os.path.dirname(href)
        if dirname != "" and not os.path.isdir(dirname):
            os.makedirs(dirname)
        with open(href, "w", encoding="utf-8") as f:
            f.write(txt)


class DuplicateKeyReportingMixin(StacIO):
    """A mixin for :class:`pystac.StacIO` implementations that will report
    on duplicate keys in the JSON being read in.

    See https://github.com/stac-utils/pystac/issues/313
    """

    def json_loads(self, txt: str, *_: Any, **__: Any) -> Dict[str, Any]:
        """Overwrites :meth:`StacIO.json_loads <pystac.StacIO.json_loads>` as the
        internal method used by :class:`DuplicateKeyReportingMixin` for deserializing
        a JSON string to a dictionary while checking for duplicate object keys.

        Raises:

            pystac.DuplicateObjectKeyError : If a duplicate object key is found.
        """
        result: Dict[str, Any] = json.loads(
            txt, object_pairs_hook=self._report_duplicate_object_names
        )
        return result

    def read_json(self, source: HREF, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Overwrites :meth:`StacIO.read_json <pystac.StacIO.read_json>` for
        deserializing a JSON file to a dictionary while checking for duplicate object
        keys.

        Raises:

            pystac.DuplicateObjectKeyError : If a duplicate object key is found.
        """
        txt = self.read_text(source, *args, **kwargs)
        try:
            return self.json_loads(txt, source=source)
        except pystac.DuplicateObjectKeyError as e:
            url = str(os.fspath(source))
            msg = str(e) + f" in {url}"
            raise pystac.DuplicateObjectKeyError(msg)

    @staticmethod
    def _report_duplicate_object_names(
        object_pairs: List[Tuple[str, Any]]
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in object_pairs:
            if key in result:
                raise pystac.DuplicateObjectKeyError(
                    f'Found duplicate object name "{key}"'
                )
            else:
                result[key] = value
        return result
