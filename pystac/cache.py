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
        ids_to_hrefs (Dict[str, str]): Cache of STACObject IDs to their HREFs.
        hrefs_to_ids
    """
    def __init__(self, ids_to_objects=None, ids_to_hrefs=None, hrefs_to_ids=None):
        self.ids_to_objects = ids_to_objects or {}
        self.ids_to_hrefs = ids_to_hrefs or {}
        self.hrefs_to_ids = hrefs_to_ids or {}

        self._collection_cache = None

    def _cache_href(self, obj):
        href = obj.get_self_href()
        if href is not None:
            self.ids_to_hrefs[obj.id] = href
            self.hrefs_to_ids[href] = obj.id

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
            self._cache_href(obj)
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

    def get_by_href(self, href):
        obj_id = self.hrefs_to_ids.get(href)
        if obj_id is not None:
            return self.get_by_id(obj_id)
        else:
            return None

    def cache(self, obj):
        """Set the given object into the cache.

        Args:
            obj (STACObject): The object to cache
        """
        self.ids_to_objects[obj.id] = obj
        self._cache_href(obj)

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
        href = self.ids_to_hrefs.pop(obj_id, None)
        if href is not None:
            self.hrefs_to_ids.pop(href, None)

    def clone(self):
        """Clone this ResolvedObjectCache

        Returns:
            ResolvedObjectCache: A clone of this cache, which contains a shallow
            copy of the ID to STACObject cache.
        """
        return ResolvedObjectCache(copy(self.ids_to_objects), copy(self.ids_to_hrefs),
                                   copy(self.hrefs_to_ids))

    def __contains__(self, obj):
        return self.contains_id(obj.id)

    def contains_id(self, obj_id):
        return obj_id in self.ids_to_objects

    def as_collection_cache(self):
        if self._collection_cache is None:
            self._collection_cache = ResolvedObjectCollectionCache(self)
        return self._collection_cache

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
        merged = ResolvedObjectCache(
            ids_to_objects=dict(ChainMap(copy(first.ids_to_objects), copy(second.ids_to_objects))),
            ids_to_hrefs=dict(ChainMap(copy(first.ids_to_hrefs), copy(second.ids_to_hrefs))),
            hrefs_to_ids=dict(ChainMap(copy(first.hrefs_to_ids), copy(second.hrefs_to_ids))))

        merged._collection_cache = ResolvedObjectCollectionCache.merge(
            merged, first._collection_cache, second._collection_cache)

        return merged


class CollectionCache:
    """Cache of collections that can be used to avoid re-reading Collection
    JSON in :func:`pystac.serialization.merge_common_properties
    <pystac.serialization.common_properties.merge_common_properties>`.
    The CollectionCache will contain collections as either as dicts or PySTAC Collections,
    and will set Collection JSON that it reads in order to merge in common properties.
    """
    def __init__(self, cached_ids=None, cached_hrefs=None):
        self.cached_ids = cached_ids or {}
        self.cached_hrefs = cached_hrefs or {}

    def get_by_id(self, collection_id):
        return self.cached_ids.get(collection_id)

    def get_by_href(self, href):
        return self.cached_hrefs.get(href)

    def contains_id(self, collection_id):
        return collection_id in self.cached_ids

    def cache(self, collection, href=None):
        """Caches a collection JSON."""
        self.cached_ids[collection['id']] = collection

        if href is not None:
            self.cached_hrefs[href] = collection


class ResolvedObjectCollectionCache(CollectionCache):
    def __init__(self, resolved_object_cache, cached_ids=None, cached_hrefs=None):
        super().__init__(cached_ids, cached_hrefs)
        self.resolved_object_cache = resolved_object_cache

    def get_by_id(self, collection_id):
        result = self.resolved_object_cache.get_by_id(collection_id)
        if result is None:
            return super().get_by_id(collection_id)
        else:
            return result

    def get_by_href(self, href):
        result = self.resolved_object_cache.get_by_href(href)
        if result is None:
            return super().get_by_href(href)
        else:
            return result

    def contains_id(self, collection_id):
        return (self.resolved_object_cache.contains_id(collection_id)
                or super().contains_id(collection_id))

    def cache(self, collection, href=None):
        super().cache(collection, href)

    @staticmethod
    def merge(resolved_object_cache, first, second):
        first_cached_ids = {}
        if first is not None:
            first_cached_ids = copy(first.cached_ids)

        second_cached_ids = {}
        if second is not None:
            second_cached_ids = copy(second.cached_ids)

        first_cached_hrefs = {}
        if first is not None:
            first_cached_hrefs = copy(first.cached_hrefs)

        second_cached_hrefs = {}
        if second is not None:
            second_cached_hrefs = copy(second.cached_hrefs)

        return ResolvedObjectCollectionCache(
            resolved_object_cache,
            cached_ids=dict(ChainMap(first_cached_ids, second_cached_ids)),
            cached_hrefs=dict(ChainMap(first_cached_hrefs, second_cached_hrefs)))
