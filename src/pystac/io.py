from pathlib import Path

from .deserialize import from_dict
from .reader import DEFAULT_READER, Reader
from .stac_object import STACObject


def read_file(href: str | Path, reader: Reader = DEFAULT_READER) -> STACObject:
    data = reader.get_json(href)
    return from_dict(data)
