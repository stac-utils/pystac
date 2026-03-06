from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class GeoInterface(Protocol):
    @property
    def __geo_interface__(self) -> dict[str, Any]: ...
