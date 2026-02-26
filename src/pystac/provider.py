from __future__ import annotations

import copy
from enum import StrEnum
from typing import Any


class Provider:
    def __init__(
        self,
        name: str,
        description: str | None = None,
        roles: list[ProviderRole | str] | None = None,
        url: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.name: str = name
        self.description: str | None = description
        self.roles: list[ProviderRole | str] | None = roles
        self.url: str | None = url
        self.extra_fields: dict[str, Any] = kwargs

    @classmethod
    def try_from(cls, data: Provider | dict[str, Any]) -> Provider:
        if isinstance(data, Provider):
            return data
        else:
            return Provider.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Provider:
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        data = copy.deepcopy(self.extra_fields)
        data["name"] = self.name
        if self.description:
            data["description"] = self.description
        if self.roles:
            data["roles"] = self.roles
        if self.url:
            data["url"] = self.url
        return data


class ProviderRole(StrEnum):
    LICENSOR = "licensor"
    PRODUCER = "producer"
    PROCESSOR = "processor"
    HOST = "host"
