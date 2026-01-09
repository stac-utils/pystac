import json
import urllib.parse
from pathlib import Path
from typing import Any, Protocol

from typing_extensions import deprecated

from pystac.stac_io import StacIO


class Writer(Protocol):
    def put_json(self, data: dict[str, Any], href: str | Path) -> None: ...
    def delete(self, href: str | Path) -> None: ...


class StandardLibraryWriter:
    def put_json(self, data: dict[str, Any], href: str | Path) -> None:
        if isinstance(href, Path) or not urllib.parse.urlparse(href).scheme:
            Path(href).parent.mkdir(parents=True, exist_ok=True)
            with open(href, "w") as f:
                json.dump(
                    data,
                    f,
                )
        else:
            raise ValueError("StandardLibraryWriter cannot write to urls")

    def delete(self, href: str | Path) -> None:
        if isinstance(href, Path) or not urllib.parse.urlparse(href).scheme:
            Path(href).unlink()
        else:
            raise ValueError("StandardLibraryWriter cannot delete urls")


@deprecated("StacIO is deprecated in PySTAC v2")
class StacIOWriter:
    def __init__(self, stac_io: StacIO) -> None:
        self.stac_io: StacIO = stac_io

    def put_json(self, data: dict[str, Any], href: str | Path) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError

    def delete(self, href: str | Path) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError


def set_default_writer(writer: Writer) -> None:
    global DEFAULT_WRITER
    DEFAULT_WRITER = writer  # pyright: ignore[reportConstantRedefinition]


DEFAULT_WRITER = StandardLibraryWriter()
