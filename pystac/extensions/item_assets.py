"""Implements the :stac-ext:`Item Assets Definition Extension <item-assets>`."""

from copy import deepcopy
from typing import Any, Dict, List, Optional

import pystac
from pystac.extensions.base import ExtensionManagementMixin
from pystac.extensions.hooks import ExtensionHooks
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.utils import get_required

SCHEMA_URI = "https://stac-extensions.github.io/item-assets/v1.0.0/schema.json"

ITEM_ASSETS_PROP = "item_assets"

ASSET_TITLE_PROP = "title"
ASSET_DESC_PROP = "description"
ASSET_TYPE_PROP = "type"
ASSET_ROLES_PROP = "roles"


class AssetDefinition:
    """Object that contains details about the datafiles that will be included in member
    Items for this Collection.

    See the :stac-ext:`Asset Object <item-assets#asset-object>` for details.
    """

    properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, AssetDefinition):
            return NotImplemented
        return self.to_dict() == o.to_dict()

    @classmethod
    def create(
        cls,
        title: Optional[str],
        description: Optional[str],
        media_type: Optional[str],
        roles: Optional[List[str]],
    ) -> "AssetDefinition":
        """
        Creates a new asset definition.

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
        """
        asset_defn = cls({})
        asset_defn.apply(
            title=title, description=description, media_type=media_type, roles=roles
        )
        return asset_defn

    def apply(
        self,
        title: Optional[str],
        description: Optional[str],
        media_type: Optional[str],
        roles: Optional[List[str]],
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
        """
        self.title = title
        self.description = description
        self.media_type = media_type
        self.roles = roles

    @property
    def title(self) -> Optional[str]:
        """Gets or sets the displayed title for clients and users."""
        return self.properties.get(ASSET_TITLE_PROP)

    @title.setter
    def title(self, v: Optional[str]) -> None:
        if v is None:
            self.properties.pop(ASSET_TITLE_PROP, None)
        else:
            self.properties[ASSET_TITLE_PROP] = v

    @property
    def description(self) -> Optional[str]:
        """Gets or sets a description of the Asset providing additional details, such as
        how it was processed or created. `CommonMark 0.29 <http://commonmark.org/>`__
        syntax MAY be used for rich text representation."""
        return self.properties.get(ASSET_DESC_PROP)

    @description.setter
    def description(self, v: Optional[str]) -> None:
        if v is None:
            self.properties.pop(ASSET_DESC_PROP, None)
        else:
            self.properties[ASSET_DESC_PROP] = v

    @property
    def media_type(self) -> Optional[str]:
        """Gets or sets the `media type
        <https://github.com/radiantearth/stac-spec/tree/v1.0.0/catalog-spec/catalog-spec.md#media-types>`__
        of the asset."""
        return self.properties.get(ASSET_TYPE_PROP)

    @media_type.setter
    def media_type(self, v: Optional[str]) -> None:
        if v is None:
            self.properties.pop(ASSET_TYPE_PROP, None)
        else:
            self.properties[ASSET_TYPE_PROP] = v

    @property
    def roles(self) -> Optional[List[str]]:
        """Gets or sets the `semantic roles
        <https://github.com/radiantearth/stac-spec/tree/v1.0.0/item-spec/item-spec.md#asset-role-types>`__
        of the asset, similar to the use of rel in links."""
        return self.properties.get(ASSET_ROLES_PROP)

    @roles.setter
    def roles(self, v: Optional[List[str]]) -> None:
        if v is None:
            self.properties.pop(ASSET_ROLES_PROP, None)
        else:
            self.properties[ASSET_ROLES_PROP] = v

    def to_dict(self) -> Dict[str, Any]:
        """Returns a JSON-like dictionary representing this ``AssetDefinition``."""
        return deepcopy(self.properties)

    def create_asset(self, href: str) -> pystac.Asset:
        """Creates a new :class:`~pystac.Asset` instance using the fields from this
        ``AssetDefinition`` and the given ``href``."""
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


class ItemAssetsExtension(ExtensionManagementMixin[pystac.Collection]):
    collection: pystac.Collection

    def __init__(self, collection: pystac.Collection) -> None:
        self.collection = collection

    @property
    def item_assets(self) -> Dict[str, AssetDefinition]:
        """Gets or sets a dictionary of assets that can be found in member Items. Maps
        the asset key to an :class:`AssetDefinition` instance."""
        result: Dict[str, Any] = get_required(
            self.collection.extra_fields.get(ITEM_ASSETS_PROP), self, ITEM_ASSETS_PROP
        )
        return {k: AssetDefinition(v) for k, v in result.items()}

    @item_assets.setter
    def item_assets(self, v: Dict[str, AssetDefinition]) -> None:
        self.collection.extra_fields[ITEM_ASSETS_PROP] = {
            k: asset_def.properties for k, asset_def in v.items()
        }

    def __repr__(self) -> str:
        return f"<ItemAssetsExtension collection.id = {self.collection.id}>"

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> "ItemAssetsExtension":
        """Extends the given :class:`~pystac.Collection` with properties from the
        :stac-ext:`Item Assets Extension <item-assets>`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Collection):
            cls.validate_has_extension(obj, add_if_missing)
            return cls(obj)
        else:
            raise pystac.ExtensionTypeError(
                f"Item Assets extension does not apply to type '{type(obj).__name__}'"
            )


class ItemAssetsExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"asset", "item-assets"}
    stac_object_types = {pystac.STACObjectType.COLLECTION}

    def migrate(
        self, obj: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        # Handle that the "item-assets" extension had the id of "assets", before
        # collection assets (since removed) took over the ID of "assets"
        if version < "1.0.0-beta.1" and "asset" in info.extensions:
            if "assets" in obj:
                obj["item_assets"] = obj["assets"]
                del obj["assets"]

        super().migrate(obj, version, info)


ITEM_ASSETS_EXTENSION_HOOKS: ExtensionHooks = ItemAssetsExtensionHooks()
