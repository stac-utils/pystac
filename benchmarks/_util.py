from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    PathLike = os.PathLike[str]


def get_data_path(rel_path: str | PathLike) -> str:
    """Gets the absolute path to a file based on a path relative to the
    tests/data-files directory in this repo."""
    rel_path = os.fspath(rel_path)
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "tests", "data-files", rel_path)
    )
