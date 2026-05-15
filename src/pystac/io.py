from pathlib import Path

from .deserialize import from_dict
from .reader import Reader, get_default_reader
from .stac_object import STACObject


def read_file(href: str | Path, reader: Reader | None = None) -> STACObject:
    if reader is None:
        reader = get_default_reader()
    data = reader.get_json(href)
    obj = from_dict(data)
    obj.reader = reader
    obj.set_self_href(str(href))
    return obj
