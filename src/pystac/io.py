"""Input and output.

In PySTAC v2.0, reading and writing STAC objects has been split into separate
protocols, [Read][pystac.io.Read] and [Write][pystac.io.Write]. This should be
transparent for most users:

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

from . import deprecate
from .errors import PySTACError
from .stac_object import STACObject


def read_file(
    href: str | Path,
    stac_io: Any = None,
    *,
    reader: Read | None = None,
) -> STACObject:
    """Reads a file from a href.

    Args:
        href: The href to read
        reader: The [Read][pystac.Read] to use for reading

    Returns:
        The STAC object
    """
    if stac_io:
        deprecate.argument("stac_io")
    return STACObject.from_file(href, reader=reader)


def write_file(
    obj: STACObject,
    include_self_link: bool | None = None,
    dest_href: str | Path | None = None,
    stac_io: Any = None,
    *,
    writer: Write | None = None,
) -> None:
    """Writes a STAC object to a file, using its href.

    If the href is not set, this will throw and error.

    Args:
        obj: The STAC object to write
        dest_href: The href to write the STAC object to
        writer: The [Write][pystac.Write] to use for writing
    """
    if include_self_link is not None:
        deprecate.argument("include_self_link")
    if stac_io:
        deprecate.argument("stac_io")

    if writer is None:
        writer = DefaultWriter()

    if dest_href is None:
        dest_href = obj.href
    if dest_href is None:
        raise PySTACError(f"cannot write {obj} without an href")
    d = obj.to_dict()
    if isinstance(dest_href, Path):
        writer.write_json_to_path(d, dest_href)
    else:
        url = urllib.parse.urlparse(dest_href)
        if url.scheme:
            writer.write_json_to_url(d, dest_href)
        else:
            writer.write_json_to_path(d, Path(dest_href))


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
