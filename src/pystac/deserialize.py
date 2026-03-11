from typing import Any

from .stac_object import STACObject


def from_dict(data: dict[str, Any]) -> STACObject:
    match data.get("type"):
        case "Catalog":
            from .catalog import Catalog

            return Catalog.from_dict(data)
        case "Collection":
            from .collection import Collection

            return Collection.from_dict(data)
        case "Feature":
            from .item import Item

            return Item.from_dict(data)
        case _:
            raise ValueError(f"Unknown STAC type: {data['type']}")
