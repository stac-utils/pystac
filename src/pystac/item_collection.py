from __future__ import annotations

import copy
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal, TypedDict, override

from typing_extensions import deprecated

from .container import Container
from .errors import STACTypeError
from .item import Item
from .reader import DEFAULT_READER, Reader
from .utils import make_absolute_href


class T_ItemCollection(TypedDict):
    type: Literal["FeatureCollection"]
    features: list[dict[str, Any]]


class ItemCollection:
    def __init__(self, items: list[Item], **kwargs: Any):
        self.items: list[Item] = [Item.try_from(item) for item in items]

        if "root" in kwargs:
            raise

        extra_fields = kwargs.pop("extra_fields", {})
        self.extra_fields: dict[str, Any] =  kwargs
        if extra_fields:
            warnings.warn(
                "Pass extra_fields entries as kwargs, "
                "instead of in extra_fields dictionary."
            )
            self.extra_fields.update(extra_fields)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> Item:
        return self.items[index]

    def __iter__(self) -> Iterator[Item]:
        return iter(self.items)

    def __contains__(self, __x: Item) -> bool:
        return __x in self.items

    def __add__(self, other: Any) -> ItemCollection:
        if not isinstance(other, ItemCollection):
            return NotImplemented

        combined = [*self.items, *other.items]
        return ItemCollection(items=combined)

    @override
    def __repr__(self) -> str:
        return f"ItemCollection({self.items})"

    def to_dict(self) -> dict[str, Any]:
        data = copy.deepcopy(self.extra_fields)
        return {
            "type": "FeatureCollection",
            "features": [item.to_dict() for item in self.items],
            **data,
        }

    def clone(self) -> ItemCollection:
        return copy.deepcopy(self)

    @deprecated("Use `ItemCollection.from_dict` instead")
    @staticmethod
    def is_item_collection(data: dict[str, Any]) -> bool:
        return data.get("type", "") == "FeatureCollection"

    @classmethod
    def try_from(cls, data: dict[str, Any] | ItemCollection) -> ItemCollection:
        if isinstance(data, ItemCollection):
            return data
        else:
            return cls(**data)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        preserve_dict: bool = True,
        root: Container | None = None,
    ) -> ItemCollection:
        if data.get("type", "") != "FeatureCollection":
            raise STACTypeError(data, cls)

        if preserve_dict:
            data = copy.deepcopy(data)

        items = data.get("features", [])
        extra_fields = {k: v for k, v in data.items() if k not in ("features", "type")}

        return cls(
            items=[Item.from_dict(item, root=root) for item in items], **extra_fields
        )

    @classmethod
    def from_file(
        cls, path: str | Path, reader: Reader = DEFAULT_READER
    ) -> ItemCollection:
        href = make_absolute_href(str(path))
        data = reader.get_json(href)

        return ItemCollection.from_dict(data)
