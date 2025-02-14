from typing import Any, Protocol


class Extendable(Protocol):
    stac_extensions: list[str] | None

    def get_fields(self) -> dict[str, Any]: ...
