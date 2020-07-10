from pystac import Extensions
from pystac.item import (Collection, Item)
from pystac.extensions.base import (CollectionExtension, ItemExtension, ExtensionDefinition,
                                    ExtendedObject)

# NOTE: The commons will be removed in 1.0


class CommonsItemExt(ItemExtension):
    """CommonsItemExt is the extension of the Item for the Commons extension.
    Unlike other extensions the Commons extension does not add any fields to a STAC Item,
    instead it allows one to move fields out of Item and into the parent STAC Collection,
    from which any member Item will inherit. Any field under an Items properties field can
    be removed and added to the Collection properties field. Since a Collection contains no
    properties itself, anything under properties are metadata fields that are common across
    all member Items.

    This class does not provide any additional functionality; the functionality for merging
    commons metadata is part of the serialization code in PySTAC.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The Item that is being extended.
    """
    def __init__(self, item):
        if item.stac_extensions is None:
            item.stac_extensions = [Extensions.COMMONS]
        elif Extensions.COMMONS not in item.stac_extensions:
            item.stac_extensions.append(Extensions.COMMONS)

        self.item = item

    @classmethod
    def _object_links(cls):
        return []

    @classmethod
    def from_item(cls, item):
        return cls(item)


class CommonsCollectionExt(CollectionExtension):
    """CommonsCollectionExt is the extension of the Collection for the Commons extension.
    Unlike other extensions the Commons extension does not add any fields to a STAC Collection,
    instead it allows one to move fields out of Collection and into the parent STAC Collection,
    from which any member Collection will inherit. Any field under an Collections properties
    field can be removed and added to the Collection properties field. Since a Collection
    contains no properties itself, anything under properties are metadata fields that are
    common across all member Collections.

    This class does not provide any additional functionality; the functionality for merging
    commons metadata is part of the serialization code in PySTAC.

    Args:
        collection (Collection): The collection to be extended.

    Attributes:
        collection (Collection): The Collection that is being extended.
    """
    def __init__(self, collection):
        if collection.stac_extensions is None:
            collection.stac_extensions = [Extensions.COMMONS]
        elif Extensions.COMMONS not in collection.stac_extensions:
            collection.stac_extensions.append(Extensions.COMMONS)

        self.collection = collection

    @classmethod
    def _object_links(cls):
        return []

    @classmethod
    def from_collection(cls, collection):
        return cls(collection)


COMMONS_EXTENSION_DEFINITION = ExtensionDefinition(
    Extensions.COMMONS,
    [ExtendedObject(Item, CommonsItemExt),
     ExtendedObject(Collection, CommonsCollectionExt)])
