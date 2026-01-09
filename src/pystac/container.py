from __future__ import annotations

import os.path
from abc import ABC
from collections.abc import Iterator
from typing import TYPE_CHECKING

from typing_extensions import deprecated

from pystac.errors import STACError
from pystac.stac_io import StacIO
from pystac.utils import make_absolute_href, make_relative_href

from .link import Link
from .rel_type import RelType
from .stac_object import STACObject

if TYPE_CHECKING:
    from .catalog import CatalogType  # pyright: ignore[reportDeprecated]
    from .href_generator import HrefGenerator
    from .item import Item
    from .writer import Writer


class Container(STACObject, ABC):
    def get_items(self, *ids: str, recursive: bool = False) -> Iterator[Item]:
        for link in self.links:
            if link.is_item():
                from .item import Item

                stac_object = link.get_target(start_href=self._href, reader=self.reader)
                if isinstance(stac_object, Item) and (not ids or stac_object.id in ids):
                    yield stac_object
            elif recursive and link.is_child():
                stac_object = link.get_target(start_href=self._href, reader=self.reader)
                if isinstance(stac_object, Container):
                    yield from stac_object.get_items(*ids, recursive=True)

    def get_item_links(self) -> list[Link]:
        return [link for link in self.links if link.is_item()]

    def add_item(self, item: Item, set_parent: bool = True) -> Link:
        from .item import Item

        if not isinstance(item, Item):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise STACError("Cannot add a non-item as an item")  # pyright: ignore[reportUnreachable]

        item_link = Link(target=item, rel=RelType.ITEM)
        self.links.append(item_link)

        if set_parent:
            parent_link = Link(target=self, rel=RelType.PARENT)
            item.remove_links(RelType.PARENT)
            item.links.append(parent_link)

        return item_link

    def add_items(self, items: list[Item]) -> list[Link]:
        links: list[Link] = []
        for item in items:
            links.append(self.add_item(item))
        return links

    def remove_item(self, id: str) -> Item | None:
        from .item import Item

        removed_item = None
        index = None
        for i, link in enumerate(self.links):
            if link.is_item():
                stac_object = link.get_target(
                    start_href=self.get_self_href(), reader=self.reader
                )
                if isinstance(stac_object, Item) and stac_object.id == id:
                    removed_item = stac_object
                    index = i
                    break

        if index is not None:
            _ = self.links.pop(index)

        return removed_item

    def clear_items(self) -> None:
        self.links: list[Link] = [link for link in self.links if not link.is_item()]

    def get_child(self, id: str, recursive: bool = False) -> Container | None:
        for child in self.get_children(recursive=recursive):
            if child.id == id:
                return child

    def get_children(self, recursive: bool = False) -> Iterator[Container]:
        for link in self.links:
            if link.is_child():
                stac_object = link.get_target(start_href=self._href, reader=self.reader)
                if isinstance(stac_object, Container):
                    yield stac_object
                    if recursive:
                        yield from stac_object.get_children(recursive=recursive)

    def get_child_links(self) -> list[Link]:
        return [link for link in self.links if link.is_child()]

    def add_child(self, child: Container, set_parent: bool = True) -> Link:
        if not isinstance(child, Container):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise STACError("Only catalogs or collections can be children")  # pyright: ignore[reportUnreachable]

        child_link = Link(target=child, rel=RelType.CHILD)
        self.links.append(child_link)

        if set_parent:
            parent_link = Link(target=self, rel=RelType.PARENT)
            child.remove_links(RelType.PARENT)
            child.links.append(parent_link)

        if root := self.get_root():
            child.set_root(root)
        else:
            child.set_root(self)

        return child_link

    def add_children(self, children: list[Container]) -> list[Link]:
        links: list[Link] = []
        for child in children:
            links.append(self.add_child(child))
        return links

    def remove_child(self, id: str) -> Container | None:
        removed_child = None
        index = None
        for i, link in enumerate(self.links):
            if link.is_child():
                stac_object = link.get_target(
                    start_href=self.get_self_href(), reader=self.reader
                )
                if isinstance(stac_object, Container) and stac_object.id == id:
                    removed_child = stac_object
                    index = i
                    break

        if index is not None:
            _ = self.links.pop(index)
            assert removed_child
            removed_child.remove_links(RelType.PARENT)
            _ = removed_child.remove_root()

        return removed_child

    def clear_children(self) -> None:
        links: list[Link] = []
        for link in self.links:
            if link.is_child():
                child = link.get_target(self.get_self_href(), self.reader)
                child.remove_links(RelType.PARENT)
                _ = child.remove_root()
            else:
                links.append(link)
        self.links = links

    @deprecated("Call .normalize_hrefs() and then .save_all()")
    def normalize_and_save(
        self,
        root_href: str,
        catalog_type: CatalogType | None = None,  # pyright: ignore[reportDeprecated]
    ) -> None:
        from .catalog import CatalogType  # pyright: ignore[reportDeprecated]

        self.normalize_hrefs(
            root_href,
            use_absolute_links=catalog_type == CatalogType.ABSOLUTE_PUBLISHED,  # pyright: ignore[reportDeprecated]
        )
        self.save_all()

    @deprecated("Use .save_all()")
    def save(
        self,
        catalog_type: CatalogType | None = None,  # pyright: ignore[reportDeprecated]
        dest_href: str | None = None,
        stac_io: StacIO | None = None,
    ) -> None:
        from .catalog import CatalogType  # pyright: ignore[reportDeprecated]

        if catalog_type:
            # In PySTAC v1, Link.to_dict() implicitly converted hrefs. In PySTAC
            # v2, we have to explicitly convert the hrefs before saving.
            self.render_all(
                use_absolute_links=catalog_type == CatalogType.ABSOLUTE_PUBLISHED  # pyright: ignore[reportDeprecated]
            )

            include_self_links = catalog_type not in (
                CatalogType.RELATIVE_PUBLISHED,  # pyright: ignore[reportDeprecated]
                CatalogType.SELF_CONTAINED,  # pyright: ignore[reportDeprecated]
            )
        else:
            include_self_links = True

        if stac_io:
            from .writer import StacIOWriter  #  pyright: ignore[reportDeprecated]

            writer = StacIOWriter(stac_io)  #  pyright: ignore[reportDeprecated]
        else:
            writer = None

        self.save_all(
            dest_href=dest_href, writer=writer, include_self_links=include_self_links
        )

    def normalize_hrefs(self, root_href: str, use_absolute_links: bool = False) -> None:
        from .href_generator import BestPracticesHrefGenerator

        href_generator = BestPracticesHrefGenerator()
        previous_self_href = self.get_self_href()
        self.set_self_href(href_generator.get_root(root_href, self))
        self.render_all(
            use_absolute_links=use_absolute_links,
            href_generator=href_generator,
            previous_self_href=previous_self_href,
        )

    def render_all(
        self,
        use_absolute_links: bool = False,
        href_generator: HrefGenerator | None = None,
        previous_self_href: str | None = None,
    ) -> None:
        for _ in self.render(use_absolute_links, href_generator, previous_self_href):
            pass

    def save_all(
        self,
        dest_href: str | None = None,
        writer: Writer | None = None,
        include_self_links: bool = True,
    ) -> None:
        for _ in self.save_iter(
            dest_href=dest_href, writer=writer, include_self_links=include_self_links
        ):
            pass

    def save_iter(
        self,
        dest_href: str | None = None,
        writer: Writer | None = None,
        include_self_links: bool = True,
    ) -> Iterator[STACObject]:
        self_href = self.get_self_href()
        if dest_href is not None:
            if self_href:
                self_dest_href = make_absolute_href(
                    make_relative_href(self_href, self_href),
                    dest_href,
                    start_is_dir=True,
                )
            else:
                raise ValueError("Cannot use dest_href without a self href")

            self.save_object(
                dest_href=self_dest_href,
                writer=writer,
                include_self_link=include_self_links,
            )
        else:
            self.save_object(
                dest_href=None, writer=writer, include_self_link=include_self_links
            )

        yield self

        for child in self.get_children():
            if dest_href is not None:
                if (child_self_href := child.get_self_href()) and self_href:
                    child_dest_href = make_absolute_href(
                        make_relative_href(child_self_href, self_href),
                        dest_href,
                        start_is_dir=True,
                    )
                else:
                    raise ValueError(
                        "Cannot use dest_href unless both self and child have self "
                        "hrefs"
                    )
                yield from child.save_iter(
                    dest_href=os.path.dirname(child_dest_href),
                    writer=writer,
                    include_self_links=include_self_links,
                )
            else:
                yield from child.save_iter(
                    dest_href=None, writer=writer, include_self_links=include_self_links
                )

        for item in self.get_items():
            if dest_href is not None:
                if (item_self_href := item.get_self_href()) and self_href:
                    item_dest_href = make_absolute_href(
                        make_relative_href(item_self_href, self_href),
                        dest_href,
                        start_is_dir=True,
                    )
                else:
                    raise ValueError(
                        "Cannot use dest_href unless both self and item have self hrefs"
                    )
                item.save_object(
                    dest_href=item_dest_href,
                    writer=writer,
                    include_self_link=include_self_links,
                )
            else:
                item.save_object(
                    dest_href=None, writer=writer, include_self_link=include_self_links
                )
            yield item

    def walk(self) -> Iterator[tuple[Container, list[Container], list[Item]]]:
        from .item import Item

        self_href = self.get_self_href()
        children: list[Container] = []
        items: list[Item] = []
        for link in self.links:
            if link.is_child() or link.is_item():
                stac_object = link.get_target(self_href, self.reader)
                if isinstance(stac_object, Container):
                    children.append(stac_object)
                elif isinstance(stac_object, Item):
                    items.append(stac_object)

        yield (self, children, items)

        for child in children:
            yield from child.walk()

    def target_in_hierarchy(self, target: STACObject) -> bool:
        for root, _, items in self.walk():
            if root == target or any(item == target for item in items):
                return True

        return False
