import os
from typing import Union

def get_data_path(rel_path: Union[str, os.PathLike]) -> str:
    """Gets the absolute path to a file based on a path relative to the
    tests/data-files directory in this repo."""
    rel_path = os.fspath(rel_path)
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "..", "tests", "data-files", rel_path
        )
    )
