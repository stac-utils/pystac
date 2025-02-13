"""Read and write with [obstore](https://developmentseed.org/obstore).

Using these classes requires `obstore` to be present on your system, e.g.:

```shell
python -m pip install 'pystac[obstore]'
```
"""

import json
import urllib.parse
from pathlib import Path
from typing import Any

import obstore
import obstore.store
from obstore.store import LocalStore


class ObstoreReader:
    """A reader that uses [obstore](https://github.com/developmentseed/obstore)."""

    def __init__(self, **kwargs: Any) -> None:
        """Creates a new obstore reader.

        Args:
            kwargs: Configuration values. Store-specific configuration is done
                with a prefix, e.g. `aws_` for AWS.  See the [obstore
                docs](https://developmentseed.org/obstore/latest/getting-started/#constructing-a-store)
                for more.
        """
        self._config = kwargs
        super().__init__()

    def read_json_from_path(self, path: Path) -> Any:
        store = LocalStore()
        result = obstore.get(store, str(path))
        return json.loads(bytes(result.bytes()))

    def read_json_from_url(self, url: str) -> Any:
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path
        base = parsed_url._replace(path="")
        store = obstore.store.from_url(
            urllib.parse.urlunparse(base), **self._config
        )  # TODO config
        result = obstore.get(store, path)
        return json.loads(bytes(result.bytes()))  # TODO can we parse directly?
