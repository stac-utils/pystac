from collections import ChainMap
from copy import copy

import pystac


def get_cache_key(stac_object):
    """Produce a cache key for the given STAC object.

    If a self href is set, use that as the cache key.
    If not, use a key that combines this object's ID with
    it's parents' IDs.

    Returns:
        Tuple[str, bool]: A tuple with the cache key as the first
            element and a boolean that is true if the cache key is
            the object's HREF as the second element.
    """
    href = stac_object.get_self_href()
    if href is not None:
        return (href, True)
    else:
        ids = []
        obj = stac_object
        while obj is not None:
            ids.append(obj.id)
            obj = obj.get_parent()
        return ('/'.join(ids), False)


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
        id_keys_to_objects (Dict[str, STACObject]): Existing cache of
            a key made up of the STACObject and it's parents IDs mapped
            to the cached STACObject.
        hrefs_to_objects (Dict[str, STACObject]): STAC Object HREFs matched to
            their cached object.
        ids_to_collections (Dict[str, Collection]): Map of collection IDs to collections.
    """
    def __init__(self, id_keys_to_objects=None, hrefs_to_objects=None, ids_to_collections=None):
        self.id_keys_to_objects = id_keys_to_objects or {}
        self.hrefs_to_objects = hrefs_to_objects or {}
        self.ids_to_collections = ids_to_collections or {}

        self._collection_cache = None

    def get_or_cache(self, obj):
        """Gets the STACObject that is the cached version of the given STACObject; or, if
        none exists, sets the cached object to the given object.

        Args:
            obj (STACObject): The given object who's cache key will be checked
                against the cache.

        Returns:
            STACObject: Either the cached object that has the same cache key as the given
            object, or the given object.
        """
        key, is_href = get_cache_key(obj)
        if is_href:
            if key in self.hrefs_to_objects:
                return self.hrefs_to_objects[key]
            else:
                self.cache(obj)
                return obj
        else:
            if key in self.id_keys_to_objects:
                return self.id_keys_to_objects[key]
            else:
                self.cache(obj)
                return obj

    def get(self, obj):
        """Get the cached object that has the same cache key as the given object.

        Args:
            obj (STACObject): The given object who's cache key will be checked against the cache.

        Returns:
            STACObject or None: Either the cached object that has the same cache key as the given
            object, or None
        """
        key, is_href = get_cache_key(obj)
        if is_href:
            return self.get_by_href(key)
        else:
            return self.id_keys_to_objects.get(key)

    def get_by_href(self, href):
        """Gets the cached object at href.

        Args:
            href (str): The href to use as the key for the cached object.

        Returns:
            STACObject or None: Returns the STACObject if cached, otherwise None.
        """
        return self.hrefs_to_objects.get(href)

    def get_collection_by_id(self, id):
        """Retrieved a cached Collection by its ID.

        Args:
            id (str): The ID of the collection.

        Returns:
            Collection or None: Returns the collection if there is one cached
                with the given ID, otherwise None.
        """
        return self.ids_to_collections.get(id)

    def cache(self, obj):
        """Set the given object into the cache.

        Args:
            obj (STACObject): The object to cache
        """
        key, is_href = get_cache_key(obj)
        if is_href:
            self.hrefs_to_objects[key] = obj
        else:
            self.id_keys_to_objects[key] = obj

        if obj.STAC_OBJECT_TYPE == pystac.STACObjectType.COLLECTION:
            self.ids_to_collections[obj.id] = obj

    def remove(self, obj):
        """Removes any cached object that matches the given object's cache key.

        Args:
            obj (STACObject): The object to remove
        """
        key, is_href = get_cache_key(obj)

        if is_href:
            self.hrefs_to_objects.pop(key, None)
        else:
            self.id_keys_to_objects.pop(key, None)

        if obj.STAC_OBJECT_TYPE == pystac.STACObjectType.COLLECTION:
            self.id_keys_to_objects.pop(obj.id, None)

    def __contains__(self, obj):
        key, is_href = get_cache_key(obj)
        return key in self.hrefs_to_objects if is_href else key in self.id_keys_to_objects

    def contains_collection_id(self, collection_id):
        """Returns True if there is a collection with given collection ID is cached."""
        return collection_id in self.ids_to_collections

    def as_collection_cache(self):
        if self._collection_cache is None:
            self._collection_cache = ResolvedObjectCollectionCache(self)
        return self._collection_cache

    @staticmethod
    def merge(first, second):
        """Merges two ResolvedObjectCache.

        The merged cache will give preference to the first argument; that is, if there
        are cached keys that exist in both the first and second cache, the object cached
        in the first will be cached in the resulting merged ResolvedObjectCache.

        Args:
            first (ResolvedObjectCache): The first cache to merge. This cache will be
                the preferred cache for objects in the case of ID conflicts.
            second (ResolvedObjectCache): The second cache to merge.

        Returns:
            ResolvedObjectCache: The resulting merged cache.
        """
        merged = ResolvedObjectCache(id_keys_to_objects=dict(
            ChainMap(copy(first.id_keys_to_objects), copy(second.id_keys_to_objects))),
                                     hrefs_to_objects=dict(
                                         ChainMap(copy(first.hrefs_to_objects),
                                                  copy(second.hrefs_to_objects))),
                                     ids_to_collections=dict(
                                         ChainMap(copy(first.ids_to_collections),
                                                  copy(second.ids_to_collections))))

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
        result = self.resolved_object_cache.get_collection_by_id(collection_id)
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
        return (self.resolved_object_cache.contains_collection_id(collection_id)
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
