import os
import posixpath
from enum import Enum
from pystac.errors import RequiredPropertyMissing
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast
from urllib.parse import urljoin, urlparse, urlunparse, ParseResult as URLParseResult
from datetime import datetime, timezone
import dateutil.parser

# Allow for modifying the path library for testability
# (i.e. testing Windows path manipulation on non-Windows systems)
_pathlib = os.path


def safe_urlparse(href: str) -> URLParseResult:
    """Wrapper around :func:`urllib.parse.urlparse` that returns consistent results for
    both Windows and UNIX file paths.

    For Windows paths, this function will include the drive prefix (e.g. ``"D:\\"``) as
    part of the ``path`` of the :class:`urllib.parse.ParseResult` rather than as the
    ``scheme`` for consistency with handling of UNIX/LINUX file paths.

    Args:
        href (str) : The HREF to parse. May be a local file path or URL.

    Returns:
        urllib.parse.ParseResult : The named tuple representing the parsed HREF.
    """
    parsed = urlparse(href)
    if parsed.scheme != "" and href.lower().startswith("{}:\\".format(parsed.scheme)):
        return URLParseResult(
            scheme="",
            netloc="",
            path="{}:{}".format(
                # We use this more complicated formulation because parsed.scheme
                # converts to lower-case
                href[: len(parsed.scheme)],
                parsed.path,
            ),
            params=parsed.params,
            query=parsed.query,
            fragment=parsed.fragment,
        )
    else:
        return parsed


class StringEnum(str, Enum):
    """Base :class:`enum.Enum` class for string enums that will serialize as the string
    value."""

    def __str__(self) -> str:
        return cast(str, self.value)


class JoinType(StringEnum):
    """Allowed join types for :func:`~pystac.utils.join_path_or_url`."""

    @staticmethod
    def from_parsed_uri(parsed_uri: URLParseResult) -> "JoinType":
        """Determines the appropriate join type based on the scheme of the parsed
        result.

        Args:
            parsed_uri (urllib.parse.ParseResult) : A named tuple representing the
                parsed URI.

        Returns:
            JoinType : The join type for the URI.
        """
        if parsed_uri.scheme == "":
            return JoinType.PATH
        else:
            return JoinType.URL

    PATH = "path"
    URL = "url"


def join_path_or_url(join_type: JoinType, *args: str) -> str:
    """Functions similarly to :func:`os.path.join`, but can be used to join either a
    local file path or a URL.

    Args:
        join_type (JoinType) : One of ``JoinType.PATH`` or ``JoinType.URL``. If
            ``JoinType.PATH``, then :func:`os.path.join` is used for the join.
            If ``JoinType.URL``, then :func:`posixpath.join` is used.
        *args (str): Additional positional string arguments to be joined.

    Returns:
        str : The joined path

    """

    if join_type == JoinType.PATH:
        return _pathlib.join(*args)
    else:
        return posixpath.join(*args)


def _make_relative_href_url(
    parsed_source: URLParseResult,
    parsed_start: URLParseResult,
    start_is_dir: bool = False,
) -> str:

    # If the start path is not a directory, get the parent directory
    start_dir = (
        parsed_start.path if start_is_dir else _pathlib.dirname(parsed_start.path)
    )

    # Strip the leading slashes from both paths
    start_dir = start_dir.lstrip("/")
    source_path = parsed_source.path.lstrip("/")

    # Get the relative path
    rel_url = posixpath.relpath(source_path, start_dir)

    # Ensure we retain a trailing slash from the original source path
    if parsed_source.path.endswith("/"):
        rel_url += "/"

    # Prepend the "./", if necessary
    if rel_url != "./" and not rel_url.startswith("../"):
        rel_url = "./" + rel_url
    return rel_url


def _make_relative_href_path(
    parsed_source: URLParseResult,
    parsed_start: URLParseResult,
    start_is_dir: bool = False,
) -> str:
    # If the start path is not a directory, get the parent directory
    start_dir = (
        parsed_start.path if start_is_dir else _pathlib.dirname(parsed_start.path)
    )

    # Strip the leading slashes from both paths
    start_dir = start_dir.lstrip("/")
    source_path = parsed_source.path.lstrip("/")

    relpath = _pathlib.relpath(source_path, start_dir)

    # Ensure we retain a trailing slash from the original source path
    if parsed_source.path.endswith("/"):
        relpath += "/"

    if relpath != "./" and not relpath.startswith(".." + _pathlib.sep):
        relpath = _pathlib.join(".", relpath)

    return relpath


def make_relative_href(
    source_href: str, start_href: str, start_is_dir: bool = False
) -> str:
    """Returns a new string that represents the ``source_href`` as a path relative to
    ``start_href``. If ``source_href`` and ``start_href`` do not share a common parent,
    then ``source_href`` is returned unchanged.

    May be used on either local file paths or URLs.

    Args:
        source_href : The HREF to make relative.
        start_href : The HREF that the resulting HREF will be relative to.
        start_is_dir : If ``True``, ``start_href`` is treated as a directory.
            Otherwise, ``start_href`` is considered to be a path to a file. Defaults to
            ``False``.

    Returns:
        str: The relative HREF.
    """

    parsed_source = safe_urlparse(source_href)
    parsed_start = safe_urlparse(start_href)
    if not (
        parsed_source.scheme == parsed_start.scheme
        and parsed_source.netloc == parsed_start.netloc
    ):
        return source_href

    if JoinType.from_parsed_uri(parsed_start) == JoinType.PATH:
        return _make_relative_href_path(parsed_source, parsed_start, start_is_dir)
    else:
        return _make_relative_href_url(parsed_source, parsed_start, start_is_dir)


def _make_absolute_href_url(
    parsed_source: URLParseResult,
    parsed_start: URLParseResult,
    start_is_dir: bool = False,
) -> str:

    # If the source is already absolute, just return it
    if parsed_source.scheme != "":
        return urlunparse(parsed_source)

    # If the start path is not a directory, get the parent directory
    if start_is_dir:
        start_dir = parsed_start.path
    else:
        # Ensure the directory has a trailing slash so urljoin works properly
        start_dir = parsed_start.path.rsplit("/", 1)[0] + "/"

    # Join the start directory to the relative path and find the absolute path
    abs_path = urljoin(start_dir, parsed_source.path)
    abs_path = abs_path.replace("\\", "/")

    return urlunparse(
        (
            parsed_start.scheme,
            parsed_start.netloc,
            abs_path,
            parsed_source.params,
            parsed_source.query,
            parsed_source.fragment,
        )
    )


def _make_absolute_href_path(
    parsed_source: URLParseResult,
    parsed_start: URLParseResult,
    start_is_dir: bool = False,
) -> str:

    # If the source is already absolute, just return it
    if _pathlib.isabs(parsed_source.path):
        return urlunparse(parsed_source)

    # If the start path is not a directory, get the parent directory
    start_dir = (
        parsed_start.path if start_is_dir else _pathlib.dirname(parsed_start.path)
    )

    # Join the start directory to the relative path and find the absolute path
    abs_path = _pathlib.abspath(_pathlib.join(start_dir, parsed_source.path))

    # Account for the normalization of abspath for
    # things like /vsitar// prefixes by replacing the
    # original start_dir text when abspath modifies the start_dir.
    if not start_dir == _pathlib.abspath(start_dir):
        abs_path = abs_path.replace(_pathlib.abspath(start_dir), start_dir)

    return abs_path


def make_absolute_href(
    source_href: str, start_href: Optional[str] = None, start_is_dir: bool = False
) -> str:
    """Returns a new string that represents ``source_href`` as an absolute path. If
    ``source_href`` is already absolute it is returned unchanged. If ``source_href``
    is relative, the absolute HREF is constructed by joining ``source_href`` to
    ``start_href``.

    May be used on either local file paths or URLs.

    Args:
        source_href : The HREF to make absolute.
        start_href : The HREF that will be used as the basis for resolving relative
            paths, if ``source_href`` is a relative path. Defaults to the current
            working directory.
        start_is_dir : If ``True``, ``start_href`` is treated as a directory.
            Otherwise, ``start_href`` is considered to be a path to a file. Defaults to
            ``False``.

    Returns:
        str: The absolute HREF.
    """
    if start_href is None:
        start_href = os.getcwd()
        start_is_dir = True

    parsed_start = safe_urlparse(start_href)
    parsed_source = safe_urlparse(source_href)

    if (
        JoinType.from_parsed_uri(parsed_source) == JoinType.URL
        or JoinType.from_parsed_uri(parsed_start) == JoinType.URL
    ):
        return _make_absolute_href_url(parsed_source, parsed_start, start_is_dir)
    else:
        return _make_absolute_href_path(parsed_source, parsed_start, start_is_dir)


def is_absolute_href(href: str) -> bool:
    """Determines if an HREF is absolute or not.

    May be used on either local file paths or URLs.

    Args:
        href : The HREF to consider.

    Returns:
        bool: ``True`` if the given HREF is absolute, ``False`` if it is relative.
    """
    parsed = safe_urlparse(href)
    return parsed.scheme != "" or _pathlib.isabs(parsed.path)


def datetime_to_str(dt: datetime) -> str:
    """Converts a :class:`datetime.datetime` instance to an ISO8601 string in the
    `RFC 3339, section 5.6
    <https://datatracker.ietf.org/doc/html/rfc3339#section-5.6>`__ format required by
    the :stac-spec:`STAC Spec <master/item-spec/common-metadata.md#date-and-time>`.

    Args:
        dt : The datetime to convert.

    Returns:
        str: The ISO8601 (RFC 3339) formatted string representing the datetime.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    timestamp = dt.isoformat()
    zulu = "+00:00"
    if timestamp.endswith(zulu):
        timestamp = "{}Z".format(timestamp[: -len(zulu)])

    return timestamp


def str_to_datetime(s: str) -> datetime:
    """Converts a string timestamp to a :class:`datetime.datetime` instance using
    :meth:`dateutil.parser.parse` under the hood. The input string may be in any
    format :std:doc:`supported by the parser <parser>`.

    Args:
        s (str) : The string to convert to :class:`datetime.datetime`.
    """
    return dateutil.parser.isoparse(s)


def geometry_to_bbox(geometry: Dict[str, Any]) -> List[float]:
    """Extract the bounding box from a geojson geometry

    Args:
        geometry : GeoJSON geometry dict

    Returns:
        list: Bounding box of geojson geometry, formatted according to:
        https://tools.ietf.org/html/rfc7946#section-5
    """
    coords = geometry["coordinates"]

    lats: List[float] = []
    lons: List[float] = []

    def extract_coords(coords: List[Union[List[float], List[List[Any]]]]) -> None:
        for x in coords:
            # This handles points
            if isinstance(x, float):
                assert isinstance(
                    coords[0], float
                ), f"Type mismatch: {coords[0]} is not a float"
                assert isinstance(
                    coords[1], float
                ), f"Type mismatch: {coords[1]} is not a float"
                lats.append(coords[0])
                lons.append(coords[1])
                return
            if isinstance(x[0], list):
                extract_coords(x)  # type:ignore
            else:
                lat, lon = x
                lats.append(lat)  # type:ignore
                lons.append(lon)  # type:ignore

    extract_coords(coords)

    lons.sort()
    lats.sort()

    bbox = [lats[0], lons[0], lats[-1], lons[-1]]

    return bbox


T = TypeVar("T")
U = TypeVar("U")


def map_opt(fn: Callable[[T], U], v: Optional[T]) -> Optional[U]:
    """Maps the value of an optional type to another value, returning
    ``None`` if the input option is ``None``.

    Args:
        fn (Callable) : A function that maps the non-optional value of type ``T`` to
            another value. This function will be called on non-``None`` values of
            ``v``.
        v (Optional[T]) : The optional value to map.

    Examples:

        Given an optional value like the following...

        .. code-block:: python

            maybe_item: Optional[pystac.Item] = ...

        ...you could replace...

        .. code-block:: python

            maybe_item_id: Optional[str] = None
            if maybe_item is not None:
                maybe_item_id = maybe_item.id

        ...with:

        .. code-block:: python

            maybe_item_id = map_opt(lambda item: item.id, maybe_item)
    """
    return v if v is None else fn(v)


def get_opt(option: Optional[T]) -> T:
    """Retrieves the value of the ``Optional`` type, raising a :exc:`ValueError` if
    the value is ``None``.

    Use this to get a properly typed value from an optional
    in contexts where you can be certain the value is not ``None``.
    If there is potential for a non-``None`` value, it's best to handle
    the ``None`` case of the optional instead of using this method.

    Args:
        option (Optional[T]) : Some ``Optional`` value

    Returns:
        The value of type T wrapped by the Optional[T]

    Examples:

        .. code-block:: python

            d = {
                "some_key": "some_value"
            }

            # This passes
            val: str = get_opt(d.get("some_key"))

            # This raises a ValueError
            val: str = get_opt(d.get("does_not_exist"))
    """
    if option is None:
        raise ValueError("Cannot get value from None")
    return option


def get_required(option: Optional[T], obj: Union[str, Any], prop: str) -> T:
    """Retrieves an ``Optional`` value that comes from a required property of some
    object. If the option is ``None``, throws an :exc:`pystac.RequiredPropertyMissing`
    with the given obj and property.

    This method is primarily used internally to retrieve properly typed required
    properties from dictionaries. For an example usage, see the
    :attr:`pystac.extensions.eo.Band.name` source code.

    Args:
        option (Optional[T]) : The ``Optional`` value.
        obj (str, Any) : The object from which the value is being retrieved. This will
            be passed to the :exc:`~pystac.RequiredPropertyMissing` exception if
            ``option`` is ``None``.
        prop (str) : The name of the property being retrieved.

    Returns:
        T : The properly typed, non-``None`` value.
    """
    if option is None:
        raise RequiredPropertyMissing(obj, prop)
    return option
