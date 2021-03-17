from copy import copy

from pystac.stac_object import STACObject
from pystac import STACError
from pystac.utils import (
    is_absolute_href,
    make_absolute_href,
    make_relative_href
)


class STACObjectWithAssets(STACObject):

    def get_assets(self):
        """Get this object's assets.

        Returns:
            Dict[str, Asset]: A copy of the dictionary of this object's assets.
        """
        return dict(self.assets.items())

    def add_asset(self, key, asset):
        """Adds an Asset to this object.

        Args:
            key (str): The unique key of this asset.
            asset (Asset): The Asset to add.
        """
        asset.set_owner(self)
        self.assets[key] = asset
        return self

    def make_asset_hrefs_relative(self):
        """Modify each asset's HREF to be relative to this object's self HREF.

        Returns:
            STACObjectWithAssets: self
        """

        self_href = None
        for asset in self.assets.values():
            href = asset.href
            if is_absolute_href(href):
                if self_href is None:
                    self_href = self.get_self_href()
                    if self_href is None:
                        raise STACError('Cannot make asset HREFs relative '
                                        'if no self_href is set.')
                asset.href = make_relative_href(asset.href, self_href)
        return self

    def make_asset_hrefs_absolute(self):
        """Modify each asset's HREF to be absolute.

        Any asset HREFs that are relative will be modified to absolute based on this
        object's self HREF.

        Returns:
            STACObjectWithAssets: self
        """
        self_href = None
        for asset in self.assets.values():
            href = asset.href
            if not is_absolute_href(href):
                if self_href is None:
                    self_href = self.get_self_href()
                    if self_href is None:
                        raise STACError('Cannot make relative asset HREFs absolute '
                                        'if no self_href is set.')
                asset.href = make_absolute_href(asset.href, self_href)

        return self

    def set_self_href(self, href):
        """Sets the absolute HREF that is represented by the ``rel == 'self'``
        :class:`~pystac.Link`.

        Changing the self HREF of the item will ensure that all asset HREFs
        remain valid. If asset HREFs are relative, the HREFs will change
        to point to the same location based on the new item self HREF,
        either by making them relative to the new location or making them
        absolute links if the new location does not share the same protocol
        as the old location.

        Args:
            href (str): The absolute HREF of this object. If the given HREF
                is not absolute, it will be transformed to an absolute
                HREF based on the current working directory. If this is None
                the call will clear the self HREF link.
        """
        prev_href = self.get_self_href()
        super().set_self_href(href)
        new_href = self.get_self_href()  # May have been made absolute.

        if prev_href is not None:
            # Make sure relative asset links remain valid.
            for asset in self.assets.values():
                asset_href = asset.href
                if not is_absolute_href(asset_href):
                    abs_href = make_absolute_href(asset_href, prev_href)
                    new_relative_href = make_relative_href(abs_href, new_href)
                    asset.href = new_relative_href


class Asset:
    """An object that contains a link to data associated with the object that can be
    downloaded or streamed.

    Args:
        href (str): Link to the asset object. Relative and absolute links are both allowed.
        title (str): Optional displayed title for clients and users.
        description (str): A description of the Asset providing additional details, such as
            how it was processed or created. CommonMark 0.29 syntax MAY be used for rich
            text representation.
        media_type (str): Optional description of the media type. Registered Media Types
            are preferred. See :class:`~pystac.MediaType` for common media types.
        roles ([str]): Optional, Semantic roles (i.e. thumbnail, overview, data, metadata)
            of the asset.
        properties (dict): Optional, additional properties for this asset. This is used by
            extensions as a way to serialize and deserialize properties on asset
            object JSON.

    Attributes:
        href (str): Link to the asset object. Relative and absolute links are both allowed.
        title (str): Optional displayed title for clients and users.
        description (str): A description of the Asset providing additional details, such as
            how it was processed or created. CommonMark 0.29 syntax MAY be used for rich
            text representation.
        media_type (str): Optional description of the media type. Registered Media Types
            are preferred. See :class:`~pystac.MediaType` for common media types.
        properties (dict): Optional, additional properties for this asset. This is used by
            extensions as a way to serialize and deserialize properties on asset
            object JSON.
        owner (Item or None): The Item this asset belongs to.
    """
    def __init__(self,
                 href,
                 title=None,
                 description=None,
                 media_type=None,
                 roles=None,
                 properties=None):
        self.href = href
        self.title = title
        self.description = description
        self.media_type = media_type
        self.roles = roles

        if properties is not None:
            self.properties = properties
        else:
            self.properties = {}

        # The Item which owns this Asset.
        self.owner = None

    def set_owner(self, element):
        """Sets the owning element of this Asset.

        The owning itelementem will be used to resolve relative HREFs of this asset.

        Args:
            element (STACObjectWithAssets): The Item that owns this asset.
        """
        self.owner = element

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
                return make_absolute_href(self.href, self.owner.get_self_href())

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

        if self.description is not None:
            d['description'] = self.description

        if self.properties is not None and len(self.properties) > 0:
            for k, v in self.properties.items():
                d[k] = v

        if self.roles is not None:
            d['roles'] = self.roles

        return d

    def clone(self):
        """Clones this asset.

        Returns:
            Asset: The clone of this asset.
        """
        return Asset(href=self.href,
                     title=self.title,
                     description=self.description,
                     media_type=self.media_type,
                     roles=self.roles,
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
        description = d.pop('description', None)
        roles = d.pop('roles', None)
        properties = None
        if any(d):
            properties = d

        return Asset(href=href,
                     media_type=media_type,
                     title=title,
                     description=description,
                     roles=roles,
                     properties=properties)
