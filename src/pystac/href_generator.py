from typing import TYPE_CHECKING, Protocol

from .utils import make_absolute_href

if TYPE_CHECKING:
    from .container import Container
    from .item import Item


class HrefGenerator(Protocol):
    def get_root(self, prefix: str, container: Container) -> str: ...
    def get_child(self, parent_href: str, container: Container) -> str: ...
    def get_item(self, parent_href: str, item: Item) -> str: ...


class BestPracticesHrefGenerator:
    def get_root(self, prefix: str, container: Container) -> str:
        from .catalog import Catalog
        from .collection import Collection

        if isinstance(container, Catalog):
            return make_absolute_href(prefix, "./catalog.json", start_is_dir=True)
        elif isinstance(container, Collection):
            return make_absolute_href(prefix, "./collection.json", start_is_dir=True)
        else:
            raise ValueError(f"Unsupported root type: {type(container)}")

    def get_child(self, parent_href: str, container: Container) -> str:
        from .catalog import Catalog
        from .collection import Collection

        if isinstance(container, Catalog):
            file_name = "catalog.json"
        elif isinstance(container, Collection):
            file_name = "collection.json"
        else:
            raise ValueError(f"Unsupported child type: {type(container)}")

        return make_absolute_href(
            parent_href, "/".join((container.id, file_name)), start_is_dir=False
        )

    def get_item(self, parent_href: str, item: Item) -> str:
        return make_absolute_href(
            parent_href, "/".join((item.id, f"{item.id}.json")), start_is_dir=False
        )


DEFAULT_HREF_GENERATOR = BestPracticesHrefGenerator()
