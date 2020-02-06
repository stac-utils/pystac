from pystac import Collection
from pystac.utils import make_absolute_href
from pystac.stac_io import STAC_IO


def merge_common_properties(item_dict, collection_cache=None, json_href=None):
    """Merges Collection properties into an Item.

    Args:
        item_dict (dict): JSON dict of the Item which properties should be merged
            into.
        collection_cache (CollectionCache): Optional CollectionCache
            that will be used to read and write cached collections.
        json_href: The HREF of the file that this JSON comes from. Used
            to resolve relative paths.

    Returns:
        bool: True if Collection properties have been merged, otherwise False.
    """
    properties_merged = False
    collection = None
    collection_href = None

    # Try the cache if we have a collection ID.
    if 'collection' in item_dict:
        collection_id = item_dict['collection']
        if collection_cache is not None:
            collection = collection_cache.get_by_id(collection_id)

    # Next, try the collection link.
    if collection is None:
        links = item_dict['links']

        # Account for 0.5 links, which were dicts
        if isinstance(links, dict):
            links = list(links.values())

        collection_link = next((l for l in links if l['rel'] == 'collection'), None)
        if collection_link is not None:
            collection_href = collection_link['href']
            if json_href is not None:
                collection_href = make_absolute_href(collection_href, json_href)
            if collection_cache is not None:
                collection = collection_cache.get_by_href(collection_href)

            if collection is None:
                collection = STAC_IO.read_json(collection_href)

    if collection is not None:
        collection_id = None
        collection_props = None
        if isinstance(collection, Collection):
            collection_id = collection.id
            collection_props = collection.properties
        else:
            collection_id = collection['id']
            if 'properties' in collection:
                collection_props = collection['properties']

        if collection_props is not None:
            for k in collection_props:
                if k not in item_dict['properties']:
                    properties_merged = True
                    item_dict['properties'][k] = collection_props[k]

        if collection_cache is not None and not collection_cache.contains_id(collection_id):
            collection_cache.cache(collection, href=collection_href)

    return properties_merged
