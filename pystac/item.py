import os
from copy import copy, deepcopy
from collections import ChainMap

import dateutil.parser

from pystac import (STAC_VERSION, STACError)
from pystac.link import Link, LinkType
from pystac.stac_object import STACObject
from pystac.utils import (is_absolute_href, make_absolute_href,
                          make_relative_href, datetime_to_str)
from pystac.collection import Collection


class Item(STACObject):
    """An Item is the core granular entity in a STAC, containing the core metadata
    that enables any client to search or crawl online catalogs of spatial 'assets' -
    satellite imagery, derived data, DEM's, etc.

    Args:
        id (str): Provider identifier. Must be unique within the STAC.
        geometry (dict): Defines the full footprint of the asset represented by this item,
            formatted according to `RFC 7946, section 3.1 (GeoJSON)
            <https://tools.ietf.org/html/rfc7946>`_.
        bbox (List[float]):  Bounding Box of the asset represented by this item using
            either 2D or 3D geometries. The length of the array must be 2*n where n is the
            number of dimensions.
        datetime (Datetime): Datetime associated with this item.
        properties (dict): A dictionary of additional metadata for the item.
        stac_extensions (List[str]): Optional list of extensions the Item implements.
        href (str or None): Optional HREF for this item, which be set as the item's
            self link's HREF.
        collection (Collection or str): The Collection or Collection ID that this item
            belongs to.

    Attributes:
        id (str): Provider identifier. Unique within the STAC.
        geometry (dict): Defines the full footprint of the asset represented by this item,
            formatted according to `RFC 7946, section 3.1 (GeoJSON)
            <https://tools.ietf.org/html/rfc7946>`_.
        bbox (List[float]):  Bounding Box of the asset represented by this item using
            either 2D or 3D geometries. The length of the array is 2*n where n is the
            number of dimensions.
        datetime (Datetime): Datetime associated with this item.
        properties (dict): A dictionary of additional metadata for the item.
        stac_extensions (List[str] or None): Optional list of extensions the Item implements.
        collection (Collection or None): Collection that this item is a part of.
        links (List[Link]): A list of :class:`~pystac.Link` objects representing
            all links associated with this STACObject.
        assets (Dict[str, Asset]): Dictionary of asset objects that can be downloaded,
            each with a unique key.
        collection_id (str or None): The Collection ID that this item belongs to, if any.
    """
    def __init__(self,
                 id,
                 geometry,
                 bbox,
                 datetime,
                 properties,
                 stac_extensions=None,
                 href=None,
                 collection=None):
        self.id = id
        self.geometry = geometry
        self.bbox = bbox
        self.datetime = datetime
        self.properties = properties
        self.stac_extensions = stac_extensions

        self.links = []
        self.assets = {}

        if href is not None:
            self.set_self_href(href)

        if collection is not None:
            if isinstance(collection, Collection):
                self.set_collection(collection)
            else:
                self.collection_id = collection
        else:
            self.collection_id = None

    def __repr__(self):
        return '<Item id={}>'.format(self.id)

    def get_assets(self):
        """Get this item's assets.

        Returns:
            Dict[str, Asset]: A copy of the dictonary of this item's assets.
        """
        return dict(self.assets.items())

    def add_asset(self, key, asset):
        """Adds an Asset to this item.

        Args:
            key (str): The unique key of this asset.
            asset (Asset): The Asset to add.
        """
        asset.set_owner(self)
        self.assets[key] = asset
        return self

    def make_asset_hrefs_relative(self):
        """Modify each asset's HREF to be relative to this item's self HREF.

        Returns:
            Item: self
        """
        self_href = self.get_self_href()
        if self_href is None:
            raise STACError(
                'Cannot make asset HREFs relative if no self_href is set.')
        for asset in self.assets.values():
            asset.href = make_relative_href(asset.href, self_href)
        return self

    def make_asset_hrefs_absolute(self):
        """Modify each asset's HREF to be absolute.

        Any asset HREFs that are relative will be modified to absolute based on this
        item's self HREF.

        Returns:
            Item: self
        """
        self_href = None
        for asset in self.assets.values():
            href = asset.href
            if not is_absolute_href(href):
                if self_href is None:
                    self_href = self.get_self_href()
                    if self_href is None:
                        raise STACError(
                            'Cannot make relative asset HREFs absolute '
                            'if no self_href is set.')
                asset.href = make_absolute_href(asset.href, self_href)

        return self

    def set_collection(self, collection, link_type=None):
        """Set the collection of this item.

        This method will replace any existing Collection link and attribute for
        this item.

        Args:
            collection (Collection): The collection to set as this item's collection.
            link_type (str): the link type to use for the collection link.
                One of :class:`~pystac.LinkType`.

        Returns:
            Item: self
        """
        if not link_type:
            prev = self.get_single_link('collection')
            if prev is not None:
                link_type = prev.link_type
            else:
                link_type = LinkType.ABSOLUTE
        self.remove_links('collection')
        self.add_link(Link.collection(collection, link_type=link_type))
        self.collection_id = collection.id
        return self

    def to_dict(self, include_self_link=True):
        links = self.links
        if not include_self_link:
            links = filter(lambda x: x.rel != 'self', links)

        assets = dict(
            map(lambda x: (x[0], x[1].to_dict()), self.assets.items()))

        self.properties['datetime'] = datetime_to_str(self.datetime)

        d = {
            'type': 'Feature',
            'stac_version': STAC_VERSION,
            'id': self.id,
            'properties': self.properties,
            'geometry': self.geometry,
            'bbox': self.bbox,
            'links': [l.to_dict() for l in links],
            'assets': assets
        }

        if self.stac_extensions is not None:
            d['stac_extensions'] = self.stac_extensions

        if self.collection_id:
            d['collection'] = self.collection_id

        return deepcopy(d)

    def clone(self):
        clone = Item(id=self.id,
                     geometry=deepcopy(self.geometry),
                     bbox=copy(self.bbox),
                     datetime=copy(self.datetime),
                     properties=deepcopy(self.properties),
                     stac_extensions=deepcopy(self.stac_extensions))
        for link in self.links:
            clone.add_link(link.clone())

        clone.assets = dict([(k, a.clone()) for (k, a) in self.assets.items()])

        return clone

    def _object_links(self):
        return ['collection']

    def normalize_hrefs(self, root_href):
        if not is_absolute_href(root_href):
            root_href = make_absolute_href(root_href,
                                           os.getcwd(),
                                           start_is_dir=True)

        old_self_href = self.get_self_href()
        new_self_href = os.path.join(root_href, '{}.json'.format(self.id))
        self.set_self_href(new_self_href)

        # Make sure relative asset links remain valid.
        # This will only work if there is a self href set.
        for asset in self.assets.values():
            asset_href = asset.href
            if not is_absolute_href(asset_href):
                if old_self_href is not None:
                    abs_href = make_absolute_href(asset_href, old_self_href)
                    new_relative_href = make_relative_href(
                        abs_href, new_self_href)
                    asset.href = new_relative_href

    @classmethod
    def from_dict(cls, d, href=None, root=None):
        id = d['id']
        geometry = d['geometry']
        bbox = d['bbox']
        properties = d['properties']
        stac_extensions = d.get('stac_extensions')
        collection_id = None
        if 'collection' in d.keys():
            collection_id = d['collection']

        datetime = properties.get('datetime')
        if datetime is None:
            raise STACError(
                'Item dict is missing a "datetime" property in the "properties" field'
            )
        datetime = dateutil.parser.parse(datetime)

        item = Item(id=id,
                    geometry=geometry,
                    bbox=bbox,
                    datetime=datetime,
                    properties=properties,
                    stac_extensions=stac_extensions,
                    collection=collection_id)

        for l in d['links']:
            item.add_link(Link.from_dict(l))

        for k, v in d['assets'].items():
            asset = Asset.from_dict(v)
            asset.set_owner(item)
            item.assets[k] = asset

        # Find the collection, merge properties if there are
        # common properties to merge.
        collection_to_merge = None
        if collection_id is not None and root is not None:
            collection_to_merge = root._resolved_objects.get_by_id(
                collection_id)
        else:
            collection_link = item.get_single_link('collection')
            if collection_link is not None:
                # If there's a relative collection link, and we have an href passed
                # in, we can resolve the collection from the link. If not,
                # we'll skip merging in collection properties.
                if collection_link.link_type == LinkType.RELATIVE and \
                   not collection_link.is_resolved():
                    if href is not None:
                        collection_link = collection_link.clone()
                        collection_link.target = make_absolute_href(
                            collection_link.target, href)
                    else:
                        collection_link = None

                if collection_link is not None:
                    collection_to_merge = collection_link.resolve_stac_object(
                        root=root).target
                    if item.collection_id is None:
                        item.collection_id = collection_to_merge.id

        if collection_to_merge is not None:
            if collection_to_merge.properties is not None:
                item.properties = dict(
                    ChainMap(item.properties, collection_to_merge.properties))

        return item


class Asset:
    """An object that contains a link to data associated with the Item that can be
    downloaded or streamed.

    Args:
        href (str): Link to the asset object. Relative and absolute links are both allowed.
        title (str): Optional displayed title for clients and users.
        media_type (str): Optional description of the media type. Registered Media Types
            are preferred. See :class:`~pystac.MediaType` for common media types.
        properties (dict): Optional, additional properties for this asset. This is used by
            extensions as a way to serialize and deserialize properties on asset
            object JSON.

    Attributes:
        href (str): Link to the asset object. Relative and absolute links are both allowed.
        title (str): Optional displayed title for clients and users.
        media_type (str): Optional description of the media type. Registered Media Types
            are preferred. See :class:`~pystac.MediaType` for common media types.
        properties (dict): Optional, additional properties for this asset. This is used by
            extensions as a way to serialize and deserialize properties on asset
            object JSON.
        owner (Item or None): The Item this asset belongs to.
    """
    def __init__(self, href, title=None, media_type=None, properties=None):
        self.href = href
        self.title = title
        self.media_type = media_type
        self.properties = properties

        # The Item which owns this Asset.
        self.owner = None

    def set_owner(self, item):
        """Sets the owning item of this Asset.

        The owning item will be used to resolve relative HREFs of this asset.

        Args:
            item (Item): The Item that owns this asset.
        """
        self.owner = item

    def get_absolute_href(self):
        """Gets the absolute href for this asset, if possible.

        If this Asset has no associated Item, this will return whatever the
        href is (as it cannot determine the absolute path, if the asset
        href is relative).

        Returns:
            str: The absolute HREF of this asset, or a relative HREF is an abslolute HREF
            cannot be determined.
        """
        if not is_absolute_href(self.href):
            if self.owner is not None:
                return make_absolute_href(self.href,
                                          self.owner.get_self_href())

        return self.href

    def to_dict(self):
        """Generate a dictionary representing the JSON of this Asset.

        Returns:
            dict: A serializion of the Asset that can be written out as JSON.
        """

        d = {'href': self.href}

        if self.media_type is not None:
            d['type'] = self.media_type

        if self.title is not None:
            d['title'] = self.title

        if self.properties is not None:
            for k, v in self.properties.items():
                d[k] = v

        return deepcopy(d)

    def clone(self):
        """Clones this asset.

        Returns:
            Asset: The clone of this asset.
        """
        return Asset(href=self.href,
                     title=self.title,
                     media_type=self.media_type,
                     properties=self.properties)

    def __repr__(self):
        return '<Asset href={}>'.format(self.href)

    @staticmethod
    def from_dict(d):
        """Constructs an Asset from a dict.

        Returns:
            Asset: The Asset deserialized from the JSON dict.
        """
        d = copy(d)
        href = d.pop('href')
        media_type = d.pop('type', None)
        title = d.pop('title', None)
        properties = None
        if any(d):
            properties = d

        return Asset(href=href,
                     media_type=media_type,
                     title=title,
                     properties=properties)
