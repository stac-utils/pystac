from typing import Any, Protocol

from .constants import STAC_OBJECT_TYPE


class Validator(Protocol):
    def validate_core(
        self, type: STAC_OBJECT_TYPE, version: str, data: dict[str, Any]
    ) -> None: ...

    def validate_extension(self, extension: str, data: dict[str, Any]) -> None: ...
