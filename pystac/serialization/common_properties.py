from pystac import Collection
from pystac.utils import make_absolute_href
from pystac.stac_io import STAC_IO
from pystac.serialization.identify import STACVersionID


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
    collection_id = None
    collection_href = None

    stac_version = item_dict.get('stac_version')

    # The commons extension was removed in 1.0.0-beta.1, so if this is an earlier STAC
    # item we don't have to bother with merging.
    if stac_version is not None and STACVersionID(stac_version) > '0.9.0':
        return False

    # Check to see if this is a 0.9.0 item that
    # doesn't extend the commons extension, in which case
    # we don't have to merge.
    if stac_version is not None and stac_version == '0.9.0':
        stac_extensions = item_dict.get('stac_extensions')
        if type(stac_extensions) is list:
            if 'commons' not in stac_extensions:
                return False
        else:
            return False

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

        collection_link = next((link for link in links if link['rel'] == 'collection'), None)
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
        elif type(collection) is dict:
            collection_id = collection['id']
            if 'properties' in collection:
                collection_props = collection['properties']
        else:
            raise ValueError('{} is expected to be a Collection or '
                             'dict but is neither.'.format(collection))

        if collection_props is not None:
            for k in collection_props:
                if k not in item_dict['properties']:
                    properties_merged = True
                    item_dict['properties'][k] = collection_props[k]

        if collection_cache is not None and not collection_cache.contains_id(collection_id):
            collection_cache.cache(collection, href=collection_href)

    return properties_merged
