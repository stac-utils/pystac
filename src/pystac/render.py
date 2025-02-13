"""Use renderers to build links and set hrefs on STAC objects, their children,
and their items.

STAC catalogs look like trees:

```mermaid
graph TD
    catalog["Catalog"] --> collection["Collection"] --> item["Item"]
```

Via `links`, STAC objects can "live" anywhere ... their locations on a
filesystem or in blob storage don't have to mirror their tree structure. In
PySTAC v2.0, STAC "trees" are mapped onto hrefs via a process called "rendering":

```python
catalog = Catalog("an-id", "a description")
collection = Collection("a-collection", "the collection")
item = Item("an-item")
catalog.add_child(collection)
collection.add_item(item)

catalog.render("/pystac")

assert catalog.get_self_href() == "/pystac/catalog.json"
assert collection.get_self_href() == "/pystac/a-collection/collection.json"
assert item.get_self_href() == "/pystac/a-collection/an-item/an-item.json"
```

Note:
    In PySTAC v1.x, setting hrefs and links was handled in
    [layout](https://pystac.readthedocs.io/en/stable/api/layout.html).
"""

from abc import ABC, abstractmethod

from .catalog import Catalog
from .collection import Collection
from .container import Container
from .item import Item
from .link import Link
from .stac_object import STACObject


class Renderer(ABC):
    """The base class for all renderers."""

    def __init__(self, root: str):
        """Creates a new renderer, rooted at the location provided."""
        self.root = root

    def render(self, stac_object: STACObject) -> str:
        """Render a single STAC object by modifying its self href and links.

        Returns:
            This object's href
        """
        from .catalog import Catalog
        from .collection import Collection
        from .item import Item

        if (parent_link := stac_object.get_parent_link()) and parent_link.href:
            # TODO is this true for every renderer?
            base = parent_link.href.rsplit("/", 1)[0] + "/" + stac_object.id
        else:
            base = self.root

        if isinstance(stac_object, Item):
            href = self.get_item_href(stac_object, base)
        elif isinstance(stac_object, Catalog):
            href = self.get_catalog_href(stac_object, base)
        elif isinstance(stac_object, Collection):
            href = self.get_collection_href(stac_object, base)
        else:
            raise Exception("unreachable")
        stac_object.href = href
        stac_object.set_self_link()

        root_link = stac_object.get_root_link()
        if isinstance(stac_object, Container):
            if root_link is None:
                root_link = Link.root(stac_object)
            for link in filter(
                lambda link: link.is_child() or link.is_item(), stac_object.iter_links()
            ):
                leaf = link.get_stac_object()
                leaf.set_link(root_link)
                leaf.set_link(Link.parent(stac_object))
                link.href = self.render(leaf)

        return href

    @abstractmethod
    def get_item_href(self, item: Item, base: str) -> str:
        """Returns an item's href."""

    @abstractmethod
    def get_collection_href(self, collection: Collection, base: str) -> str:
        """Returns a collection's href."""

    @abstractmethod
    def get_catalog_href(self, catalog: Catalog, base: str) -> str:
        """Returns a catalog's href."""


class DefaultRenderer(Renderer):
    """The default renderer, based on STAC [best practices](https://github.com/radiantearth/stac-spec/blob/master/best-practices.md#catalog-layout)."""

    def get_item_href(self, item: Item, base: str) -> str:
        return base + "/" + item.id + ".json"

    def get_catalog_href(self, catalog: Catalog, base: str) -> str:
        return base + "/catalog.json"

    def get_collection_href(self, collection: Collection, base: str) -> str:
        return base + "/collection.json"
