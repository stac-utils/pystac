from pathlib import Path
from typing import Any

from pystac.reader import Reader, StandardLibraryReader
from pystac.writer import StandardLibraryWriter, Writer


class MockReader(Reader):
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.reader = StandardLibraryReader()

    def get_json(self, href: str | Path) -> dict[str, Any]:
        self.calls.append(str(href))
        return self.reader.get_json(href)


class MockWriter(Writer):
    def __init__(self) -> None:
        self.calls: list[tuple[dict[str, Any], str | Path]] = []
        self.writer = StandardLibraryWriter()

    def put_json(self, data: dict[str, Any], href: str | Path) -> None:
        self.calls.append((data, href))
        self.writer.put_json(data, href)

    def delete(self, href: str | Path) -> None:
        self.writer.delete(href)
