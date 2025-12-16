from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from . import deprecate
from .constants import CHILD, ITEM
from .io import Write
from .item import Item
from .link import Link
from .stac_object import STACObject

if TYPE_CHECKING:
    from .collection import Collection


class Container(STACObject):
    """Base class for [Catalog][pystac.Catalog] and [Collection][pystac.Collection].

    While collections are very similar to catalogs, they _technically_ are to
    distinct data structures. To reflect that in code, `Collection` does not
    inherit from `Catalog`. Instead, they both inherit from this `Container`
    class, which doesn't exist in the STAC spec but provides us a useful place
    to store shared behavior.
    """

    def set_stac_version(self, version: str) -> None:
        """Sets the STAC version for this object and all of its children and items.

        Args:
            version: The STAC version
        """
        for root, _, items in self.walk():
            root.stac_version = version
            for item in items:
                item.stac_version = version

    def walk(self) -> Iterator[tuple[Container, list[Container], list[Item]]]:
        """Walks this container, yielding a tuple of this container, its
        children, and its items.

        This works a bit like `os.walk`, but for STAC.

        Returns:
            An iterator over a container, its children, and its items.

        Examples:
            >>> for root, children, items in catalog.walk():
            ...     print(root, children, items)
        """
        children: list[Container] = []
        items: list[Item] = []
        for link in self.iter_links(CHILD, ITEM):
            stac_object = link.get_stac_object()
            if isinstance(stac_object, Container):
                children.append(stac_object)
            if isinstance(stac_object, Item):
                items.append(stac_object)
        yield self, children, items
        for child in children:
            yield from child.walk()

    def add_item(self, item: Item) -> None:
        """Adds an item to this container."""
        self.add_link(Link.item(item))

    def get_items(self, recursive: bool = False) -> Iterator[Item]:
        """Iterates over all items in this container.

        Args:
            recursive: If true, include all items belonging to children as well.
        """
        for link in self.iter_links():
            if link.is_item():
                stac_object = link.get_stac_object()
                if isinstance(stac_object, Item):
                    yield stac_object
            if recursive and link.is_child():
                child = link.get_stac_object()
                if isinstance(child, Container):
                    yield from child.get_items(recursive=recursive)

    def add_child(self, child: Container) -> None:
        """Adds a child to this container."""
        self.add_link(Link.child(child))

    def get_child(
        self, id: str, recursive: bool = False, sort_links_by_id: bool = True
    ) -> Container | None:
        # TODO handle sort links by id
        for child in self.get_children(recursive=recursive):
            if child.id == id:
                return child
        return None

    def get_children(self, recursive: bool = False) -> Iterator[Container]:
        """Iterates over all children in this container.

        Args:
            recursive: If true, include all children's children, and so on.
        """
        for link in filter(lambda link: link.is_child(), self.iter_links()):
            stac_object = link.get_stac_object()
            if isinstance(stac_object, Container):
                yield stac_object
                if recursive:
                    yield from stac_object.get_children(recursive=recursive)

    def get_children_and_items(self) -> Iterator[STACObject]:
        """Iterates over all children and items in this container.

        If you'd like to do recursive iteration over all children and items, use
        [walk][pystac.Container.walk].
        """
        for link in filter(
            lambda link: link.is_child() or link.is_item(), self.iter_links()
        ):
            yield link.get_stac_object()

    def get_collections(self, recursive: bool = False) -> Iterator[Collection]:
        """Iterates over all collections in this container.

        Args:
            recursive: If true, include all children's collections, and so on.
        """
        from .collection import Collection

        for link in filter(lambda link: link.is_child(), self.iter_links()):
            stac_object = link.get_stac_object()
            if isinstance(stac_object, Collection):
                yield stac_object
            if recursive and isinstance(stac_object, Container):
                yield from stac_object.get_collections(recursive=recursive)

    def save(
        self,
        catalog_type: Any = None,
        dest_href: str | Path | None = None,
        stac_io: Any = None,
        *,
        writer: Write | None = None,
    ) -> None:
        if catalog_type:
            deprecate.argument("catalog_type")
        if dest_href:
            deprecate.argument("dest_href")
        if stac_io:
            deprecate.argument("stac_io")
        if writer is None:
            writer = self.writer

        self.save_object(stac_io=stac_io, writer=writer)
        for stac_object in self.get_children_and_items():
            if isinstance(stac_object, Container):
                stac_object.save(
                    writer=writer
                )  # TODO do we need to pass through any of the deprecated arguments?
            else:
                stac_object.save_object(writer=writer)

    @deprecate.function("Use render() and then save()")
    def normalize_and_save(
        self,
        root_href: str,
        catalog_type: Any = None,
        strategy: Any = None,
        stac_io: Any = None,
        skip_unresolved: bool = False,
    ) -> None:
        self.render(root_href)
        self.save()
