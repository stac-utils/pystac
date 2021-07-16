from copy import deepcopy
from typing import Any, cast, Dict, List, Optional, TYPE_CHECKING, Union

from pystac.utils import is_absolute_href, make_absolute_href

if TYPE_CHECKING:
    from pystac.collection import Collection as Collection_Type
    from pystac.item import Item as Item_Type


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

    owner: Optional[Union["Item_Type", "Collection_Type"]]
    """The :class:`~pystac.Item` or :class:`~pystac.Collection` that this asset belongs
    to, or ``None`` if it has no owner."""

    fields: Dict[str, Any]
    """All fields associated with this asset."""

    def __init__(
        self,
        href: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        media_type: Optional[str] = None,
        roles: Optional[List[str]] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.fields = extra_fields or {}
        self.href = href
        self.title = title
        self.description = description
        self.media_type = media_type
        self.roles = roles

        # The Item which owns this Asset.
        self.owner = None

    def _set_field(
        self, prop_name: str, v: Optional[Any], pop_if_none: bool = True
    ) -> None:
        if v is None and pop_if_none:
            self.fields.pop(prop_name, None)
        else:
            self.fields[prop_name] = v

    @property
    def href(self) -> str:
        """Link to the asset object. Relative and absolute links are both allowed."""
        return cast(str, self.fields["href"])

    @href.setter
    def href(self, v: str) -> None:
        self.fields["href"] = v

    @property
    def title(self) -> Optional[str]:
        """Optional displayed title for clients and users."""
        return self.fields.get("title")

    @title.setter
    def title(self, v: Optional[str]) -> None:
        self._set_field("title", v)

    @property
    def description(self) -> Optional[str]:
        """A description of the Asset providing additional details, such as how it was
        processed or created. CommonMark 0.29 syntax MAY be used for rich text
        representation."""
        return self.fields.get("description")

    @description.setter
    def description(self, v: Optional[str]) -> None:
        self._set_field("description", v)

    @property
    def media_type(self) -> Optional[str]:
        """Optional description of the media type. Registered Media Types are preferred.
        See :class:`~pystac.MediaType` for common media types.

        Note:
            This will be stored in the "type" property of the Asset dictionary.
        """

        return self.fields.get("type")

    @media_type.setter
    def media_type(self, v: Optional[str]) -> None:
        self._set_field("type", v)

    @property
    def roles(self) -> Optional[List[str]]:
        """Optional, Semantic roles (i.e. thumbnail, overview, data, metadata) of the
        asset."""
        return self.fields.get("roles")

    @roles.setter
    def roles(self, v: Optional[List[str]]) -> None:
        self._set_field("roles", v)

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

    def to_dict(self, preserve_dict: bool = True) -> Dict[str, Any]:
        """Generate a dictionary representing the JSON of this Asset.

        Returns:
            dict: A serialization of the Asset that can be written out as JSON.
        """
        if preserve_dict:
            return deepcopy(self.fields)
        else:
            return self.fields

    def clone(self) -> "Asset":
        """Clones this asset.

        Returns:
            Asset: The clone of this asset.
        """
        cls = self.__class__
        return cls.from_dict(self.fields)

    def __repr__(self) -> str:
        return "<Asset href={}>".format(self.href)

    @classmethod
    def from_dict(cls, d: Dict[str, Any], preserve_dict: bool = True) -> "Asset":
        """Constructs an Asset from a dict.

        Returns:
            Asset: The Asset deserialized from the JSON dict.
        """
        if preserve_dict:
            d = deepcopy(d)
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
