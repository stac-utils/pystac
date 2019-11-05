from collections import ChainMap
from copy import copy


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

    Args:
        ids_to_objects (Dict[str, STACObject]): Existing cache of STACObject IDs mapped
        to the cached STACObject.
    """
    def __init__(self, ids_to_objects=None):
        self.ids_to_objects = ids_to_objects or {}

    def get_or_cache(self, obj):
        """Gets the STACObject that is the cached version of the given STACObject; or, if
        none exists, sets the cached object to the given object.

        Args:
            obj (STACObject): The given object who's ID will be checked against the cache.

        Returns:
            STACObject: Either the cached object that has the same ID as the given
            object, or the given object.
        """
        if obj.id in self.ids_to_objects:
            return self.ids_to_objects[obj.id]
        else:
            self.ids_to_objects[obj.id] = obj
            return obj

    def get(self, obj):
        """Get the cached object that has the same ID as the given object.

        Args:
            obj (STACObject): The given object who's ID will be checked against the cache.

        Returns:
            STACObject or None: Either the cached object that has the same ID as the given
            object, or None
        """
        return self.get_by_id(obj.id)

    def get_by_id(self, obj_id):
        """Get the cached object that has the given ID.

        Args:
            obj_id (str): The ID to be checked against the cache.

        Returns:
            STACObject or None: Either the cached object that has the given ID, or None
        """

        return self.ids_to_objects.get(obj_id)

    def cache(self, obj):
        """Set the given object into the cache.

        Args:
            obj (STACObject): The object to cache
        """
        self.ids_to_objects[obj.id] = obj

    def remove(self, obj):
        """Removes any cached object that matches the given object's id.

        Args:
            obj (STACObject): The object to remove
        """
        self.remove_by_id(obj.id)

    def remove_by_id(self, obj_id):
        """Removes any cached object that matches the given ID.

        Args:
            obj_id (str): The object ID to remove
        """
        self.ids_to_objects.pop(obj_id, None)

    def clone(self):
        """Clone this ResolvedObjectCache

        Returns:
            ResolvedObjectCache: A clone of this cache, which contains a shallow
            copy of the ID to STACObject cache.
        """
        return ResolvedObjectCache(copy(self.ids_to_objects))

    def __contains__(self, obj):
        return obj.id in self.ids_to_objects

    @staticmethod
    def merge(first, second):
        """Merges two ResolvedObjectCache.

        The merged cache will give preference to the first argument; that is, if there
        are cached IDs that exist in both the first and second cache, the object cached
        in the first will be cached in the resulting merged ResolvedObjectCache.

        Args:
            first (ResolvedObjectCache): The first cache to merge. This cache will be
                the prefered cache for objects in the case of ID conflicts.
            second (ResolvedObjectCache): The second cache to merge.

        Returns:
            ResolvedObjectCache: The resulting merged cache.
        """
        return ResolvedObjectCache(
            dict(
                ChainMap(copy(first.ids_to_objects),
                         copy(second.ids_to_objects))))
