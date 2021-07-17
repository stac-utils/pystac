from datetime import datetime as Datetime
from pystac.errors import STACError
from typing import Any, cast, Dict, List, Optional, Type, TYPE_CHECKING, TypeVar, Union

import pystac
from pystac import utils

if TYPE_CHECKING:
    from pystac.provider import Provider as Provider_Type
    from pystac.asset import Asset as Asset_Type
    from pystac.item import Item as Item_Type


P = TypeVar("P")


class CommonMetadata:
    """Object containing fields that are not included in core item schema but
    are still commonly used. All attributes are defined within the properties of
    this item and are optional

    Args:
        properties : Dictionary of attributes that is the Item's properties
    """

    object: Union["Asset_Type", "Item_Type"]
    """The object from which common metadata is obtained."""

    def __init__(self, object: Union["Asset_Type", "Item_Type"]):
        self.object = object

    def _set_field(self, prop_name: str, v: Optional[Any]) -> None:
        if hasattr(self.object, prop_name):
            setattr(self.object, prop_name, v)
        elif hasattr(self.object, "properties"):
            item = cast("Item_Type", self.object)
            if v is None:
                item.properties.pop(prop_name, None)
            else:
                item.properties[prop_name] = v
        elif hasattr(self.object, "extra_fields") and isinstance(
            self.object.extra_fields, Dict
        ):
            if v is None:
                self.object.extra_fields.pop(prop_name, None)
            else:
                self.object.extra_fields[prop_name] = v
        else:
            raise pystac.STACError(f"Cannot set field {prop_name} on {self}.")

    def _get_field(self, prop_name: str, _typ: Type[P]) -> Optional[P]:
        maybe_field: Optional[P]

        if hasattr(self.object, prop_name):
            return cast(Optional[P], getattr(self.object, prop_name))
        elif hasattr(self.object, "properties"):
            item = cast("Item_Type", self.object)
            return item.properties.get(prop_name)
        elif hasattr(self.object, "extra_fields") and isinstance(
            self.object.extra_fields, Dict
        ):
            return self.object.extra_fields.get(prop_name)
        else:
            raise STACError(f"Cannot get field {prop_name} from {self}.")

    # Basics
    @property
    def title(self) -> Optional[str]:
        """Gets or set the object's title."""
        return self._get_field("title", str)

    @title.setter
    def title(self, v: Optional[str]) -> None:
        self._set_field("title", v)

    @property
    def description(self) -> Optional[str]:
        """Gets or set the object's description."""
        return self._get_field("description", str)

    @description.setter
    def description(self, v: Optional[str]) -> None:
        self._set_field("description", v)

    # Date and Time Range
    @property
    def start_datetime(self) -> Optional[Datetime]:
        """Get or set the object's start_datetime."""
        return utils.map_opt(
            utils.str_to_datetime, self._get_field("start_datetime", str)
        )

    @start_datetime.setter
    def start_datetime(self, v: Optional[Datetime]) -> None:
        self._set_field("start_datetime", utils.map_opt(utils.datetime_to_str, v))

    @property
    def end_datetime(self) -> Optional[Datetime]:
        """Get or set the item's end_datetime."""
        return utils.map_opt(
            utils.str_to_datetime, self._get_field("end_datetime", str)
        )

    @end_datetime.setter
    def end_datetime(self, v: Optional[Datetime]) -> None:
        self._set_field("end_datetime", utils.map_opt(utils.datetime_to_str, v))

    # License
    @property
    def license(self) -> Optional[str]:
        """Get or set the current license."""
        return self._get_field("license", str)

    @license.setter
    def license(self, v: Optional[str]) -> None:
        self._set_field("license", v)

    # Providers
    @property
    def providers(self) -> Optional[List["Provider_Type"]]:
        """Get or set a list of the object's providers."""
        return utils.map_opt(
            lambda providers: [pystac.Provider.from_dict(d) for d in providers],
            self._get_field("providers", List[Dict[str, Any]]),
        )

    @providers.setter
    def providers(self, v: Optional[List["Provider_Type"]]) -> None:
        self._set_field(
            "providers",
            utils.map_opt(lambda providers: [p.to_dict() for p in providers], v),
        )

    # Instrument
    @property
    def platform(self) -> Optional[str]:
        """Gets or set the object's platform attribute."""
        return self._get_field("platform", str)

    @platform.setter
    def platform(self, v: Optional[str]) -> None:
        self._set_field("platform", v)

    @property
    def instruments(self) -> Optional[List[str]]:
        """Gets or sets the names of the instruments used."""
        return self._get_field("instruments", List[str])

    @instruments.setter
    def instruments(self, v: Optional[List[str]]) -> None:
        self._set_field("instruments", v)

    @property
    def constellation(self) -> Optional[str]:
        """Gets or set the name of the constellation associate with an object."""
        return self._get_field("constellation", str)

    @constellation.setter
    def constellation(self, v: Optional[str]) -> None:
        self._set_field("constellation", v)

    @property
    def mission(self) -> Optional[str]:
        """Gets or set the name of the mission associated with an object."""
        return self._get_field("mission", str)

    @mission.setter
    def mission(self, v: Optional[str]) -> None:
        self._set_field("mission", v)

    @property
    def gsd(self) -> Optional[float]:
        """Gets or sets the Ground Sample Distance at the sensor."""
        return self._get_field("gsd", float)

    @gsd.setter
    def gsd(self, v: Optional[float]) -> None:
        self._set_field("gsd", v)

    # Metadata
    @property
    def created(self) -> Optional[Datetime]:
        """Get or set the metadata file's creation date. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string.

        Note:
            ``created`` has a different meaning depending on the type of STAC object.
            On an :class:`~pystac.Item`, it refers to the creation time of the
            metadata. On an :class:`~pystac.Asset`, it refers to the creation time of
            the actual data linked to in :attr:`Asset.href <pystac.Asset.href`.
        """
        return utils.map_opt(utils.str_to_datetime, self._get_field("created", str))

    @created.setter
    def created(self, v: Optional[Datetime]) -> None:
        self._set_field("created", utils.map_opt(utils.datetime_to_str, v))

    @property
    def updated(self) -> Optional[Datetime]:
        """Get or set the metadata file's update date. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string

        Note:
            ``updated`` has a different meaning depending on the type of STAC object.
            On an :class:`~pystac.Item`, it refers to the update time of the
            metadata. On an :class:`~pystac.Asset`, it refers to the update time of
            the actual data linked to in :attr:`Asset.href <pystac.Asset.href`.
        """
        return utils.map_opt(utils.str_to_datetime, self._get_field("updated", str))

    @updated.setter
    def updated(self, v: Optional[Datetime]) -> None:
        self._set_field("updated", utils.map_opt(utils.datetime_to_str, v))
