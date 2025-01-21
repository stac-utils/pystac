from __future__ import annotations

import os
import shutil
from copy import copy, deepcopy
from html import escape
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

from pystac import MediaType, STACError, common_metadata, utils
from pystac.html.jinja_env import get_jinja_env
from pystac.utils import is_absolute_href, make_absolute_href, make_relative_href

if TYPE_CHECKING:
    from pystac.common_metadata import CommonMetadata
    from pystac.extensions.ext import AssetExt

#: Generalized version of :class:`Asset`
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

    title: str | None
    """Optional displayed title for clients and users."""

    description: str | None
    """A description of the Asset providing additional details, such as how it was
    processed or created. CommonMark 0.29 syntax MAY be used for rich text
    representation."""

    media_type: str | None
    """Optional description of the media type. Registered Media Types are preferred.
    See :class:`~pystac.MediaType` for common media types."""

    roles: list[str] | None
    """Optional, Semantic roles (i.e. thumbnail, overview, data, metadata) of the
    asset."""

    owner: Assets | None
    """The :class:`~pystac.Item` or :class:`~pystac.Collection` that this asset belongs
    to, or ``None`` if it has no owner."""

    extra_fields: dict[str, Any]
    """Optional, additional fields for this asset. This is used by extensions as a
    way to serialize and deserialize properties on asset object JSON."""

    def __init__(
        self,
        href: str,
        title: str | None = None,
        description: str | None = None,
        media_type: str | None = None,
        roles: list[str] | None = None,
        extra_fields: dict[str, Any] | None = None,
    ) -> None:
        self.href = utils.make_posix_style(href)
        self.title = title
        self.description = description
        self.media_type = media_type
        self.roles = roles
        self.extra_fields = extra_fields or {}

        # The Item which owns this Asset.
        self.owner = None

    def set_owner(self, obj: Assets) -> None:
        """Sets the owning item of this Asset.

        The owning item will be used to resolve relative HREFs of this asset.

        Args:
            obj: The Collection or Item that owns this asset.
        """
        self.owner = obj

    def get_absolute_href(self) -> str | None:
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

    def to_dict(self) -> dict[str, Any]:
        """Returns this Asset as a dictionary.

        Returns:
            dict: A serialization of the Asset.
        """

        d: dict[str, Any] = {"href": self.href}

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
        return f"<Asset href={self.href}>"

    def _repr_html_(self) -> str:
        jinja_env = get_jinja_env()
        if jinja_env:
            template = jinja_env.get_template("JSON.jinja2")
            return str(template.render(dict=self.to_dict()))
        else:
            return escape(repr(self))

    @classmethod
    def from_dict(cls: type[A], d: dict[str, Any]) -> A:
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
        that owns it. See :meth:`~pystac.Item.delete_asset` for that.

        Does not modify the asset.
        """
        href = _absolute_href(self.href, self.owner, "delete")
        os.remove(href)

    @property
    def ext(self) -> AssetExt:
        """Accessor for extension classes on this asset

        Example::

            asset.ext.proj.code = "EPSG:4326"
        """
        from pystac.extensions.ext import AssetExt

        return AssetExt(stac_object=self)


class Assets(Protocol):
    """Protocol, with functionality, for STAC objects that have assets."""

    assets: dict[str, Asset]
    """The asset dictionary."""

    def get_assets(
        self,
        media_type: str | MediaType | None = None,
        role: str | None = None,
    ) -> dict[str, Asset]:
        """Get this object's assets.

        Args:
            media_type: If set, filter the assets such that only those with a
                matching ``media_type`` are returned.
            role: If set, filter the assets such that only those with a matching
                ``role`` are returned.

        Returns:
            Dict[str, Asset]: A dictionary of assets that match ``media_type``
                and/or ``role`` if set or else all of this object's assets.
        """
        return {
            k: deepcopy(v)
            for k, v in self.assets.items()
            if (media_type is None or v.media_type == media_type)
            and (role is None or v.has_role(role))
        }

    def add_asset(self, key: str, asset: Asset) -> None:
        """Adds an Asset to this object.

        Args:
            key : The unique key of this asset.
            asset : The Asset to add.
        """
        asset.set_owner(self)
        self.assets[key] = asset

    def delete_asset(self, key: str) -> None:
        """Deletes the asset at the given key, and removes the asset's data
        file from the local filesystem.

        It is an error to attempt to delete an asset's file if it is on a
        remote filesystem.

        To delete the asset without removing the file, use `del item.assets["key"]`.

        Args:
            key: The unique key of this asset.
        """
        asset = self.assets[key]
        asset.set_owner(self)
        asset.delete()

        del self.assets[key]

    def make_asset_hrefs_relative(self) -> Assets:
        """Modify each asset's HREF to be relative to this object's self HREF.

        Returns:
            Item: self
        """
        self_href = self.get_self_href()
        for asset in self.assets.values():
            if is_absolute_href(asset.href):
                if self_href is None:
                    raise STACError(
                        "Cannot make asset HREFs relative if no self_href is set."
                    )
                asset.href = make_relative_href(asset.href, self_href)
        return self

    def make_asset_hrefs_absolute(self) -> Assets:
        """Modify each asset's HREF to be absolute.

        Any asset HREFs that are relative will be modified to absolute based on this
        item's self HREF.

        Returns:
            Assets: self
        """
        self_href = self.get_self_href()
        for asset in self.assets.values():
            if not is_absolute_href(asset.href):
                if self_href is None:
                    raise STACError(
                        "Cannot make relative asset HREFs absolute "
                        "if no self_href is set."
                    )
                asset.href = make_absolute_href(asset.href, self_href)
        return self

    def get_self_href(self) -> str | None:
        """Abstract definition of STACObject.get_self_href.

        Needed to make the `make_asset_hrefs_{absolute|relative}` methods pass
        type checking. Refactoring out all the link behavior in STACObject to
        its own protocol would be too heavy, so we just use this stub instead.
        """
        ...


def _absolute_href(href: str, owner: Assets | None, action: str = "access") -> str:
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
