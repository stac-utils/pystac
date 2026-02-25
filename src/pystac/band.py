from __future__ import annotations

import copy
from typing import Any, override


class Band:
    def __init__(
        self,
        name: str | None = None,
        **kwargs: Any,
    ):
        self.name: str | None = name
        self.extra_fields: dict[str, Any] = kwargs

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        else:
            return self.extra_fields[key]

    def __setitem__(self, key: str, value: Any) -> None:
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self.extra_fields[key] = value

    def __contains__(self, key: str) -> bool:
        return key == "name" or key in self.extra_fields

    def __deepcopy__(self, memo: dict[int, Any]) -> Band:
        return Band(
            name=self.name,
            **copy.deepcopy(self.extra_fields, memo),
        )

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Band):
            return NotImplemented
        return self.to_dict() == other.to_dict()

    @classmethod
    def try_from(cls, data: dict[str, Any] | Band) -> Band:
        if isinstance(data, Band):
            return data
        else:
            return cls(**data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Band:
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        data = copy.deepcopy(self.extra_fields)
        if self.name:
            data["name"] = self.name
        return data
