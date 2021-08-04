"""Implements the Timestamps extension.

https://github.com/stac-extensions/timestamps
"""

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    Iterable,
    Optional,
    TypeVar,
    Union,
    cast,
)

from pystac import asset as asset_mod
from pystac import errors
from pystac import item as item_mod
from pystac import stac_object, summaries, utils
from pystac.extensions import base, hooks

if TYPE_CHECKING:
    from datetime import datetime as Datetime_Type

    from pystac.asset import Asset as Asset_Type
    from pystac.collection import Collection as Collection_Type
    from pystac.item import Item as Item_Type
    from pystac.summaries import RangeSummary as RangeSummary_Type

T = TypeVar("T", "Item_Type", "Asset_Type")

SCHEMA_URI = "https://stac-extensions.github.io/timestamps/v1.0.0/schema.json"

PUBLISHED_PROP = "published"
EXPIRES_PROP = "expires"
UNPUBLISHED_PROP = "unpublished"


class TimestampsExtension(
    Generic[T],
    base.PropertiesExtension,
    base.ExtensionManagementMixin[Union["Item_Type", "Collection_Type"]],
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
        published: Optional["Datetime_Type"] = None,
        expires: Optional["Datetime_Type"] = None,
        unpublished: Optional["Datetime_Type"] = None,
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
    def published(self) -> Optional["Datetime_Type"]:
        """Gets or sets a datetime object that represents the date and time that the
        corresponding data was published the first time.

        'Published' has a different meaning depending on where it is used. If available
        in the asset properties, it refers to the timestamps valid for the actual data
        linked to the Asset Object. If it comes from the Item properties, it refers to
        timestamp valid for the metadata.
        """
        return utils.map_opt(
            utils.str_to_datetime, self._get_property(PUBLISHED_PROP, str)
        )

    @published.setter
    def published(self, v: Optional["Datetime_Type"]) -> None:
        self._set_property(PUBLISHED_PROP, utils.map_opt(utils.datetime_to_str, v))

    @property
    def expires(self) -> Optional["Datetime_Type"]:
        """Gets or sets a datetime object that represents the date and time the
        corresponding data expires (is not valid any longer).

        'Unpublished' has a different meaning depending on where it is used. If
        available in the asset properties, it refers to the timestamps valid for the
        actual data linked to the Asset Object. If it comes from the Item properties,
        it refers to to the timestamp valid for the metadata.
        """
        return utils.map_opt(
            utils.str_to_datetime, self._get_property(EXPIRES_PROP, str)
        )

    @expires.setter
    def expires(self, v: Optional["Datetime_Type"]) -> None:
        self._set_property(EXPIRES_PROP, utils.map_opt(utils.datetime_to_str, v))

    @property
    def unpublished(self) -> Optional["Datetime_Type"]:
        """Gets or sets a datetime object that represents the date and time the
        corresponding data was unpublished.

        'Unpublished' has a different meaning depending on where it is used. If
        available in the asset properties, it refers to the timestamps valid for the
        actual data linked to the Asset Object. If it comes from the Item properties,
        it's referencing to the timestamp valid for the metadata.
        """
        return utils.map_opt(
            utils.str_to_datetime, self._get_property(UNPUBLISHED_PROP, str)
        )

    @unpublished.setter
    def unpublished(self, v: Optional["Datetime_Type"]) -> None:
        self._set_property(UNPUBLISHED_PROP, utils.map_opt(utils.datetime_to_str, v))

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
        if isinstance(obj, item_mod.Item):
            cls.validate_has_extension(obj, add_if_missing)
            return cast(TimestampsExtension[T], ItemTimestampsExtension(obj))
        elif isinstance(obj, asset_mod.Asset):
            cls.validate_owner_has_extension(obj, add_if_missing)
            return cast(TimestampsExtension[T], AssetTimestampsExtension(obj))
        else:
            raise errors.ExtensionTypeError(
                f"Timestamps extension does not apply to type '{type(obj).__name__}'"
            )

    @classmethod
    def summaries(
        cls, obj: "Collection_Type", add_if_missing: bool = False
    ) -> "SummariesTimestampsExtension":
        """Returns the extended summaries object for the given collection."""
        cls.validate_has_extension(obj, add_if_missing)
        return SummariesTimestampsExtension(obj)


class ItemTimestampsExtension(TimestampsExtension["Item_Type"]):
    """A concrete implementation of :class:`TimestampsExtension` on an
    :class:`~pystac.Item` that extends the properties of the Item to include properties
    defined in the :stac-ext:`Timestamps Extension <timestamps>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`TimestampsExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: "Item_Type"
    """The :class:`~pystac.Item` being extended."""

    properties: Dict[str, Any]
    """The :class:`~pystac.Item` properties, including extension properties."""

    def __init__(self, item: "Item_Type"):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return "<ItemTimestampsExtension Item id={}>".format(self.item.id)


class AssetTimestampsExtension(TimestampsExtension["Asset_Type"]):
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

    def __init__(self, asset: "Asset_Type"):
        self.asset_href = asset.href
        self.properties = asset.extra_fields
        if asset.owner and isinstance(asset.owner, item_mod.Item):
            self.additional_read_properties = [asset.owner.properties]

    def __repr__(self) -> str:
        return "<AssetTimestampsExtension Asset href={}>".format(self.asset_href)


class SummariesTimestampsExtension(base.SummariesExtension):
    """A concrete implementation of :class:`~SummariesExtension` that extends
    the ``summaries`` field of a :class:`~pystac.Collection` to include properties
    defined in the :stac-ext:`Timestamps Extension <timestamps>`.
    """

    @property
    def published(self) -> Optional["RangeSummary_Type[Datetime_Type]"]:
        """Get or sets the summary of :attr:`TimestampsExtension.published` values
        for this Collection.
        """

        return utils.map_opt(
            lambda s: summaries.RangeSummary(
                utils.str_to_datetime(s.minimum), utils.str_to_datetime(s.maximum)
            ),
            self.summaries.get_range(PUBLISHED_PROP),
        )

    @published.setter
    def published(self, v: Optional["RangeSummary_Type[Datetime_Type]"]) -> None:
        self._set_summary(
            PUBLISHED_PROP,
            utils.map_opt(
                lambda s: summaries.RangeSummary(
                    utils.datetime_to_str(s.minimum), utils.datetime_to_str(s.maximum)
                ),
                v,
            ),
        )

    @property
    def expires(self) -> Optional["RangeSummary_Type[Datetime_Type]"]:
        """Get or sets the summary of :attr:`TimestampsExtension.expires` values
        for this Collection.
        """

        return utils.map_opt(
            lambda s: summaries.RangeSummary(
                utils.str_to_datetime(s.minimum), utils.str_to_datetime(s.maximum)
            ),
            self.summaries.get_range(EXPIRES_PROP),
        )

    @expires.setter
    def expires(self, v: Optional["RangeSummary_Type[Datetime_Type]"]) -> None:
        self._set_summary(
            EXPIRES_PROP,
            utils.map_opt(
                lambda s: summaries.RangeSummary(
                    utils.datetime_to_str(s.minimum), utils.datetime_to_str(s.maximum)
                ),
                v,
            ),
        )

    @property
    def unpublished(self) -> Optional["RangeSummary_Type[Datetime_Type]"]:
        """Get or sets the summary of :attr:`TimestampsExtension.unpublished` values
        for this Collection.
        """

        return utils.map_opt(
            lambda s: summaries.RangeSummary(
                utils.str_to_datetime(s.minimum), utils.str_to_datetime(s.maximum)
            ),
            self.summaries.get_range(UNPUBLISHED_PROP),
        )

    @unpublished.setter
    def unpublished(self, v: Optional["RangeSummary_Type[Datetime_Type]"]) -> None:
        self._set_summary(
            UNPUBLISHED_PROP,
            utils.map_opt(
                lambda s: summaries.RangeSummary(
                    utils.datetime_to_str(s.minimum), utils.datetime_to_str(s.maximum)
                ),
                v,
            ),
        )


class TimestampsExtensionHooks(hooks.ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"timestamps"}
    stac_object_types = {stac_object.STACObjectType.ITEM}


TIMESTAMPS_EXTENSION_HOOKS: hooks.ExtensionHooks = TimestampsExtensionHooks()
