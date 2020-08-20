import pystac
from pystac import Extensions
from pystac.extensions.base import (ExtendedObject, ExtensionDefinition, ItemExtension)
from pystac.item import Item
from pystac.utils import datetime_to_str, str_to_datetime


class TimestampsItemExt(ItemExtension):
    """TimestampsItemExt is the extension of an Item in that
    allows to specify additional timestamps for assets and metadata.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The Item that is being extended.

    Note:
        Using TimestampsItemExt to directly wrap an item will add the 'timestamps'
        extension ID to the item's stac_extensions.
    """
    def __init__(self, item):
        if item.stac_extensions is None:
            item.stac_extensions = [Extensions.TIMESTAMPS]
        elif Extensions.TIMESTAMPS not in item.stac_extensions:
            item.stac_extensions.append(Extensions.TIMESTAMPS)

        self.item = item

    @classmethod
    def from_item(cls, item):
        return cls(item)

    @classmethod
    def _object_links(cls):
        return []

    def apply(self, published=None, expires=None, unpublished=None):
        """Applies timestamps extension properties to the extended Item.

        Args:
            published (datetime or None): Date and time the corresponding data
                was published the first time.
            expires (datetime or None): Date and time the corresponding data
                expires (is not valid any longer).
            unpublished (datetime or None): Date and time the corresponding data
                was unpublished.
        """
        if published is None and expires is None and unpublished is None:
            raise pystac.STACError("timestamps extension needs at least one property value.")

        self.published = published
        self.expires = expires
        self.unpublished = unpublished

    def _timestamp_getter(self, key, asset=None):
        if asset is not None and key in asset.properties:
            timestamp_str = asset.properties.get(key)
        else:
            timestamp_str = self.item.properties.get(key)

        timestamp = None
        if timestamp_str is not None:
            timestamp = str_to_datetime(timestamp_str)

        return timestamp

    def _timestamp_setter(self, timestamp, key, asset=None):
        if timestamp is None:
            self.item.properties[key] = timestamp
        else:
            timestamp_str = datetime_to_str(timestamp)
            if asset is not None:
                asset.properties[key] = timestamp_str
            else:
                self.item.properties[key] = timestamp_str

    @property
    def published(self):
        """Get or sets a datetime objects that represent
            the date and time that the corresponding data
            was published the first time.

        Returns:
            datetime
        """
        return self.get_published()

    @published.setter
    def published(self, v):
        self.set_published(v)

    def get_published(self, asset=None):
        """Get an Item or Asset published datetime

        If an Asset is supplied and the published property exists on the Asset,
        return the Asset's value. Otherwise return the Item's value. 'Published'
        has a different meaning depending on where it is used. If available in
        the asset properties, it refers to the timestamps valid for the actual data linked
        to the Asset Object. If it comes from the Item properties, it's referencing to
        the timestamp valid for the metadata.

        Returns:
            datetime
        """
        return self._timestamp_getter('published', asset)

    def set_published(self, published, asset=None):
        """Set an Item or asset published datetime

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        self._timestamp_setter(published, 'published', asset)

    @property
    def expires(self):
        """Get or sets a datetime objects that represent
            the date and time the corresponding data
            expires (is not valid any longer).

        Returns:
            datetime
        """
        return self.get_expires()

    @expires.setter
    def expires(self, v):
        self.set_expires(v)

    def get_expires(self, asset=None):
        """Get an Item or Asset expires datetime

        If an Asset is supplied and the expires property exists on the Asset,
        return the Asset's value. Otherwise return the Item's value. 'Unpublished'
        has a different meaning depending on where it is used. If available in
        the asset properties, it refers to the timestamps valid for the actual data linked
        to the Asset Object. If it comes from the Item properties, it's referencing to
        the timestamp valid for the metadata.

        Returns:
            datetime
        """
        return self._timestamp_getter('expires', asset)

    def set_expires(self, expires, asset=None):
        """Set an Item or asset expires datetime

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        self._timestamp_setter(expires, 'expires', asset)

    @property
    def unpublished(self):
        """Get or sets a datetime objects that represent
        the Date and time the corresponding data was unpublished.

        Returns:
            datetime
        """
        return self.get_unpublished()

    @unpublished.setter
    def unpublished(self, v):
        self.set_unpublished(v)

    def get_unpublished(self, asset=None):
        """Get an Item or Asset unpublished datetime

        If an Asset is supplied and the unpublished property exists on the Asset,
        return the Asset's value. Otherwise return the Item's value. 'Unpublished'
        has a different meaning depending on where it is used. If available in
        the asset properties, it refers to the timestamps valid for the actual data linked
        to the Asset Object. If it comes from the Item properties, it's referencing to
        the timestamp valid for the metadata.

        Returns:
            datetime
        """
        return self._timestamp_getter('unpublished', asset)

    def set_unpublished(self, unpublished, asset=None):
        """Set an Item or asset unpublished datetime

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        self._timestamp_setter(unpublished, 'unpublished', asset)


TIMESTAMPS_EXTENSION_DEFINITION = ExtensionDefinition(Extensions.TIMESTAMPS,
                                                      [ExtendedObject(Item, TimestampsItemExt)])
