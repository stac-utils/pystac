from __future__ import annotations

from abc import ABC
from collections.abc import Iterator
from typing import TYPE_CHECKING

from typing_extensions import deprecated

from .link import Link
from .rel_type import RelType
from .stac_object import STACObject

if TYPE_CHECKING:
    from .catalog import CatalogType  # pyright: ignore[reportDeprecated]
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

    def save_all(self) -> None:
        for _ in self.save_iter():
            pass

    def save_iter(self) -> Iterator[STACObject]:
        for root, _, items in self.walk():
            root.save_object()
            yield root
            for item in items:
                item.save_object()
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
