"""
Implements the `Item Asset Definition Object
<https://github.com/radiantearth/stac-spec/blob/v1.1.0/collection-spec/collection-spec.md#item-asset-definition-object>`__
for use as values in the :attr:`~pystac.Collection.item_assets` dict.
"""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

import pystac

if TYPE_CHECKING:
    from pystac.extensions.ext import ItemAssetExt


ASSET_TITLE_PROP = "title"
ASSET_DESC_PROP = "description"
ASSET_TYPE_PROP = "type"
ASSET_ROLES_PROP = "roles"


class ItemAssetDefinition:
    """Implementation of the `Item Asset Definition Object
    <https://github.com/radiantearth/stac-spec/blob/v1.1.0/collection-spec/collection-spec.md#item-asset-definition-object>`__
    for use as values in the :attr:`~pystac.Collection.item_assets` dict.
    """

    properties: dict[str, Any]

    owner: pystac.Collection | None

    def __init__(
        self, properties: dict[str, Any], owner: pystac.Collection | None = None
    ) -> None:
        self.properties = properties
        self.owner = owner

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, ItemAssetDefinition):
            return NotImplemented
        return self.to_dict() == o.to_dict()

    @classmethod
    def create(
        cls,
        title: str | None,
        description: str | None,
        media_type: str | None,
        roles: list[str] | None,
        extra_fields: dict[str, Any] | None = None,
    ) -> ItemAssetDefinition:
        """
        Creates a new asset definition.

        Args:
            title : Displayed title for clients and users.
            description : Description of the Asset providing additional details,
                such as how it was processed or created.
                `CommonMark 0.29 <http://commonmark.org/>`__ syntax MAY be used
                for rich text representation.
            media_type : `media type\
                <https://github.com/radiantearth/stac-spec/tree/v1.1.0/catalog-spec/catalog-spec.md#media-types>`__
                 of the asset.
            roles : `semantic roles
                <https://github.com/radiantearth/stac-spec/tree/v1.1.0/item-spec/item-spec.md#asset-role-types>`__
                of the asset, similar to the use of rel in links.
            extra_fields : Additional fields on the asset definition, e.g. from
                extensions.
        """
        asset_defn = cls({})
        asset_defn.apply(
            title=title,
            description=description,
            media_type=media_type,
            roles=roles,
            extra_fields=extra_fields,
        )
        return asset_defn

    def apply(
        self,
        title: str | None,
        description: str | None,
        media_type: str | None,
        roles: list[str] | None,
        extra_fields: dict[str, Any] | None = None,
    ) -> None:
        """
        Sets the properties for this asset definition.

        Args:
            title : Displayed title for clients and users.
            description : Description of the Asset providing additional details,
                such as how it was processed or created.
                `CommonMark 0.29 <http://commonmark.org/>`__ syntax MAY be used
                for rich text representation.
            media_type : `media type\
                <https://github.com/radiantearth/stac-spec/tree/v1.0.0/catalog-spec/catalog-spec.md#media-types>`__
                 of the asset.
            roles : `semantic roles
                <https://github.com/radiantearth/stac-spec/tree/v1.0.0/item-spec/item-spec.md#asset-role-types>`__
                of the asset, similar to the use of rel in links.
            extra_fields : Additional fields on the asset definition, e.g. from
                extensions.
        """
        if extra_fields:
            self.properties.update(extra_fields)
        self.title = title
        self.description = description
        self.media_type = media_type
        self.roles = roles
        self.owner = None

    def set_owner(self, obj: pystac.Collection) -> None:
        """Sets the owning item of this ItemAssetDefinition.

        The owning item will be used to resolve relative HREFs of this asset.

        Args:
            obj: The Collection that owns this asset.
        """
        self.owner = obj

    @property
    def title(self) -> str | None:
        """Gets or sets the displayed title for clients and users."""
        return self.properties.get(ASSET_TITLE_PROP)

    @title.setter
    def title(self, v: str | None) -> None:
        if v is None:
            self.properties.pop(ASSET_TITLE_PROP, None)
        else:
            self.properties[ASSET_TITLE_PROP] = v

    @property
    def description(self) -> str | None:
        """Gets or sets a description of the Asset providing additional details, such as
        how it was processed or created. `CommonMark 0.29 <http://commonmark.org/>`__
        syntax MAY be used for rich text representation."""
        return self.properties.get(ASSET_DESC_PROP)

    @description.setter
    def description(self, v: str | None) -> None:
        if v is None:
            self.properties.pop(ASSET_DESC_PROP, None)
        else:
            self.properties[ASSET_DESC_PROP] = v

    @property
    def media_type(self) -> str | None:
        """Gets or sets the `media type
        <https://github.com/radiantearth/stac-spec/tree/v1.0.0/catalog-spec/catalog-spec.md#media-types>`__
        of the asset."""
        return self.properties.get(ASSET_TYPE_PROP)

    @media_type.setter
    def media_type(self, v: str | None) -> None:
        if v is None:
            self.properties.pop(ASSET_TYPE_PROP, None)
        else:
            self.properties[ASSET_TYPE_PROP] = v

    @property
    def roles(self) -> list[str] | None:
        """Gets or sets the `semantic roles
        <https://github.com/radiantearth/stac-spec/tree/v1.0.0/item-spec/item-spec.md#asset-role-types>`__
        of the asset, similar to the use of rel in links."""
        return self.properties.get(ASSET_ROLES_PROP)

    @roles.setter
    def roles(self, v: list[str] | None) -> None:
        if v is None:
            self.properties.pop(ASSET_ROLES_PROP, None)
        else:
            self.properties[ASSET_ROLES_PROP] = v

    def to_dict(self) -> dict[str, Any]:
        """Returns a dictionary representing this ``ItemAssetDefinition``."""
        return deepcopy(self.properties)

    def create_asset(self, href: str) -> pystac.Asset:
        """Creates a new :class:`~pystac.Asset` instance using the fields from this
        ``ItemAssetDefinition`` and the given ``href``."""
        return pystac.Asset(
            href=href,
            title=self.title,
            description=self.description,
            media_type=self.media_type,
            roles=self.roles,
            extra_fields={
                k: v
                for k, v in self.properties.items()
                if k
                not in {
                    ASSET_TITLE_PROP,
                    ASSET_DESC_PROP,
                    ASSET_TYPE_PROP,
                    ASSET_ROLES_PROP,
                }
            },
        )

    @property
    def ext(self) -> ItemAssetExt:
        """Accessor for extension classes on this item_asset

        Example::

            collection.item_assets["data"].ext.proj.epsg = 4326
        """
        from pystac.extensions.ext import ItemAssetExt

        return ItemAssetExt(stac_object=self)


class _ItemAssets(dict):  # type:ignore
    """Private class for exposing item_assets as a dict

    This class coerces values to ``ItemAssetDefinition``s and
    sets that owner on all ``ItemAssetDefinition``s to the collection
    that it is owned by.
    """

    collection: pystac.Collection

    def __init__(self, collection: pystac.Collection) -> None:
        self.collection = collection
        if not collection.extra_fields.get("item_assets"):
            collection.extra_fields["item_assets"] = {}
        self.update(collection.extra_fields["item_assets"])

    def __setitem__(self, key: str, value: Any) -> None:
        if isinstance(value, ItemAssetDefinition):
            asset_definition = value
            asset_definition.set_owner(self.collection)
        else:
            asset_definition = ItemAssetDefinition(value, self.collection)
        self.collection.extra_fields["item_assets"][key] = asset_definition.properties
        super().__setitem__(key, asset_definition)

    def update(self, *args: Any, **kwargs: Any) -> None:
        for k, v in dict(*args, **kwargs).items():
            self[k] = v
