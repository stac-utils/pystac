from datetime import datetime as Datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import pystac
from pystac import utils

if TYPE_CHECKING:
    from pystac.collection import Provider
    from pystac.asset import Asset


class CommonMetadata:
    """Object containing fields that are not included in core item schema but
    are still commonly used. All attributes are defined within the properties of
    this item and are optional

    Args:
        properties : Dictionary of attributes that is the Item's properties
    """

    def __init__(self, properties: Dict[str, Any]):
        self.properties = properties

    # Basics
    @property
    def title(self) -> Optional[str]:
        """Get or set the item's title

        Returns:
            str: Human readable title describing the item
        """
        return self.properties.get("title")

    @title.setter
    def title(self, v: Optional[str]) -> None:
        self.properties["title"] = v

    @property
    def description(self) -> Optional[str]:
        """Get or set the item's description

        Returns:
            str: Detailed description of the item
        """
        return self.properties.get("description")

    @description.setter
    def description(self, v: Optional[str]) -> None:
        self.properties["description"] = v

    # Date and Time Range
    @property
    def start_datetime(self) -> Optional[Datetime]:
        """Get or set the item's start_datetime.

        Returns:
            datetime: Start date and time for the item
        """
        return self.get_start_datetime()

    @start_datetime.setter
    def start_datetime(self, v: Optional[Datetime]) -> None:
        self.set_start_datetime(v)

    def get_start_datetime(self, asset: Optional["Asset"] = None) -> Optional[Datetime]:
        """Gets an Item or an Asset start_datetime.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            datetime
        """
        if asset is None or "start_datetime" not in asset.extra_fields:
            start_datetime = self.properties.get("start_datetime")
        else:
            start_datetime = asset.extra_fields.get("start_datetime")

        if start_datetime is None:
            return None

        return utils.str_to_datetime(start_datetime)

    def set_start_datetime(
        self, start_datetime: Optional[Datetime], asset: Optional["Asset"] = None
    ) -> None:
        """Set an Item or an Asset start_datetime.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["start_datetime"] = (
                None if start_datetime is None else utils.datetime_to_str(start_datetime)
            )
        else:
            asset.extra_fields["start_datetime"] = (
                None if start_datetime is None else utils.datetime_to_str(start_datetime)
            )

    @property
    def end_datetime(self) -> Optional[Datetime]:
        """Get or set the item's end_datetime. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string

        Returns:
            datetime: End date and time for the item
        """
        return self.get_end_datetime()

    @end_datetime.setter
    def end_datetime(self, v: Optional[Datetime]) -> None:
        self.set_end_datetime(v)

    def get_end_datetime(self, asset: Optional["Asset"] = None) -> Optional[Datetime]:
        """Gets an Item or an Asset end_datetime.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            datetime
        """
        if asset is None or "end_datetime" not in asset.extra_fields:
            end_datetime = self.properties.get("end_datetime")
        else:
            end_datetime = asset.extra_fields.get("end_datetime")

        if end_datetime is None:
            return None

        return utils.str_to_datetime(end_datetime)

    def set_end_datetime(
        self, end_datetime: Optional[Datetime], asset: Optional["Asset"] = None
    ) -> None:
        """Set an Item or an Asset end_datetime.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["end_datetime"] = (
                None if end_datetime is None else utils.datetime_to_str(end_datetime)
            )
        else:
            asset.extra_fields["end_datetime"] = (
                None if end_datetime is None else utils.datetime_to_str(end_datetime)
            )

    # License
    @property
    def license(self) -> Optional[str]:
        """Get or set the current license

        Returns:
            str: Item's license(s), either SPDX identifier of 'various'
        """
        return self.get_license()

    @license.setter
    def license(self, v: Optional[str]) -> None:
        self.set_license(v)

    def get_license(self, asset: Optional["Asset"] = None) -> Optional[str]:
        """Gets an Item or an Asset license.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or "license" not in asset.extra_fields:
            return self.properties.get("license")
        else:
            return asset.extra_fields.get("license")

    def set_license(
        self, license: Optional[str], asset: Optional["Asset"] = None
    ) -> None:
        """Set an Item or an Asset license.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["license"] = license
        else:
            asset.extra_fields["license"] = license

    # Providers
    @property
    def providers(self) -> Optional[List["Provider"]]:
        """Get or set a list of the item's providers. The setter can take either
        a Provider object or a dict but always stores each provider as a dict

        Returns:
            List["Provider"]: List of organizations that captured or processed the data,
            encoded as Provider objects
        """
        return self.get_providers()

    @providers.setter
    def providers(self, v: Optional[List["Provider"]]) -> None:
        self.set_providers(v)

    def get_providers(self, asset: Optional["Asset"] = None) -> Optional[List["Provider"]]:
        """Gets an Item or an Asset providers.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            List["Provider"]
        """
        if asset is None or "providers" not in asset.extra_fields:
            providers = self.properties.get("providers")
        else:
            providers = asset.extra_fields.get("providers")

        if providers is None:
            return None

        return [pystac.Provider.from_dict(d) for d in providers]

    def set_providers(
        self, providers: Optional[List["Provider"]], asset: Optional["Asset"] = None
    ) -> None:
        """Set an Item or an Asset providers.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            if providers is None:
                self.properties.pop("providers", None)
            else:
                providers_dicts = [d.to_dict() for d in providers]
                self.properties["providers"] = providers_dicts
        else:
            if providers is None:
                asset.extra_fields.pop("providers", None)
            else:
                providers_dicts = [d.to_dict() for d in providers]
                asset.extra_fields["providers"] = providers_dicts

    # Instrument
    @property
    def platform(self) -> Optional[str]:
        """Get or set the item's platform attribute

        Returns:
            str: Unique name of the specific platform to which the instrument
            is attached
        """
        return self.get_platform()

    @platform.setter
    def platform(self, v: Optional[str]) -> None:
        self.set_platform(v)

    def get_platform(self, asset: Optional["Asset"] = None) -> Optional[str]:
        """Gets an Item or an Asset platform.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or "platform" not in asset.extra_fields:
            return self.properties.get("platform")
        else:
            return asset.extra_fields.get("platform")

    def set_platform(
        self, platform: Optional[str], asset: Optional["Asset"] = None
    ) -> None:
        """Set an Item or an Asset platform.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["platform"] = platform
        else:
            asset.extra_fields["platform"] = platform

    @property
    def instruments(self) -> Optional[List[str]]:
        """Get or set the names of the instruments used

        Returns:
            List[str]: Name(s) of instrument(s) used
        """
        return self.get_instruments()

    @instruments.setter
    def instruments(self, v: Optional[List[str]]) -> None:
        self.set_instruments(v)

    def get_instruments(self, asset: Optional["Asset"] = None) -> Optional[List[str]]:
        """Gets an Item or an Asset instruments.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            Optional[List[str]]
        """
        if asset is None or "instruments" not in asset.extra_fields:
            return self.properties.get("instruments")
        else:
            return asset.extra_fields.get("instruments")

    def set_instruments(
        self, instruments: Optional[List[str]], asset: Optional["Asset"] = None
    ) -> None:
        """Set an Item or an Asset instruments.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["instruments"] = instruments
        else:
            asset.extra_fields["instruments"] = instruments

    @property
    def constellation(self) -> Optional[str]:
        """Get or set the name of the constellation associate with an item

        Returns:
            str: Name of the constellation to which the platform belongs
        """
        return self.get_constellation()

    @constellation.setter
    def constellation(self, v: Optional[str]) -> None:
        self.set_constellation(v)

    def get_constellation(self, asset: Optional["Asset"] = None) -> Optional[str]:
        """Gets an Item or an Asset constellation.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or "constellation" not in asset.extra_fields:
            return self.properties.get("constellation")
        else:
            return asset.extra_fields.get("constellation")

    def set_constellation(
        self, constellation: Optional[str], asset: Optional["Asset"] = None
    ) -> None:
        """Set an Item or an Asset constellation.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["constellation"] = constellation
        else:
            asset.extra_fields["constellation"] = constellation

    @property
    def mission(self) -> Optional[str]:
        """Get or set the name of the mission associated with an item

        Returns:
            str: Name of the mission in which data are collected
        """
        return self.get_mission()

    @mission.setter
    def mission(self, v: Optional[str]) -> None:
        self.set_mission(v)

    def get_mission(self, asset: Optional["Asset"] = None) -> Optional[str]:
        """Gets an Item or an Asset mission.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            str
        """
        if asset is None or "mission" not in asset.extra_fields:
            return self.properties.get("mission")
        else:
            return asset.extra_fields.get("mission")

    def set_mission(
        self, mission: Optional[str], asset: Optional["Asset"] = None
    ) -> None:
        """Set an Item or an Asset mission.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["mission"] = mission
        else:
            asset.extra_fields["mission"] = mission

    @property
    def gsd(self) -> Optional[float]:
        """Get or sets the Ground Sample Distance at the sensor.

        Returns:
            [float]: Ground Sample Distance at the sensor
        """
        return self.get_gsd()

    @gsd.setter
    def gsd(self, v: Optional[float]) -> None:
        self.set_gsd(v)

    def get_gsd(self, asset: Optional["Asset"] = None) -> Optional[float]:
        """Gets an Item or an Asset gsd.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value

        Returns:
            float
        """
        if asset is None or "gsd" not in asset.extra_fields:
            return self.properties.get("gsd")
        else:
            return asset.extra_fields.get("gsd")

    def set_gsd(self, gsd: Optional[float], asset: Optional["Asset"] = None) -> None:
        """Set an Item or an Asset gsd.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["gsd"] = gsd
        else:
            asset.extra_fields["gsd"] = gsd

    # Metadata
    @property
    def created(self) -> Optional[Datetime]:
        """Get or set the metadata file's creation date. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string

        Returns:
            datetime: Creation date and time of the metadata file
        """
        return self.get_created()

    @created.setter
    def created(self, v: Optional[Datetime]) -> None:
        self.set_created(v)

    def get_created(self, asset: Optional["Asset"] = None) -> Optional[Datetime]:
        """Gets an Item or an Asset created time.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value.

        Note:
            ``created`` and ``updated`` have different meaning depending on where they
            are used. If those fields are available in the Item `properties`, it's
            referencing the creation and update times of the metadata. Having those
            fields in the Item `assets` refers to the creation and update times of the
            actual data linked to in the Asset Object.

        Returns:
            datetime
        """
        if asset is None or "created" not in asset.extra_fields:
            created = self.properties.get("created")
        else:
            created = asset.extra_fields.get("created")

        if created is None:
            return None

        return utils.str_to_datetime(created)

    def set_created(
        self, created: Optional[Datetime], asset: Optional["Asset"] = None
    ) -> None:
        """Set an Item or an Asset created time.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["created"] = (
                None if created is None else utils.datetime_to_str(created)
            )
        else:
            asset.extra_fields["created"] = (
                None if created is None else utils.datetime_to_str(created)
            )

    @property
    def updated(self) -> Optional[Datetime]:
        """Get or set the metadata file's update date. All datetime attributes have
        setters that can take either a string or a datetime, but always stores
        the attribute as a string

        Note:
            ``created`` and ``updated`` have different meaning depending on where they
            are used. If those fields are available in the Item `properties`, it's
            referencing the creation and update times of the metadata. Having those
            fields in the Item `assets` refers to the creation and update times of the
            actual data linked to in the Asset Object.

        Returns:
            datetime: Date and time that the metadata file was most recently
                updated
        """
        return self.get_updated()

    @updated.setter
    def updated(self, v: Optional[Datetime]) -> None:
        self.set_updated(v)

    def get_updated(self, asset: Optional["Asset"] = None) -> Optional[Datetime]:
        """Gets an Item or an Asset updated time.

        If an Asset is supplied and the Item property exists on the Asset,
        returns the Asset's value. Otherwise returns the Item's value.

        Note:
            ``created`` and ``updated`` have different meaning depending on where they
            are used. If those fields are available in the Item `properties`, it's
            referencing the creation and update times of the metadata. Having those
            fields in the Item `assets` refers to the creation and update times of the
            actual data linked to in the Asset Object.

        Returns:
            datetime
        """
        if asset is None or "updated" not in asset.extra_fields:
            updated = self.properties.get("updated")
        else:
            updated = asset.extra_fields.get("updated")

        if updated is None:
            return None

        return utils.str_to_datetime(updated)

    def set_updated(
        self, updated: Optional[Datetime], asset: Optional["Asset"] = None
    ) -> None:
        """Set an Item or an Asset updated time.

        If an Asset is supplied, sets the property on the Asset.
        Otherwise sets the Item's value.
        """
        if asset is None:
            self.properties["updated"] = (
                None if updated is None else utils.datetime_to_str(updated)
            )
        else:
            asset.extra_fields["updated"] = (
                None if updated is None else utils.datetime_to_str(updated)
            )
