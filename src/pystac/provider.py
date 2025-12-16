from __future__ import annotations

from enum import Enum
from typing import Any

from typing_extensions import Self


class Provider:
    @classmethod
    def from_dict(cls: type[Self], d: dict[str, Any]) -> Self:
        return cls(**d)

    def __init__(
        self,
        name: str,
        description: str | None = None,
        roles: list[Role | str] | None = None,
        url: str | None = None,
    ):
        self.name = name
        self.description = description
        self.roles = roles
        self.url = url

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"name": self.name}
        if self.description is not None:
            d["description"] = self.description
        if self.roles is not None:
            d["roles"] = [
                role.value if isinstance(role, Role) else role for role in self.roles
            ]
        if self.url is not None:
            d["url"] = self.url
        return d


class Role(Enum):
    LICENSOR = "LICENSOR"
    PRODUCER = "PRODUCER"
    PROCESSOR = "PROCESSOR"
    HOST = "HOST"
