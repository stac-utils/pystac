import os
import posixpath
from pystac.errors import RequiredPropertyMissing
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from urllib.parse import urlparse, ParseResult as URLParseResult
from datetime import datetime, timezone
import dateutil.parser

# Allow for modifying the path library for testability
# (i.e. testing Windows path manipulation on non-Windows systems)
_pathlib = os.path


def _urlparse(href: str) -> URLParseResult:
    """Version of URL parse that takes into account windows paths.

    A windows absolute path will be parsed with a scheme from urllib.parse.urlparse.
    This method will take this into account.
    """
    parsed = urlparse(href)
    if parsed.scheme != "" and href.lower().startswith("{}:\\".format(parsed.scheme)):
        return URLParseResult(
            scheme="",
            netloc="",
            path="{}:{}".format(parsed.scheme, parsed.path),
            params=parsed.params,
            query=parsed.query,
            fragment=parsed.fragment,
        )
    else:
        return parsed


def _join(is_path: bool, *args: str) -> str:
    """Version of os.path.join that takes into account whether or not we are working
    with a URL.

    A windows system shouldn't use os.path.join if we're working with a URL.
    """
    if is_path:
        return _pathlib.join(*args)
    else:
        return posixpath.join(*args)


def make_relative_href(
    source_href: str, start_href: str, start_is_dir: bool = False
) -> str:
    """Makes a given HREF relative to the given starting HREF.

    Args:
        source_href (str): The HREF to make relative.
        start_href (str): The HREF that the resulting HREF will be relative with
            respect to.
        start_is_dir (str): If True, the start_href is treated as a directory.
            Otherwise, the start_href is considered to be a file HREF.
            Defaults to False.

    Returns:
        str: The relative HREF. If the source_href and start_href do not share a common
        parent, then source_href will be returned unchanged.
    """

    parsed_source = _urlparse(source_href)
    parsed_start = _urlparse(start_href)
    if not (
        parsed_source.scheme == parsed_start.scheme
        and parsed_source.netloc == parsed_start.netloc
    ):
        return source_href

    is_path = parsed_start.scheme == ""

    if start_is_dir:
        start_dir = parsed_start.path
    else:
        start_dir = _pathlib.dirname(parsed_start.path)
    relpath = _pathlib.relpath(parsed_source.path, start_dir)
    if not is_path:
        relpath = relpath.replace("\\", "/")
    if not relpath.startswith("."):
        relpath = _join(is_path, ".", relpath)

    return relpath


def make_absolute_href(
    source_href: str, start_href: Optional[str] = None, start_is_dir: bool = False
) -> str:
    """Makes a given HREF absolute based on the given starting HREF.

    Args:
        source_href (str): The HREF to make absolute.
        start_href (str): The HREF that will be used as the basis for which to resolve
            relative paths, if source_href is a relative path. Defaults to the
            current working directory.
        start_is_dir (str): If True, the start_href is treated as a directory.
            Otherwise, the start_href is considered to be a file HREF.
            Defaults to False.

    Returns:
        str: The absolute HREF. If the source_href is already an absolute href,
        then it will be returned unchanged.
    """
    if start_href is None:
        start_href = os.getcwd()
        start_is_dir = True

    parsed_source = _urlparse(source_href)
    if parsed_source.scheme == "":
        if not _pathlib.isabs(parsed_source.path):
            parsed_start = _urlparse(start_href)
            is_path = parsed_start.scheme == ""
            if start_is_dir:
                start_dir = parsed_start.path
            else:
                start_dir = _pathlib.dirname(parsed_start.path)
            abs_path = _pathlib.abspath(_join(is_path, start_dir, parsed_source.path))

            # Account for the normalization of abspath for
            # things like /vsitar// prefixes by replacing the
            # original start_dir text when abspath modifies the start_dir.
            if not start_dir == _pathlib.abspath(start_dir):
                abs_path = abs_path.replace(_pathlib.abspath(start_dir), start_dir)

            if parsed_start.scheme != "":
                if not is_path:
                    abs_path = abs_path.replace("\\", "/")

                return "{}://{}{}".format(
                    parsed_start.scheme, parsed_start.netloc, abs_path
                )
            else:
                return abs_path
        else:
            return source_href
    else:
        return source_href


def is_absolute_href(href: str) -> bool:
    """Determines if an HREF is absolute or not.

    Args:
        href (str): The HREF to consider.

    Returns:
        bool: True if the given HREF is absolute, False if it is relative.
    """
    parsed = _urlparse(href)
    return parsed.scheme != "" or _pathlib.isabs(parsed.path)


def datetime_to_str(dt: datetime) -> str:
    """Convert a python datetime to an ISO8601 string

    Args:
        dt (datetime): The datetime to convert.

    Returns:
        str: The ISO8601 formatted string representing the datetime.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    timestamp = dt.isoformat()
    zulu = "+00:00"
    if timestamp.endswith(zulu):
        timestamp = "{}Z".format(timestamp[: -len(zulu)])

    return timestamp


def str_to_datetime(s: str) -> datetime:
    return dateutil.parser.parse(s)


def geometry_to_bbox(geometry: Dict[str, Any]) -> List[float]:
    """Extract the bounding box from a geojson geometry

    Args:
        geometry (dict): GeoJSON geometry dict

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
                lats.append(coords[0])  # type:ignore
                lons.append(coords[1])  # type:ignore
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
    """Maps the value of an option to another value, returning
    None if the input option is None.
    """
    return v if v is None else fn(v)


def get_opt(option: Optional[T]) -> T:
    """Retrieves the value of the Optional type.

    If the Optional is None, this will raise a value error.
    Use this to get a properly typed value from an optional
    in contexts where you can be certain the value is not None.
    If there is potential for a non-None value, it's best to handle
    the None case of the optional instead of using this method.

    Returns:
        The value of type T wrapped by the Optional[T]
    """
    if option is None:
        raise ValueError("Cannot get value from None")
    return option


def get_required(option: Optional[T], obj: Union[str, Any], prop: str) -> T:
    """Retrieves an optional value that comes from a required property.
    If the option is None, throws an RequiredPropertyError with
    the given obj and property
    """
    if option is None:
        raise RequiredPropertyMissing(obj, prop)
    return option
