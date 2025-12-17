from typing import Protocol

from .catalog import Catalog
from .collection import Collection
from .item import Item
from .stac_object import STACObject


class Render(Protocol):
    def get_href(self, stac_object: STACObject, base: str) -> str:
        """Returns a STAC object's href."""
        ...

    def get_file_name(self, stac_object: STACObject) -> str:
        """Returns a STAC object's file name."""
        ...


class BestPracticesRenderer:
    """The default renderer, based on STAC [best practices](https://github.com/radiantearth/stac-spec/blob/master/best-practices.md#catalog-layout)."""

    def get_href(self, stac_object: STACObject, base: str) -> str:
        return "/".join((base, stac_object.id, self.get_file_name(stac_object)))

    def get_file_name(self, stac_object: STACObject) -> str:
        if isinstance(stac_object, Item):
            return f"{stac_object.id}.json"
        elif isinstance(stac_object, Catalog):
            return "catalog.json"
        elif isinstance(stac_object, Collection):
            return "collection.json"
        else:
            raise Exception("unreachable")
