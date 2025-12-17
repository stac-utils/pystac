from __future__ import annotations

import copy
from typing import Any

from typing_extensions import override

from .constants import CATALOG_TYPE
from .container import Container
from .link import Link


class Catalog(Container):
    @classmethod
    @override
    def get_type(cls) -> str:
        return CATALOG_TYPE

    def __init__(
        self,
        id: str,
        description: str,
        title: str | None = None,
        stac_extensions: list[str] | None = None,
        # TODO allow extra fields here for backwards compatibility
        stac_version: str | None = None,
        links: list[Link | dict[str, Any]] | None = None,
        **kwargs: Any,
    ):
        self.description: str = description
        self.title: str | None = title
        super().__init__(id, stac_version, stac_extensions, links, **kwargs)

    @override
    def _to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "type": self.get_type(),
            "stac_version": self.stac_version,
        }
        if self.stac_extensions is not None:
            d["stac_extensions"] = self.stac_extensions
        d["id"] = self.id
        if self.title is not None:
            d["title"] = self.title
        d["description"] = self.description
        d["links"] = [link.to_dict() for link in self.iter_links()]
        d.update(copy.deepcopy(self.extra_fields))
        return d
