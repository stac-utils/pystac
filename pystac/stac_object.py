from abc import (ABC, abstractmethod)
from pystac.link import Link

class STACObject(ABC):
    """A STAC Object has links, can can be cloned or copied."""

    def __init__(self):
        self.links = []

    def add_link(self, link):
        self.links.append(link)

    def add_links(self, links):
        self.links.extend(links)

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
                link.resolve_stac_object(root=self.get_root(), parent=parent)
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

    def full_copy(self, root=None, parent=None):
        clone = self.clone()

        if root is None:
            root = clone
        clone.set_root(root)
        if parent:
            clone.set_parent(parent)

        for link in (clone.get_child_links() + clone.get_item_links()):
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

    @abstractmethod
    def clone(self):
        pass
