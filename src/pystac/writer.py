import json
import urllib.parse
from pathlib import Path
from typing import Any, Protocol


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


def set_default_writer(writer: Writer) -> None:
    global DEFAULT_WRITER
    DEFAULT_WRITER = writer  # pyright: ignore[reportConstantRedefinition]


DEFAULT_WRITER = StandardLibraryWriter()
