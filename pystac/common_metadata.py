from datetime import datetime as Datetime
from typing import Any, Dict, List, Optional

from pystac.utils import map_opt, str_to_datetime, datetime_to_str
from pystac.collection import Provider


class CommonMetadata:
    """Object containing fields that are not included in core Item schema but
    are still commonly used. All attributes are defined within the properties of
    the Item or the top-level property of an Asset and are optional

    Args:
        fields : Dictionary of attributes that are either the ``properties`` of the
        extended :class:`~pystac.Item` or the top-level fields of the extended
        :class:`~pystac.Asset`.
    """

    fields: Dict[str, Any]
    """The fields that this extension wraps. This may be the ``properties`` object (in
    the case of an :class:`~pystac.Item`) or the top-level fields (in the case of an
    :class:`pystac.Asset`).

    Note that making changes to this dictionary mutates the fields on the extended
    object directly."""

    def __init__(self, fields: Dict[str, Any]):
        self.fields = fields

    def _set_field(
        self, prop_name: str, v: Optional[Any], pop_if_none: bool = True
    ) -> None:
        if v is None and pop_if_none:
            self.fields.pop(prop_name, None)
        else:
            self.fields[prop_name] = v

    # Basics
    @property
    def title(self) -> Optional[str]:
        """Gets or sets the object's title

        Returns:
            str: Human readable title describing the Item or Asset
        """
        return self.fields.get("title")

    @title.setter
    def title(self, v: Optional[str]) -> None:
        self._set_field("title", v)

    @property
    def description(self) -> Optional[str]:
        """Gets or sets the object's description."""
        return self.fields.get("description")

    @description.setter
    def description(self, v: Optional[str]) -> None:
        self._set_field("description", v)

    # Date and Time Range
    @property
    def datetime(self) -> Optional[Datetime]:
        """Gets or sets the object's datetime. Value will be stored as a string in the
        ``fields`` dictionary."""
        return map_opt(str_to_datetime, self.fields.get("datetime"))

    @datetime.setter
    def datetime(self, v: Optional[Datetime]) -> None:
        self._set_field("datetime", map_opt(datetime_to_str, v), pop_if_none=False)

    @property
    def start_datetime(self) -> Optional[Datetime]:
        """Gets or sets the object's start_datetime. Value will be stored as a string in
        the ``fields`` dictionary.
        """
        return map_opt(str_to_datetime, self.fields.get("start_datetime"))

    @start_datetime.setter
    def start_datetime(self, v: Optional[Datetime]) -> None:
        self._set_field("start_datetime", map_opt(datetime_to_str, v))

    @property
    def end_datetime(self) -> Optional[Datetime]:
        """Gets or sets the object's end_datetime. Value will be stored as a string in
        the ``fields`` dictionary.
        """
        return map_opt(str_to_datetime, self.fields.get("end_datetime"))

    @end_datetime.setter
    def end_datetime(self, v: Optional[Datetime]) -> None:
        self._set_field("end_datetime", map_opt(datetime_to_str, v))

    # License
    @property
    def license(self) -> Optional[str]:
        """Get or set the current license."""
        return self.fields.get("license")

    @license.setter
    def license(self, v: Optional[str]) -> None:
        self._set_field("license", v)

    # Providers
    @property
    def providers(self) -> Optional[List[Provider]]:
        """Get or set a list of the object's providers. Value will be stored as a list
        of dictionaries in the ``fields`` dictionary.
        """
        maybe_providers: Optional[List[Dict[str, Any]]] = self.fields.get("providers")
        return map_opt(
            lambda providers: [Provider.from_dict(p) for p in providers],
            maybe_providers,
        )

    @providers.setter
    def providers(self, v: Optional[List[Provider]]) -> None:
        self._set_field(
            "providers", map_opt(lambda providers: [p.to_dict() for p in providers], v)
        )

    # Instrument
    @property
    def platform(self) -> Optional[str]:
        """Gets or set the object's platform attribute."""
        return self.fields.get("platform")

    @platform.setter
    def platform(self, v: Optional[str]) -> None:
        self._set_field("platform", v)

    @property
    def instruments(self) -> Optional[List[str]]:
        """Gets or set the names of the instruments used."""
        return self.fields.get("instruments")

    @instruments.setter
    def instruments(self, v: Optional[List[str]]) -> None:
        self._set_field("instruments", v)

    @property
    def constellation(self) -> Optional[str]:
        """Gets or set the name of the constellation associate with an object."""
        return self.fields.get("constellation")

    @constellation.setter
    def constellation(self, v: Optional[str]) -> None:
        self._set_field("constellation", v)

    @property
    def mission(self) -> Optional[str]:
        """Gets or set the name of the mission associated with an object."""
        return self.fields.get("mission")

    @mission.setter
    def mission(self, v: Optional[str]) -> None:
        self._set_field("mission", v)

    @property
    def gsd(self) -> Optional[float]:
        """Get or sets the Ground Sample Distance at the sensor."""
        return self.fields.get("gsd")

    @gsd.setter
    def gsd(self, v: Optional[float]) -> None:
        self._set_field("gsd", v)

    # Metadata
    @property
    def created(self) -> Optional[Datetime]:
        """Gets or sets the metadata file's creation date. Value will be stored as a string in
        the ``fields`` dictionary.

        Note:
            ``created`` has a different meaning depending on where it is used. If the
            field is available in the Item ``properties``, it refers to the creation
            time of the metadata. If it is available in an Asset's fields, it refers to
            the creation time of the actual data linked to in the Asset's ``href``.
        """
        return map_opt(str_to_datetime, self.fields.get("created"))

    @created.setter
    def created(self, v: Optional[Datetime]) -> None:
        self._set_field("created", map_opt(datetime_to_str, v))

    @property
    def updated(self) -> Optional[Datetime]:
        """Gets or sets the metadata file's update date. Value will be stored as a string in
        the ``fields`` dictionary.

        Note:
            ``update`` has a different meaning depending on where it is used. If the
            field is available in the Item ``properties``, it refers to the update
            time of the metadata. If it is available in an Asset's fields, it refers to
            the update time of the actual data linked to in the Asset's ``href``.
        """
        return map_opt(str_to_datetime, self.fields.get("updated"))

    @updated.setter
    def updated(self, v: Optional[Datetime]) -> None:
        self._set_field("updated", map_opt(datetime_to_str, v))

