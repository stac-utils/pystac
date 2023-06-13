from __future__ import annotations

import os
import shutil
from copy import copy, deepcopy
from html import escape
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar, Union

from pystac import common_metadata, utils
from pystac.html.jinja_env import get_jinja_env

if TYPE_CHECKING:
    from pystac.collection import Collection
    from pystac.common_metadata import CommonMetadata
    from pystac.item import Item

A = TypeVar("A", bound="Asset")


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

    owner: Optional[Union[Item, Collection]]
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
        self.href = utils.make_posix_style(href)
        self.title = title
        self.description = description
        self.media_type = media_type
        self.roles = roles
        self.extra_fields = extra_fields or {}

        # The Item which owns this Asset.
        self.owner = None

    def set_owner(self, obj: Union[Collection, Item]) -> None:
        """Sets the owning item of this Asset.

        The owning item will be used to resolve relative HREFs of this asset.

        Args:
            obj: The Collection or Item that owns this asset.
        """
        self.owner = obj

    def get_absolute_href(self) -> Optional[str]:
        """Gets the absolute href for this asset, if possible.

        If this Asset has no associated Item, and the asset HREF is a relative path,
            this method will return ``None``. If the Item that owns the Asset has no
            self HREF, this will also return ``None``.

        Returns:
            str: The absolute HREF of this asset, or None if an absolute HREF could not
                be determined.
        """
        if utils.is_absolute_href(self.href):
            return self.href
        else:
            if self.owner is not None:
                item_self = self.owner.get_self_href()
                if item_self is not None:
                    return utils.make_absolute_href(self.href, item_self)
            return None

    def to_dict(self) -> Dict[str, Any]:
        """Returns this Asset as a dictionary.

        Returns:
            dict: A serialization of the Asset.
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

    def clone(self) -> Asset:
        """Clones this asset. Makes a ``deepcopy`` of the
        :attr:`~pystac.Asset.extra_fields`.

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
            extra_fields=deepcopy(self.extra_fields),
        )

    def has_role(self, role: str) -> bool:
        """Check if a role exists in the Asset role list.

        Args:
            role: Role to check for existence.

        Returns:
            bool: True if role exists, else False.
        """
        if self.roles is None:
            return False
        else:
            return role in self.roles

    @property
    def common_metadata(self) -> CommonMetadata:
        """Access the asset's common metadata fields as a
        :class:`~pystac.CommonMetadata` object."""
        return common_metadata.CommonMetadata(self)

    def __repr__(self) -> str:
        return "<Asset href={}>".format(self.href)

    def _repr_html_(self) -> str:
        jinja_env = get_jinja_env()
        if jinja_env:
            template = jinja_env.get_template("JSON.jinja2")
            return str(template.render(dict=self.to_dict()))
        else:
            return escape(repr(self))

    @classmethod
    def from_dict(cls: Type[A], d: Dict[str, Any]) -> A:
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

    def move(self, href: str) -> Asset:
        """Moves this asset's file to a new location on the local filesystem,
        setting the asset href accordingly.

        Modifies the asset in place, and returns the same asset.

        Args:
            href: The new asset location. Must be a local path. If relative
                it must be relative to the owner object.

        Returns:
            Asset: The asset with the updated href.
        """
        src = _absolute_href(self.href, self.owner, "move")
        dst = _absolute_href(href, self.owner, "move")
        shutil.move(src, dst)
        self.href = href
        return self

    def copy(self, href: str) -> Asset:
        """Copies this asset's file to a new location on the local filesystem,
        setting the asset href accordingly.

        Modifies the asset in place, and returns the same asset.

        Args:
            href: The new asset location. Must be a local path. If relative
                it must be relative to the owner object.

        Returns:
            Asset: The asset with the updated href.
        """
        src = _absolute_href(self.href, self.owner, "copy")
        dst = _absolute_href(href, self.owner, "copy")
        shutil.copy2(src, dst)
        self.href = href
        return self

    def delete(self) -> None:
        """Delete this asset's file. Does not delete the asset from the item
        that owns it. See :func:`~pystac.Item.delete_asset` for that.

        Does not modify the asset.
        """
        href = _absolute_href(self.href, self.owner, "delete")
        os.remove(href)


def _absolute_href(
    href: str, owner: Optional[Union[Item, Collection]], action: str = "access"
) -> str:
    if utils.is_absolute_href(href):
        return href
    else:
        item_self = owner.get_self_href() if owner else None
        if item_self is None:
            raise ValueError(
                f"Cannot {action} file if asset href ('{href}') is relative "
                "and owner item is not set. Hint: try using "
                ":func:`~pystac.Item.make_asset_hrefs_absolute`"
            )
        return utils.make_absolute_href(href, item_self)
