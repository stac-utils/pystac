from copy import deepcopy

from pystac import STACError
from pystac.extension import Extension
from pystac.collection import Collection
from pystac.item import Item

class DataCube(Item, Collection):
    
    _EXTENSION_FIELDS = ['dimensions']

    