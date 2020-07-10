import json

from pystac import (STACError, STAC_VERSION)
from pystac.stac_io import STAC_IO
from pystac.item import Item
from pystac.link import Link
from pystac.stac_object import LinkMixin


class ItemCollection(LinkMixin):
    """A GeoJSON `FeatureCollection <https://tools.ietf.org/html/rfc7946#section-3.3>`_ that
    is augmented with foreign members relevant to a STAC entity.

    Args:
        features (List[Item]): Optional initial list of items contained by this ItemCollection.
        stac_extensions (List[str]): Optional list of extensions implemented.

    Attributes:
        features (List[Item]): Items contained by this ItemCollection
        links (List[Link]): A list of :class:`~pystac.Link` objects representing
            all links associated with this ItemCollection.
    """
    def __init__(self, features=None, stac_extensions=None):
        if features is None:
            self.features = []
        else:
            self.features = features

        self.stac_extensions = stac_extensions

        self.links = []

    def __repr__(self):
        return '<ItemCollection with {} items>'.format(len(self.features))

    @staticmethod
    def from_dict(d):
        """Constructs an ItemCollection from a dict.

        Returns:
            ItemCollection: The ItemCollection deserialized from the JSON dict.
        """
        features = [Item.from_dict(feature) for feature in d['features']]
        stac_extensions = d.get('stac_extensions')

        ic = ItemCollection(features=features, stac_extensions=stac_extensions)

        if 'links' in d.keys():
            for link in d['links']:
                ic.add_link(Link.from_dict(link))
        return ic

    @staticmethod
    def from_file(href):
        """Reads an ItemCollection from a file.

        Args:
            href (str): The HREF to read the item from.

        Returns:
            ItemCollection: ItemCollection that was read from the given file.
        """
        d = json.loads(STAC_IO.read_text(href))
        c = ItemCollection.from_dict(d)
        return c

    def to_dict(self, include_self_link=False):
        """Generate a dictionary representing the JSON of this ItemCollection.

        Args:
            include_self_link (bool): If True, writes the ItemCollection's self link.
                Defaults to False.

        Returns:
            dict: A serializion of the ItemCollection that can be written out as JSON.
        """
        links = self.links
        if not include_self_link:
            links = filter(lambda l: l.rel != 'self', links)

        d = {
            'type': 'FeatureCollection',
            'stac_version': STAC_VERSION,
            'features': [f.to_dict() for f in self.features],
            'links': [link.to_dict() for link in links]
        }

        if self.stac_extensions is not None:
            d['stac_extensions'] = self.stac_extensions

        return d

    def get_items(self):
        """Gets all the items associated with this ItemCollection.

        Returns:
            List[Item]: The Items of this ItemCollection
        """
        return self.features

    def add_item(self, item):
        """Adds an Item to this ItemCollection.

        Args:
            item (Item): The item to add.
        """
        self.features.append(item)

    def add_items(self, items):
        """Adds Items to this ItemCollection.

        Args:
            items (Iterable[Item]): The items to add.
        """
        for item in items:
            self.add_item(item)

    def save(self, href=None, include_self_link=True):
        """Saves this ItemCollection.

        Args:
            href (str): The HREF to save the ItemCollection to. If None,
                will save to the currently set ``self`` link.
                If supplied, will set this href to the ItemCollection's self link.
            include_self_link (bool): If True, will include the self link
                in the set of links of the saved JSON.
        """
        if href is None:
            href = self.get_self_href()
            if href is None:
                raise STACError('Must either supply an href or set a self href on '
                                'this ItemCollection.')
        else:
            self.set_self_href(href)

        STAC_IO.save_json(href, self.to_dict(include_self_link=include_self_link))
