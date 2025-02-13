from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

from . import io
from .decorators import v2_deprecated
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
        for link in filter(
            lambda link: link.is_child() or link.is_item(), self.iter_links()
        ):
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

    def render(
        self,
        root: str | Path,
    ) -> None:
        """Renders this container and all of its children and items.

        See the [pystac.render][] documentation for more.

        Args:
            root: The directory at the root of the rendered filesystem tree.
        """
        # TODO allow renderer customization
        from .render import DefaultRenderer

        renderer = DefaultRenderer(str(root))
        renderer.render(self)

    def save(self, writer: Write | None = None) -> None:
        """Saves this container and all of its children.

        This will error if any objects don't have an `href` set. Use
        [Container.render][pystac.Container.render] to set those `href` values.

        Args:
            writer: The writer that will be used for the save operation. If not
                provided, this container's writer will be used.
        """
        if writer is None:
            writer = self.writer
        io.write_file(self, writer=writer)
        for stac_object in self.get_children_and_items():
            if isinstance(stac_object, Container):
                stac_object.save(writer)
            else:
                io.write_file(stac_object, writer=writer)

    @v2_deprecated("Use render() and then save()")
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
