import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Protocol
from urllib.request import Request

from .utils import get_user_agent


class Reader(Protocol):
    def get_json(self, href: str | Path) -> dict[str, Any]: ...


class StandardLibraryReader:
    def get_json(self, href: str | Path) -> dict[str, Any]:
        if isinstance(href, Path):
            with open(href) as f:
                return json.load(f)
        parsed_url = urllib.parse.urlparse(href)
        if parsed_url.scheme in ["http", "https"]:
            request = Request(href, headers={"User-Agent": get_user_agent()})
            with urllib.request.urlopen(request) as f:
                return json.load(f)
        elif not parsed_url.scheme:
            with open(href) as f:
                return json.load(f)
        else:
            raise ValueError(f"Unsupported scheme: {parsed_url.scheme} for {href}")


def set_default_reader(reader: Reader) -> None:
    global DEFAULT_READER
    DEFAULT_READER = reader  # pyright: ignore[reportConstantRedefinition]


DEFAULT_READER = StandardLibraryReader()
