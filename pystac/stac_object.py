from abc import (ABC, abstractmethod)

from pystac.link import Link
from pystac.io import STAC_IO

class STACObject(ABC):
    """A STAC Object has links, and can be cloned or copied."""

    def __init__(self):
        self.links = []

    def add_link(self, link):
        link.set_owner(self)
        self.links.append(link)

    def add_links(self, links):
        for link in links:
            self.add_link(link)

    def get_single_link(self, rel):
        return next((l for l in self.links if l.rel == rel), None)

    def get_root(self):
        root_link = self.get_single_link('root')
        if root_link:
            return root_link.resolve_stac_object().target
        else:
            return None

    def set_root(self, root):
        self.links = [l for l in self.links if l.rel != 'root']
        self.links.append(Link.root(root))

    def get_parent(self):
        parent_link = self.get_single_link('parent')
        if parent_link:
            return parent_link.resolve_stac_object().target
        else:
            return None

    def set_parent(self, parent):
        self.links = [l for l in self.links if l.rel != 'parent']
        self.links.append(Link.parent(parent))

    def get_self_href(self):
        self_link = self.get_single_link('self')
        if self_link:
            return self_link.target
        else:
            return None

    def set_self_href(self, href):
        self.links = [l for l in self.links if l.rel != 'self']
        self.links.append(Link.self_href(href))

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

    def make_links_relative(self):
        for l in self.links:
            if not l.rel == 'self':
                l.make_relative()

    def make_links_absolute(self):
        for l in self.links:
            l.make_absolute()

    def save_object(self, include_self_link=True):
        """Saves this STAC Object to it's 'self' HREF.

        Args:
          include_self_link: If this is true, include the 'self' link with this object. Otherwise,
              leave out the self link (required for relative links and self contained catalogs).
        """
        STAC_IO.save_json(self.get_self_href(),
                          self.to_dict(include_self_link=include_self_link))

    @abstractmethod
    def to_dict(self, include_self_link=True):
        pass

    @abstractmethod
    def clone(self):
        pass

    @abstractmethod
    def full_copy(self, root=None, parent=None):
        """Create a full copy of this STAC object and any children or items
        contained by this object.
        """
        pass
