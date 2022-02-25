"""Implements the :stac-ext:`Timestamps Extension <timestamps>`."""

from datetime import datetime as datetime
from pystac.summaries import RangeSummary
from typing import Dict, Any, Iterable, Generic, Optional, TypeVar, Union, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import datetime_to_str, map_opt, str_to_datetime

T = TypeVar("T", pystac.Item, pystac.Asset)

SCHEMA_URI = "https://stac-extensions.github.io/timestamps/v1.0.0/schema.json"

PUBLISHED_PROP = "published"
EXPIRES_PROP = "expires"
UNPUBLISHED_PROP = "unpublished"


class TimestampsExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Union[pystac.Item, pystac.Collection]],
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Item` or :class:`~pystac.Asset` with properties from the
    :stac-ext:`Timestamps Extension <timestamps>`. This class is generic over the type
    of STAC Object to be extended (e.g. :class:`~pystac.Item`, :class:`~pystac.Asset`).

    To create a concrete instance of :class:`TimestampsExtension`, use the
    :meth:`TimestampsExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> ts_ext = TimestampsExtension.ext(item)
    """

    def apply(
        self,
        published: Optional[datetime] = None,
        expires: Optional[datetime] = None,
        unpublished: Optional[datetime] = None,
    ) -> None:
        """Applies timestamps extension properties to the extended Item.

        Args:
            published : Date and time the corresponding data
                was published the first time.
            expires : Date and time the corresponding data
                expires (is not valid any longer).
            unpublished : Date and time the corresponding data
                was unpublished.
        """
        self.published = published
        self.expires = expires
        self.unpublished = unpublished

    @property
    def published(self) -> Optional[datetime]:
        """Gets or sets a datetime object that represents the date and time that the
        corresponding data was published the first time.

        'Published' has a different meaning depending on where it is used. If available
        in the asset properties, it refers to the timestamps valid for the actual data
        linked to the Asset Object. If it comes from the Item properties, it refers to
        timestamp valid for the metadata.
        """
        return map_opt(str_to_datetime, self._get_property(PUBLISHED_PROP, str))

    @published.setter
    def published(self, v: Optional[datetime]) -> None:
        self._set_property(PUBLISHED_PROP, map_opt(datetime_to_str, v))

    @property
    def expires(self) -> Optional[datetime]:
        """Gets or sets a datetime object that represents the date and time the
        corresponding data expires (is not valid any longer).

        'Unpublished' has a different meaning depending on where it is used. If
        available in the asset properties, it refers to the timestamps valid for the
        actual data linked to the Asset Object. If it comes from the Item properties,
        it refers to to the timestamp valid for the metadata.
        """
        return map_opt(str_to_datetime, self._get_property(EXPIRES_PROP, str))

    @expires.setter
    def expires(self, v: Optional[datetime]) -> None:
        self._set_property(EXPIRES_PROP, map_opt(datetime_to_str, v))

    @property
    def unpublished(self) -> Optional[datetime]:
        """Gets or sets a datetime object that represents the date and time the
        corresponding data was unpublished.

        'Unpublished' has a different meaning depending on where it is used. If
        available in the asset properties, it refers to the timestamps valid for the
        actual data linked to the Asset Object. If it comes from the Item properties,
        it's referencing to the timestamp valid for the metadata.
        """
        return map_opt(str_to_datetime, self._get_property(UNPUBLISHED_PROP, str))

    @unpublished.setter
    def unpublished(self, v: Optional[datetime]) -> None:
        self._set_property(UNPUBLISHED_PROP, map_opt(datetime_to_str, v))

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> "TimestampsExtension[T]":
        """Extends the given STAC Object with properties from the :stac-ext:`Timestamps
        Extension <timestamps>`.

        This extension can be applied to instances of :class:`~pystac.Item` or
        :class:`~pystac.Asset`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Item):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(TimestampsExtension[T], ItemTimestampsExtension(obj))
        elif isinstance(obj, pystac.Asset):
            cls.validate_owner_has_extension(obj, add_if_missing)
            return cast(TimestampsExtension[T], AssetTimestampsExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"Timestamps extension does not apply to type '{type(obj).__name__}'"
            )

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> "SummariesTimestampsExtension":
        """Returns the extended summaries object for the given collection."""
        cls.validate_has_extension(obj, add_if_missing)
        return SummariesTimestampsExtension(obj)


class ItemTimestampsExtension(TimestampsExtension[pystac.Item]):
    """A concrete implementation of :class:`TimestampsExtension` on an
    :class:`~pystac.Item` that extends the properties of the Item to include properties
    defined in the :stac-ext:`Timestamps Extension <timestamps>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`TimestampsExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: pystac.Item
    """The :class:`~pystac.Item` being extended."""

    properties: Dict[str, Any]
    """The :class:`~pystac.Item` properties, including extension properties."""

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return "<ItemTimestampsExtension Item id={}>".format(self.item.id)


class AssetTimestampsExtension(TimestampsExtension[pystac.Asset]):
    """A concrete implementation of :class:`TimestampsExtension` on an
    :class:`~pystac.Asset` that extends the Asset fields to include properties
    defined in the :stac-ext:`Timestamps Extension <timestamps>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`TimestampsExtension.ext` on an :class:`~pystac.Asset` to extend it.
    """

    asset_href: str
    """The ``href`` value of the :class:`~pystac.Asset` being extended."""

    properties: Dict[str, Any]
    """The :class:`~pystac.Asset` fields, including extension properties."""

    additional_read_properties: Optional[Iterable[Dict[str, Any]]] = None
    """If present, this will be a list containing 1 dictionary representing the
    properties of the owning :class:`~pystac.Item`."""

    def __init__(self, asset: pystac.Asset):
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, pystac.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return "<AssetTimestampsExtension Asset href={}>".format(self.asset_href)


class SummariesTimestampsExtension(SummariesExtension):
    """A concrete implementation of :class:`~SummariesExtension` that extends
    the ``summaries`` field of a :class:`~pystac.Collection` to include properties
    defined in the :stac-ext:`Timestamps Extension <timestamps>`.
    """

    @property
    def published(self) -> Optional[RangeSummary[datetime]]:
        """Get or sets the summary of :attr:`TimestampsExtension.published` values
        for this Collection.
        """

        return map_opt(
            lambda s: RangeSummary(
                str_to_datetime(s.minimum), str_to_datetime(s.maximum)
            ),
            self.summaries.get_range(PUBLISHED_PROP),
        )

    @published.setter
    def published(self, v: Optional[RangeSummary[datetime]]) -> None:
        self._set_summary(
            PUBLISHED_PROP,
            map_opt(
                lambda s: RangeSummary(
                    datetime_to_str(s.minimum), datetime_to_str(s.maximum)
                ),
                v,
            ),
        )

    @property
    def expires(self) -> Optional[RangeSummary[datetime]]:
        """Get or sets the summary of :attr:`TimestampsExtension.expires` values
        for this Collection.
        """

        return map_opt(
            lambda s: RangeSummary(
                str_to_datetime(s.minimum), str_to_datetime(s.maximum)
            ),
            self.summaries.get_range(EXPIRES_PROP),
        )

    @expires.setter
    def expires(self, v: Optional[RangeSummary[datetime]]) -> None:
        self._set_summary(
            EXPIRES_PROP,
            map_opt(
                lambda s: RangeSummary(
                    datetime_to_str(s.minimum), datetime_to_str(s.maximum)
                ),
                v,
            ),
        )

    @property
    def unpublished(self) -> Optional[RangeSummary[datetime]]:
        """Get or sets the summary of :attr:`TimestampsExtension.unpublished` values
        for this Collection.
        """

        return map_opt(
            lambda s: RangeSummary(
                str_to_datetime(s.minimum), str_to_datetime(s.maximum)
            ),
            self.summaries.get_range(UNPUBLISHED_PROP),
        )

    @unpublished.setter
    def unpublished(self, v: Optional[RangeSummary[datetime]]) -> None:
        self._set_summary(
            UNPUBLISHED_PROP,
            map_opt(
                lambda s: RangeSummary(
                    datetime_to_str(s.minimum), datetime_to_str(s.maximum)
                ),
                v,
            ),
        )


class TimestampsExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"timestamps"}
    stac_object_types = {pystac.STACObjectType.ITEM}


TIMESTAMPS_EXTENSION_HOOKS: ExtensionHooks = TimestampsExtensionHooks()
