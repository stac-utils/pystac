import os
from urllib.parse import urlparse

def make_relative_href(source_href, start_href, start_is_dir=False):
    parsed_source = urlparse(source_href)
    parsed_start = urlparse(start_href)
    if not (parsed_source.scheme == parsed_start.scheme and
            parsed_source.netloc == parsed_start.netloc):
        return source_href

    if start_is_dir:
        start_dir = parsed_start.path
    else:
        start_dir =  os.path.dirname(parsed_start.path)
    relpath = os.path.relpath(parsed_source.path, start_dir)
    if not relpath.startswith('.'):
        relpath = './{}'.format(relpath)

    return relpath


def make_absolute_href(source_href, start_href=None, start_is_dir=False):
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
            abs_path = os.path.abspath(os.path.join(start_dir, parsed_source.path))
            if parsed_start.scheme != '':
                return '{}://{}{}'.format(parsed_start.scheme,
                                          parsed_start.netloc,
                                          abs_path)
            else:
                return abs_path
        else:
            return source_href
    else:
        return source_href

def is_absolute_href(href):
    parsed = urlparse(href)
    return parsed.scheme != '' or os.path.isabs(parsed.path)
