import os
import posixpath
from urllib.parse import (urlparse, ParseResult as URLParseResult)
from datetime import timezone
import dateutil.parser

# Allow for modifying the path library for testability
# (i.e. testing Windows path manipulation on non-Windows systems)
_pathlib = os.path


def _urlparse(href):
    """Version of URL parse that takes into account windows paths.

    A windows absolute path will be parsed with a scheme from urllib.parse.urlparse.
    This method will take this into account.
    """
    parsed = urlparse(href)
    if parsed.scheme != '' and href.lower().startswith('{}:\\'.format(parsed.scheme)):
        return URLParseResult(scheme='',
                              netloc='',
                              path='{}:{}'.format(parsed.scheme, parsed.path),
                              params=parsed.params,
                              query=parsed.query,
                              fragment=parsed.fragment)
    else:
        return parsed


def _join(is_path, *args):
    """Version of os.path.join that takes into account whether or not we are working
    with a URL.

    A windows system shouldn't use os.path.join if we're working with a URL.
    """
    if is_path:
        return _pathlib.join(*args)
    else:
        return posixpath.join(*args)


def make_relative_href(source_href, start_href, start_is_dir=False):
    """Makes a given HREF relative to the given starting HREF.

    Args:
        source_href (str): The HREF to make relative.
        start_href (str): The HREF that the resulting HREF will be relative with
            respect to.
        start_is_dir (str): If True, the start_href is treated as a directory.
            Otherwise, the start_href is considered to be a file HREF. Defaults to False.

    Returns:
        str: The relative HREF. If the source_href and start_href do not share a common
        parent, then source_href will be returned unchanged.
    """

    parsed_source = _urlparse(source_href)
    parsed_start = _urlparse(start_href)
    if not (parsed_source.scheme == parsed_start.scheme
            and parsed_source.netloc == parsed_start.netloc):
        return source_href

    is_path = parsed_start.scheme == ''

    if start_is_dir:
        start_dir = parsed_start.path
    else:
        start_dir = _pathlib.dirname(parsed_start.path)
    relpath = _pathlib.relpath(parsed_source.path, start_dir)
    if not is_path:
        relpath = relpath.replace('\\', '/')
    if not relpath.startswith('.'):
        relpath = _join(is_path, '.', relpath)

    return relpath


def make_absolute_href(source_href, start_href=None, start_is_dir=False):
    """Makes a given HREF absolute based on the given starting HREF.

    Args:
        source_href (str): The HREF to make absolute.
        start_href (str): The HREF that will be used as the basis for which to resolve
            relative paths, if source_href is a relative path. Defaults to the
            current working directory.
        start_is_dir (str): If True, the start_href is treated as a directory.
            Otherwise, the start_href is considered to be a file HREF. Defaults to False.

    Returns:
        str: The absolute HREF. If the source_href is already an absolute href,
        then it will be returned unchanged. If the source_href it None, it will
        return None.
    """
    if source_href is None:
        return None

    if start_href is None:
        start_href = os.getcwd()
        start_is_dir = True

    parsed_source = _urlparse(source_href)
    if parsed_source.scheme == '':
        if not _pathlib.isabs(parsed_source.path):
            parsed_start = _urlparse(start_href)
            is_path = parsed_start.scheme == ''
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

            if parsed_start.scheme != '':
                if not is_path:
                    abs_path = abs_path.replace('\\', '/')

                return '{}://{}{}'.format(parsed_start.scheme, parsed_start.netloc, abs_path)
            else:
                return abs_path
        else:
            return source_href
    else:
        return source_href


def is_absolute_href(href):
    """Determines if an HREF is absolute or not.

    Args:
        href (str): The HREF to consider.

    Returns:
        bool: True if the given HREF is absolute, False if it is relative.
    """
    parsed = _urlparse(href)
    return parsed.scheme != '' or _pathlib.isabs(parsed.path)


def datetime_to_str(dt):
    """Convert a python datetime to an ISO8601 string

    Args:
        dt (datetime): The datetime to convert.

    Returns:
        str: The ISO8601 formatted string representing the datetime.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    timestamp = dt.isoformat()
    zulu = '+00:00'
    if timestamp.endswith(zulu):
        timestamp = '{}Z'.format(timestamp[:-len(zulu)])

    return timestamp


def str_to_datetime(s):
    return dateutil.parser.parse(s)


def geometry_to_bbox(geometry):
    """Extract the bounding box from a geojson geometry

    Args:
        geometry (dict): GeoJSON geometry dict

    Returns:
        list: Bounding box of geojson geometry, formatted according to:
        https://tools.ietf.org/html/rfc7946#section-5
    """
    coords = geometry['coordinates']

    lats = []
    lons = []

    def extract_coords(coords):
        for x in coords:
            # This handles points
            if isinstance(x, float):
                lats.append(coords[0])
                lons.append(coords[1])
                return
            if isinstance(x[0], list):
                extract_coords(x)
            else:
                lat, lon = x
                lats.append(lat)
                lons.append(lon)

    extract_coords(coords)

    lons.sort()
    lats.sort()

    bbox = [lats[0], lons[0], lats[-1], lons[-1]]

    return bbox
