import os
from copy import copy
from urllib.parse import urlparse

from pystac import STACError
from pystac.io import STAC_IO

class Link:
    def __init__(self, rel, target, media_type=None, title=None, properties=None):
        self.rel = rel
        self.target = target # An object or an href
        self.media_type = media_type
        self.title = title
        self.properties = properties

    def __repr__(self):
        return '<Link rel={} target={}>'.format(self.rel, self.target)

    def resolve_stac_object(self, root=None, parent=None):
        if isinstance(self.target, str):
            # If it's a relative link, base it off the parent.
            target_path = self.target
            parsed = urlparse(self.target)
            if parsed.scheme == '':
                if not os.path.isabs(parsed.path):
                    if parent is None:
                        raise STACError('Relative path {} encountered '
                                        'without parent.'.format(target_path))
                    parent_href = parent.get_self_href()
                    if parent_href is None:
                        raise STACError('Relative path {} encountered '
                                        'without parent "self" link set.'.format(target_path))
                    parsed_parent = urlparse(parent_href)
                    parent_dir = os.path.dirname(parsed_parent.path)
                    abs_path = os.path.abspath(os.path.join(parent_dir, target_path))
                    if parsed_parent.scheme != '':
                        target_path = '{}://{}{}'.format(parsed_parent.scheme,
                                                         parsed_parent.netloc,
                                                         abs_path)
                    else:
                        target_path = abs_path
            print(target_path)

            obj = STAC_IO.read_stac_json(target_path, root=root, parent=parent)
            obj.set_self_href(target_path)
        else:
            obj = self.target

        if root is not None:
            self.target = root._resolved_objects.get_or_set(obj)
            self.target.set_root(root)
        else:
            self.target = obj

        if parent:
            self.target.set_parent(parent)

        return self

    def is_resolved(self):
        return not isinstance(self.target, str)

    def to_dict(self):
        d = { 'rel': self.rel }
        if self.is_resolved():
            d['href'] = self.target.get_self_href()
        else:
            d['href'] = self.target

        if self.media_type is not None:
            d['type'] = self.media_type

        if self.title is not None:
            d['title'] = self.title

        if self.properties:
            for k, v in self.properties.items():
                d[k] = v

        return d

    def clone(self):
        return Link(rel=self.rel,
                    target=self.target,
                    media_type=self.media_type,
                    title=self.title)

    @staticmethod
    def from_dict(d):
        d = copy(d)
        rel = d.pop('rel')
        href = d.pop('href')
        media_type = d.pop('type', None)
        title = d.pop('title', None)

        properties = None
        if any(d):
            properties = d

        return Link(rel=rel,
                    target=href,
                    media_type=media_type,
                    title=title,
                    properties=properties)

    @staticmethod
    def root(c):
        """Creates a link to a root Catalog or Collection."""
        return Link('root', c, media_type='application/json')

    @staticmethod
    def parent(c):
        """Creates a link to a parent Catalog or Collection."""
        return Link('parent', c, media_type='application/json')

    @staticmethod
    def collection(c):
        """Creates a link to an item's Collection."""
        return Link('collection', c, media_type='application/json')

    @staticmethod
    def self_href(href):
        """Creates a self link to the file's location."""
        return Link('self', href, media_type='application/json')

    @staticmethod
    def child(c, title=None):
        """Creates a link to a child Catalog or Collection."""
        return Link('child', c, title=title, media_type='application/json')

    @staticmethod
    def item(item, title=None):
        """Creates a link to an Item."""
        return Link('item', item, title=title, media_type='application/json')
