from pystac.utils import make_absolute_href
from pystac.stac_io import STAC_IO


def merge_common_properties(item_dict, collection_cache=None, json_href=None):
    """Merges Collection properties into an Item.

    Args:
        item_dict: JSON dict of the Item which properties should be merged
            into.
        collection_cache: Optional cache of Collection JSON that has previously
            read. Keyed to either the Collection ID or an HREF.
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
            collection = collection_cache.get(collection_id)

    # Next, try the collection link.
    if collection is None:
        links = item_dict['links']
        collection_link = next((l for l in links if l['rel'] == 'collection'),
                               None)
        if collection_link is not None:
            collection_href = collection_link['href']
            if json_href is not None:
                collection_href = make_absolute_href(collection_href,
                                                     json_href)
            if collection_cache is not None:
                collection = collection_cache.get(collection_href)

            if collection is None:
                collection = STAC_IO.read_json(collection_href)

    if collection is not None:
        if 'properties' in collection:
            for k in collection['properties']:
                if k not in item_dict['properties']:
                    properties_merged = True
                    item_dict['properties'][k] = collection['properties'][k]

        if collection_cache is not None and collection[
                'id'] not in collection_cache:
            collection_id = collection['id']
            collection_cache[collection_id] = collection
            if collection_href is not None:
                collection_cache[collection_href] = collection

    return properties_merged
