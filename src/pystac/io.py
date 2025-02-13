"""Input and output.

In PySTAC v2.0, reading and writing STAC objects has been split into separate
protocols, [Read][pystac.io.Read] and [Write][pystac.io.Write] classes. This
should be a transparent operation for most users:

```python
catalog = pystac.read_file("catalog.json")
reader = catalog.get_reader()
for child in catalog.get_children():
    # The default reader is shared for all fetched objects.
    assert child.get_reader() is reader
```

Note:
    In PySTAC v1.x, input and output were handled by
    [StacIO](https://pystac.readthedocs.io/en/stable/api/pystac.html#pystac.StacIO).
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Protocol

from .errors import PystacError
from .stac_object import STACObject


def read_file(href: str | Path, reader: Read | None = None) -> STACObject:
    """Reads a file from a href.

    Uses the default [Reader][pystac.DefaultReader].

    Args:
        href: The href to read

    Returns:
        The STAC object

    Examples:
        >>> item = pystac.read_file("item.json")
    """
    return STACObject.from_file(href, reader=reader)


def write_file(
    stac_object: STACObject,
    *,
    href: str | Path | None = None,
    writer: Write | None = None,
) -> None:
    """Writes a STAC object to a file, using its href.

    If the href is not set, this will throw and error.

    Args:
        stac_object: The STAC object to write
    """
    if writer is None:
        writer = DefaultWriter()
    if href is None:
        href = stac_object.href
    if href is None:
        raise PystacError(f"cannot write {stac_object} without an href")
    data = stac_object.to_dict()
    if isinstance(href, Path):
        writer.write_json_to_path(data, href)
    else:
        url = urllib.parse.urlparse(href)
        if url.scheme:
            writer.write_json_to_url(data, href)
        else:
            writer.write_json_to_path(data, Path(href))


def make_absolute_href(href: str, base: str | None) -> str:
    if urllib.parse.urlparse(href).scheme:
        return href  # TODO file:// schemes

    if base:
        if urllib.parse.urlparse(base).scheme:
            raise NotImplementedError("url joins not implemented yet, should be easy")
        else:
            if base.endswith("/"):  # TODO windoze
                return str((Path(base) / href).resolve(strict=False))
            else:
                return str((Path(base).parent / href).resolve(strict=False))
    else:
        raise NotImplementedError


class Read(Protocol):
    """A protocol for anything that can read JSON for pystac."""

    def read_json_from_path(self, path: Path) -> Any:
        """Reads JSON from a path."""

    def read_json_from_url(self, url: str) -> Any:
        """Reads JSON from a url."""


class Write(Protocol):
    """A protocol for anything that can write JSON for pystac."""

    def write_json_to_path(self, data: Any, path: Path) -> None:
        """Writes JSON to a filesystem path."""

    def write_json_to_url(self, data: Any, url: str) -> None:
        """Writes json to a URL."""


class DefaultReader:
    """A reader that uses only the Python standard library."""

    def read_json_from_path(self, path: Path) -> Any:
        """Writes JSON to a filesystem path."""
        with open(path) as f:
            return json.load(f)

    def read_json_from_url(self, url: str) -> Any:
        """Reads JSON from a url using `urllib.request`."""
        with urllib.request.urlopen(url) as response:
            return json.load(response)


class DefaultWriter:
    """A writer."""

    def write_json_to_path(self, data: Any, path: Path) -> None:
        """Writes JSON to a filesystem path.

        Any parent directories will be created.
        """
        path.parent.mkdir(exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)

    def write_json_to_url(self, data: Any, url: str) -> None:
        """Writes JSON to a url.

        Always raises a `NotImplementedError`."""
        raise NotImplementedError(
            "The default pystac writer cannot write to urls. Use another writer, "
            "like `pystac.ObstoreWriter` (enabled by `python -m pip install "
            "'pystac[obstore]'`)"
        )
