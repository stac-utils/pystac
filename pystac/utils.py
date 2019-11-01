import os
from urllib.parse import urlparse


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
    parsed_source = urlparse(source_href)
    parsed_start = urlparse(start_href)
    if not (parsed_source.scheme == parsed_start.scheme
            and parsed_source.netloc == parsed_start.netloc):
        return source_href

    if start_is_dir:
        start_dir = parsed_start.path
    else:
        start_dir = os.path.dirname(parsed_start.path)
    relpath = os.path.relpath(parsed_source.path, start_dir)
    if not relpath.startswith('.'):
        relpath = './{}'.format(relpath)

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
        then it will be returned unchanged.
    """
    if start_href is None:
        start_href = os.getcwd()
        start_is_dir = True

    parsed_source = urlparse(source_href)
    if parsed_source.scheme == '':
        if not os.path.isabs(parsed_source.path):
            parsed_start = urlparse(start_href)
            if start_is_dir:
                start_dir = parsed_start.path
            else:
                start_dir = os.path.dirname(parsed_start.path)
            abs_path = os.path.abspath(
                os.path.join(start_dir, parsed_source.path))
            if parsed_start.scheme != '':
                return '{}://{}{}'.format(parsed_start.scheme,
                                          parsed_start.netloc, abs_path)
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
    parsed = urlparse(href)
    return parsed.scheme != '' or os.path.isabs(parsed.path)
