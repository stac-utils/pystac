from pathlib import Path

from .deserialize import from_dict
from .reader import DEFAULT_READER, Reader
from .stac_object import STACObject


def read_file(href: str | Path, reader: Reader = DEFAULT_READER) -> STACObject:
    data = reader.get_json(href)
    obj = from_dict(data)
    if obj.get_self_href() is None:
        obj.set_self_href(str(href))
    return obj
