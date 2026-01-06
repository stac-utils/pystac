from typing import Any, Protocol


class Extendable(Protocol):
    def get_fields(self) -> dict[str, Any]: ...
