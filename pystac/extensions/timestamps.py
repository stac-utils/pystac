from datetime import datetime as Datetime
from pystac.extensions.hooks import ExtensionHooks
from typing import Generic, Optional, Set, TypeVar, cast

import pystac as ps
from pystac.extensions.base import ExtensionException, ExtensionManagementMixin, PropertiesExtension
from pystac.utils import datetime_to_str, map_opt, str_to_datetime

T = TypeVar('T', ps.Item, ps.Asset)

SCHEMA_URI = "https://stac-extensions.github.io/timestamps/v1.0.0/schema.json"

PUBLISHED_PROP = "published"
EXPIRES_PROP = "expires"
UNPUBLISHED_PROP = "unpublished"


class TimestampsExtension(Generic[T], PropertiesExtension, ExtensionManagementMixin[ps.Item]):
    """TimestampsItemExt is the extension of an Item in that
    allows to specify additional timestamps for assets and metadata.
    """
    def apply(self,
              published: Optional[Datetime] = None,
              expires: Optional[Datetime] = None,
              unpublished: Optional[Datetime] = None) -> None:
        """Applies timestamps extension properties to the extended Item.

        Args:
            published (datetime or None): Date and time the corresponding data
                was published the first time.
            expires (datetime or None): Date and time the corresponding data
                expires (is not valid any longer).
            unpublished (datetime or None): Date and time the corresponding data
                was unpublished.
        """
        self.published = published
        self.expires = expires
        self.unpublished = unpublished

    @property
    def published(self) -> Optional[Datetime]:
        """Get or sets a datetime objects that represent
            the date and time that the corresponding data
            was published the first time.

        'Published'
        has a different meaning depending on where it is used. If available in
        the asset properties, it refers to the timestamps valid for the actual data linked
        to the Asset Object. If it comes from the Item properties, it's referencing to
        the timestamp valid for the metadata.

        Returns:
            datetime
        """
        return map_opt(str_to_datetime, self._get_property(PUBLISHED_PROP, str))

    @published.setter
    def published(self, v: Optional[Datetime]) -> None:
        self._set_property(PUBLISHED_PROP, map_opt(datetime_to_str, v))

    @property
    def expires(self) -> Optional[Datetime]:
        """Get or sets a datetime objects that represent
            the date and time the corresponding data
            expires (is not valid any longer).

        'Unpublished'
        has a different meaning depending on where it is used. If available in
        the asset properties, it refers to the timestamps valid for the actual data linked
        to the Asset Object. If it comes from the Item properties, it's referencing to
        the timestamp valid for the metadata.

        Returns:
            datetime
        """
        return map_opt(str_to_datetime, self._get_property(EXPIRES_PROP, str))

    @expires.setter
    def expires(self, v: Optional[Datetime]) -> None:
        self._set_property(EXPIRES_PROP, map_opt(datetime_to_str, v))

    @property
    def unpublished(self) -> Optional[Datetime]:
        """Get or sets a datetime objects that represent
        the Date and time the corresponding data was unpublished.

        'Unpublished'
        has a different meaning depending on where it is used. If available in
        the asset properties, it refers to the timestamps valid for the actual data linked
        to the Asset Object. If it comes from the Item properties, it's referencing to
        the timestamp valid for the metadata.

        Returns:
            datetime
        """
        return map_opt(str_to_datetime, self._get_property(UNPUBLISHED_PROP, str))

    @unpublished.setter
    def unpublished(self, v: Optional[Datetime]) -> None:
        self._set_property(UNPUBLISHED_PROP, map_opt(datetime_to_str, v))

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI


class ItemTimestampsExtension(TimestampsExtension[ps.Item]):
    def __init__(self, item: ps.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return '<ItemtimestampsExtension Item id={}>'.format(self.item.id)


class AssetTimestampsExtension(TimestampsExtension[ps.Asset]):
    def __init__(self, asset: ps.Asset):
        self.asset_href = asset.href
        self.properties = asset.properties
        if asset.owner and isinstance(asset.owner, ps.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return '<AssettimestampsExtension Asset href={}>'.format(self.asset_href)


class TimestampsExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: Set[str] = set(['timestamps'])
    stac_object_types: Set[ps.STACObjectType] = set([ps.STACObjectType.ITEM])


def timestamps_ext(obj: T) -> TimestampsExtension[T]:
    if isinstance(obj, ps.Item):
        return cast(TimestampsExtension[T], ItemTimestampsExtension(obj))
    elif isinstance(obj, ps.Asset):
        return cast(TimestampsExtension[T], AssetTimestampsExtension(obj))
    else:
        raise ExtensionException(f"File extension does not apply to type {type(obj)}")


TIMESTAMPS_EXTENSION_HOOKS = TimestampsExtensionHooks()