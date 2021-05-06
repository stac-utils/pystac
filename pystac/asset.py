from copy import copy
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union

import pystac
from pystac.utils import is_absolute_href, make_absolute_href

if TYPE_CHECKING:
    from pystac.collection import Collection as Collection_Type
    from pystac.item import Item as Item_Type


class Asset:
    """An object that contains a link to data associated with an Item or Collection that
    can be downloaded or streamed.

    Args:
        href (str): Link to the asset object. Relative and absolute links are both
            allowed.
        title (str): Optional displayed title for clients and users.
        description (str): A description of the Asset providing additional details,
            such as how it was processed or created. CommonMark 0.29 syntax MAY be used
            for rich text representation.
        media_type (str): Optional description of the media type. Registered Media Types
            are preferred. See :class:`~pystac.MediaType` for common media types.
        roles ([str]): Optional, Semantic roles (i.e. thumbnail, overview,
            data, metadata) of the asset.
        properties (dict): Optional, additional properties for this asset. This is used
            by extensions as a way to serialize and deserialize properties on asset
            object JSON.

    Attributes:
        href (str): Link to the asset object. Relative and absolute links are both
            allowed.
        title (str): Optional displayed title for clients and users.
        description (str): A description of the Asset providing additional details,
            such as how it was processed or created. CommonMark 0.29 syntax MAY be
            used for rich text representation.
        media_type (str): Optional description of the media type. Registered Media Types
            are preferred. See :class:`~pystac.MediaType` for common media types.
        properties (dict): Optional, additional properties for this asset. This is used
            by extensions as a way to serialize and deserialize properties on asset
            object JSON.
        owner: The Item or Collection this asset belongs to, or None if it has no owner.
    """

    def __init__(
        self,
        href: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        media_type: Optional[str] = None,
        roles: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
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
        self.owner: Optional[Union[pystac.Item, pystac.Collection]] = None

    def set_owner(self, obj: Union["Collection_Type", "Item_Type"]) -> None:
        """Sets the owning item of this Asset.

        The owning item will be used to resolve relative HREFs of this asset.

        Args:
            obj: The Collection or Item that owns this asset.
        """
        self.owner = obj

    def get_absolute_href(self) -> Optional[str]:
        """Gets the absolute href for this asset, if possible.

        If this Asset has no associated Item, and the asset HREF is a relative path,
            this method will return None.

        Returns:
            str: The absolute HREF of this asset, or None if an absolute HREF could not
                be determined.
        """
        if is_absolute_href(self.href):
            return self.href
        else:
            if self.owner is not None:
                return make_absolute_href(self.href, self.owner.get_self_href())
            else:
                return None

    def to_dict(self) -> Dict[str, Any]:
        """Generate a dictionary representing the JSON of this Asset.

        Returns:
            dict: A serialization of the Asset that can be written out as JSON.
        """

        d: Dict[str, Any] = {"href": self.href}

        if self.media_type is not None:
            d["type"] = self.media_type

        if self.title is not None:
            d["title"] = self.title

        if self.description is not None:
            d["description"] = self.description

        if self.properties is not None and len(self.properties) > 0:
            for k, v in self.properties.items():
                d[k] = v

        if self.roles is not None:
            d["roles"] = self.roles

        return d

    def clone(self) -> "Asset":
        """Clones this asset.

        Returns:
            Asset: The clone of this asset.
        """
        return Asset(
            href=self.href,
            title=self.title,
            description=self.description,
            media_type=self.media_type,
            roles=self.roles,
            properties=self.properties,
        )

    def __repr__(self) -> str:
        return "<Asset href={}>".format(self.href)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Asset":
        """Constructs an Asset from a dict.

        Returns:
            Asset: The Asset deserialized from the JSON dict.
        """
        d = copy(d)
        href = d.pop("href")
        media_type = d.pop("type", None)
        title = d.pop("title", None)
        description = d.pop("description", None)
        roles = d.pop("roles", None)
        properties = None
        if any(d):
            properties = d

        return Asset(
            href=href,
            media_type=media_type,
            title=title,
            description=description,
            roles=roles,
            properties=properties,
        )
