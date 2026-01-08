from __future__ import annotations

from abc import ABC
from collections.abc import Iterator
from typing import TYPE_CHECKING

from .link import Link
from .rel_type import RelType
from .stac_object import STACObject

if TYPE_CHECKING:
    from .href_generator import HrefGenerator
    from .item import Item


class Container(STACObject, ABC):
    def get_items(self, recursive: bool = False) -> Iterator[Item]:
        for link in self.links:
            if link.is_item():
                from .item import Item

                stac_object = link.get_target(start_href=self._href, reader=self.reader)
                if isinstance(stac_object, Item):
                    yield stac_object
            elif recursive and link.is_child():
                stac_object = link.get_target(start_href=self._href, reader=self.reader)
                if isinstance(stac_object, Container):
                    yield from stac_object.get_items(recursive=True)

    def add_item(self, item: Item) -> None:
        self.links.append(Link(target=item, rel=RelType.ITEM))

    def get_child(self, id: str) -> Container | None:
        for link in self.get_child_links():
            stac_object = link.get_target(start_href=self._href, reader=self.reader)
            if isinstance(stac_object, Container) and stac_object.id == id:
                return stac_object

    def add_child(self, child: Container) -> None:
        link = Link(target=child, rel=RelType.CHILD)
        self.links.append(link)

    def get_child_links(self) -> list[Link]:
        return [link for link in self.links if link.is_child()]

    def get_item_links(self) -> list[Link]:
        return [link for link in self.links if link.is_item()]

    def normalize_hrefs(self, root_href: str) -> None:
        from .href_generator import BestPracticesHrefGenerator

        href_generator = BestPracticesHrefGenerator()
        self.set_self_href(href_generator.get_root(root_href, self))
        self.render_all(href_generator=href_generator)

    def render_all(
        self,
        use_absolute_links: bool = False,
        href_generator: HrefGenerator | None = None,
    ) -> None:
        for _ in self.render(use_absolute_links, href_generator):
            pass

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
