from copy import copy
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from pystac import common_metadata, utils

if TYPE_CHECKING:
    from pystac.common_metadata import CommonMetadata as CommonMetadata_Type
    from pystac.core import Collection as Collection_Type
    from pystac.core import Item as Item_Type


class Asset:
    """An object that contains a link to data associated with an Item or Collection that
    can be downloaded or streamed.

    Args:
        href : Link to the asset object. Relative and absolute links are both
            allowed.
        title : Optional displayed title for clients and users.
        description : A description of the Asset providing additional details,
            such as how it was processed or created. CommonMark 0.29 syntax MAY be used
            for rich text representation.
        media_type : Optional description of the media type. Registered Media Types
            are preferred. See :class:`~pystac.MediaType` for common media types.
        roles : Optional, Semantic roles (i.e. thumbnail, overview,
            data, metadata) of the asset.
        extra_fields : Optional, additional fields for this asset. This is used
            by extensions as a way to serialize and deserialize properties on asset
            object JSON.
    """

    href: str
    """Link to the asset object. Relative and absolute links are both allowed."""

    title: Optional[str]
    """Optional displayed title for clients and users."""

    description: Optional[str]
    """A description of the Asset providing additional details, such as how it was
    processed or created. CommonMark 0.29 syntax MAY be used for rich text
    representation."""

    media_type: Optional[str]
    """Optional description of the media type. Registered Media Types are preferred.
    See :class:`~pystac.MediaType` for common media types."""

    roles: Optional[List[str]]
    """Optional, Semantic roles (i.e. thumbnail, overview, data, metadata) of the
    asset."""

    owner: Optional[Union["Item_Type", "Collection_Type"]]
    """The :class:`~pystac.Item` or :class:`~pystac.Collection` that this asset belongs
    to, or ``None`` if it has no owner."""

    extra_fields: Dict[str, Any]
    """Optional, additional fields for this asset. This is used by extensions as a
    way to serialize and deserialize properties on asset object JSON."""

    def __init__(
        self,
        href: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        media_type: Optional[str] = None,
        roles: Optional[List[str]] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.href = href
        self.title = title
        self.description = description
        self.media_type = media_type
        self.roles = roles
        self.extra_fields = extra_fields or {}

        # The Item which owns this Asset.
        self.owner = None

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
        if utils.is_absolute_href(self.href):
            return self.href
        else:
            if self.owner is not None:
                return utils.make_absolute_href(self.href, self.owner.get_self_href())
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

        if self.extra_fields is not None and len(self.extra_fields) > 0:
            for k, v in self.extra_fields.items():
                d[k] = v

        if self.roles is not None:
            d["roles"] = self.roles

        return d

    def clone(self) -> "Asset":
        """Clones this asset.

        Returns:
            Asset: The clone of this asset.
        """
        cls = self.__class__
        return cls(
            href=self.href,
            title=self.title,
            description=self.description,
            media_type=self.media_type,
            roles=self.roles,
            extra_fields=self.extra_fields,
        )

    @property
    def common_metadata(self) -> "CommonMetadata_Type":
        """Access the asset's common metadata fields as a
        :class:`~pystac.CommonMetadata` object."""
        return common_metadata.CommonMetadata(self)

    def __repr__(self) -> str:
        return "<Asset href={}>".format(self.href)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Asset":
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

        return cls(
            href=href,
            media_type=media_type,
            title=title,
            description=description,
            roles=roles,
            extra_fields=properties,
        )
