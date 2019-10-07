from collections import ChainMap
from copy import (copy, deepcopy)

class ResolvedObjectCache:
    """This class tracks resolved objects tied to root catalogs.
    A STAC object is 'resolved' when it is a Python Object; a link
    to a STAC object such as a Catalog or Item is considered "unresolved"
    if it's target is pointed at an HREF of the object.

    Tracking resolved objects allows us to tie together the same instances
    when there are loops in the Graph of the STAC catalog (e.g. a LabelItem
    can link to a rel:source, and if that STAC Item exists in the same
    root catalog they should refer to the same Python object).

    Resolution tracking is important when copying STACs in-memory: In order
    for object links to refer to the copy of STAC Objects rather than their
    originals, we have to keep track of the resolved STAC Objects and replace
    them with their copies.
    """
    def __init__(self, ids_to_objects=None):
        self.ids_to_objects = ids_to_objects or {}

    def get_or_set(self, obj):
        if obj.id in self.ids_to_objects:
            return self.ids_to_objects[obj.id]
        else:
            self.ids_to_objects[obj.id] = obj
            return obj

    def get(self, obj):
        return self.ids_to_objects.get(obj.id)

    def set(self, obj):
        self.ids_to_objects[obj.id] = obj

    def clone(self):
        return ResolvedObjectCache(copy(self.ids_to_objects))

    def __contains__(self, obj):
        return obj.id in self.ids_to_objects

    @staticmethod
    def merge(first, second):
        return ResolvedObjectCache(dict(ChainMap(copy(first.ids_to_objects),
                                                 copy(second.ids_to_objects))))
