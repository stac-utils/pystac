import os
from urllib.parse import urlparse

def make_relative_href(source_href, start_href):
    parsed_source = urlparse(source_href)
    parsed_start = urlparse(start_href)
    if not (parsed_source.scheme == parsed_start.scheme and
            parsed_source.netloc == parsed_start.netloc):
        return source_href

    start_dir =  os.path.dirname(parsed_start.path)
    relpath = os.path.relpath(parsed_source.path, start_dir)
    if not relpath.startswith('.'):
        relpath = './{}'.format(relpath)

    return relpath


def make_absolute_href(source_href, start_href):
    parsed_source = urlparse(source_href)
    if parsed_source.scheme == '':
        if not os.path.isabs(parsed_source.path):
            parsed_start = urlparse(start_href)
            parent_dir = os.path.dirname(parsed_start.path)
            abs_path = os.path.abspath(os.path.join(parent_dir, parsed_source.path))
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
