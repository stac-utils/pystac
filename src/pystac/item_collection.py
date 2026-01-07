from collections.abc import Iterator
from typing import override

from .item import Item


class ItemCollection:
    def __init__(self, items: list[Item]):
        self.items: list[Item] = items

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> Item:
        return self.items[index]

    def __iter__(self) -> Iterator[Item]:
        return iter(self.items)

    @override
    def __repr__(self) -> str:
        return f"ItemCollection({self.items})"
