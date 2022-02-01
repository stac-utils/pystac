import os
from typing import Any, Dict, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from pystac.item import Item as Item_Type

HREF = Union[str, os.PathLike]

ItemLike = Union["Item_Type", Dict[str, Any]]
