from abc import (ABC, abstractmethod)

from pystac.link import (Link, LinkType)
from pystac.io import STAC_IO

class STACObject(ABC):
    """A STAC Object has links, and can be cloned or copied."""

    def __init__(self):
        self.links = []

    def add_link(self, link):
        if self.id == 'test' and link.rel == 'parent':
            raise Exception('{}'.format(self.links))
        link.set_owner(self)
        self.links.append(link)
        return self

    def add_links(self, links):
        for link in links:
            self.add_link(link)
        return self

    def remove_links(self, rel):
        self.links = [l for l in self.links if l.rel != rel]
        return self

    def get_single_link(self, rel):
        return next((l for l in self.links if l.rel == rel), None)

    def get_root(self):
        root_link = self.get_root_link()
        if root_link:
            return root_link.resolve_stac_object().target
        else:
            return None

    def get_root_link(self):
        return self.get_single_link('root')

    def set_root(self, root, link_type=None):
        if not link_type:
            prev = self.get_single_link('root')
            if prev is not None:
                link_type = prev.link_type
            else:
                link_type = LinkType.ABSOLUTE
        self.remove_links('root')
        self.add_link(Link.root(root, link_type=link_type))
        return self

    def get_parent(self):
        parent_link = self.get_single_link('parent')
        if parent_link:
            return parent_link.resolve_stac_object().target
        else:
            return None

    def set_parent(self, parent, link_type=None):
        if not link_type:
            prev = self.get_single_link('parent')
            if prev is not None:
                link_type = prev.link_type
            else:
                link_type = LinkType.ABSOLUTE
        self.remove_links('parent')
        self.add_link(Link.parent(parent, link_type=link_type))
        return self

    def get_self_href(self):
        self_link = self.get_single_link('self')
        if self_link:
            return self_link.target
        else:
            return None

    def set_self_href(self, href):
        self.remove_links('self')
        self.add_link(Link.self_href(href))
        return self

    def get_stac_objects(self, rel, parent=None):
        result = []
        for i in range(0, len(self.links)):
            link = self.links[i]
            if link.rel == rel:
                link.resolve_stac_object(root=self.get_root())
                result.append(link.target)
        return result

    def get_links(self, rel=None):
        if rel is None:
            return self.links
        else:
            return [l for l in self.links if l.rel == rel]

    def clear_links(self, rel=None):
        if rel is not None:
            self.links = [l for l in self.links if l.rel != rel]
        else:
            self.links = []
        return self

    def make_links_relative(self):
        for l in self.links:
            if l.rel != 'self':
                l.make_relative()
        return self

    def make_links_absolute(self):
        for l in self.links:
            if l.rel != 'self':
                l.make_absolute()
        return self

    def save_object(self, include_self_link=True):
        """Saves this STAC Object to it's 'self' HREF.

        Args:
          include_self_link: If this is true, include the 'self' link with this object.
              Otherwise, leave out the self link (required for relative links
              and self contained catalogs).
        """
        STAC_IO.save_json(self.get_self_href(),
                          self.to_dict(include_self_link=include_self_link))

    def full_copy(self, root=None, parent=None):
        """Create a full copy of this STAC object and any stac objects linked to by
        this object.
        """
        clone = self.clone()

        if root is None:
            root = clone
        clone.set_root(root)
        if parent:
            clone.set_parent(parent)

        link_rels = set(self._object_links())
        for link in clone.links:
            if link.rel in link_rels:
                link.resolve_stac_object()
                target = link.target
                if target in root._resolved_objects:
                    target = root._resolved_objects.get(target)
                else:
                    copied_target = target.full_copy(root=root, parent=clone)
                    root._resolved_objects.set(copied_target)
                    target = copied_target
                if link.rel in ['child', 'item']:
                    target.set_root(root)
                    target.set_parent(clone)
                link.target = target

        return clone

    def fully_resolve(self):
        """Ensure all STACObjects linked to by this STACObject are
        resolved. This is important for operations such as changing
        HREFs.
        """
        link_rels = set(self._object_links())
        for link in self.links:
            if link.rel in link_rels:
                if not link.is_resolved():
                    link.resolve_stac_object(root=self.get_root())
                    link.target.fully_resolve()

    @abstractmethod
    def _object_links(self):
        """Inhereted classes return a list of link 'rel' types that represent
        STACObjects linked to by this object (not including root, parent or self).
        This can include optional relations (which may not be present).
        """
        pass

    @abstractmethod
    def to_dict(self, include_self_link=True):
        pass

    @abstractmethod
    def clone(self):
        pass

    @staticmethod
    def from_file(href):
        return STAC_IO.read_stac_object(href)
