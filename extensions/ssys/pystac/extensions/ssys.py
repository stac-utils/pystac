"""Implements the :stac-ext:`Solar System Extension <ssys>`."""

from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.utils import StringEnum

#: Generalized version of :class:`~pystac.Item`, :class:`~pystac.Asset` or
#: :class:`~pystac.ItemAssetDefinition`
T = TypeVar(
    "T",
    pystac.Item,
    pystac.Asset,
    pystac.ItemAssetDefinition,
    pystac.Collection,
    pystac.Catalog,
)

# WHen updating, change SCHEMA_URI and move the previous value in SCHEMA_URIS
SCHEMA_URI: str = "https://stac-extensions.github.io/ssys/v1.1.1/schema.json"
SCHEMA_URIS: list[str] = [SCHEMA_URI]
PREFIX: str = "ssys:"

# Field names
TARGETS_PROPS = PREFIX + "targets"
LOCAL_TIME_PROPS = PREFIX + "local_time"
TARGET_CLASS_PROPS = PREFIX + "target_class"


class SolSysTargetClass(StringEnum):
    """Accepted values for the planetary body's target class
    according to the IVOA.
    """

    ASTEROID = "asteroid"
    DWARF_PLANET = "dwarf_planet"
    PLANET = "planet"
    SATELLITE = "satellite"
    COMET = "comet"
    EXOPLANET = "exoplanet"
    INTERPLANETARY_MEDIUM = "interplanetary_medium"
    SAMPLE = "sample"
    SKY = "sky"
    SPACECRAFT = "spacecraft"
    SPACEJUNK = "spacejunk"
    STAR = "star"
    CALIBRATION = "calibration"


class SolSysExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection | pystac.Catalog],
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Item` or :class:`~pystac.Asset` with properties from the
    :stac-ext:`Solar System Extension <eo>`. This class is generic over the type of
    STAC Object to be extended (e.g. :class:`~pystac.Item`,
    :class:`~pystac.Asset`).

    To create a concrete instance of :class:`SolSysExtension`, use the
    :meth:`SolSysExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> ssys_ext = SolSysExtension.ext(item)
    """

    name: Literal["ssys"] = "ssys"

    def apply(
        self,
        targets: list[str] | None = None,
        local_time: str | None = None,
        target_class: SolSysTargetClass | None = None,
    ) -> None:
        """Applies Solar System Extension properties to the extended
        :class:`~pystac.Item` or :class:`~pystac.Asset`.

        Args:
            targets : Array to hold list of target bodies (e.g. Mars, Moon, Earth)
                conforming to the `International Virtual Observatory Alliance<https://www.ivoa.net/documents/EPNTAP/20220822/REC-EPNTAP-2.0.html#tth_sEc2.1.3>`_
                target name specification.
            local_time : Lexicographically sortable time string (e.g., `01:115:12.343`)
            target_class : The identity of the type of the target as defined by
                the `International Virtual Observatory Alliance<https://www.ivoa.net/documents/EPNTAP/20220822/REC-EPNTAP-2.0.html#tth_sEc2.1.3>`_
        """
        self.targets = targets
        self.local_time = local_time
        self.target_class = target_class

    @property
    def targets(self) -> list[str] | None:
        """Allows to have one or more targets listed within an array of strings.
        This can happen, for example, if several moons are in the same view.

        As an example, this scene has both of Ganymede and Jupiter in the same image
        as taken by the NASA mission Cassini `PIA02862<https://photojournal.jpl.nasa.gov/catalog/PIA02862>`_.

        Returns:
            list[str] or None
        """
        return self._get_property(TARGETS_PROPS, list[str])

    @targets.setter
    def targets(self, _targets: list[str] | None) -> None:
        self._set_property(TARGETS_PROPS, _targets)

    @property
    def local_time(self) -> str | None:
        """Allows for API searchable non-UTC time definitions.

        The time should be encoded in a string that is lexicographically sortable.
        It is unlikely that this time should be something like the SpacecraftClockCount
        or another entry from the PDS metadata as most metadata files do not include
        a local (or local solar time). This field exists to support discovery in a time
        format that is meaningful to the user. Suggested formats are provided below:

        ==== ==========================
        Body Time String Format
        ==== ==========================
        Mars ``MarsYear:Sol:LocalTime``
        ==== ==========================

        As a fallback one can consider using the Julian date. This has drawbacks
         though, as the Julian date does not
         account for the day/night cycle in different bodies which is often a factor
         in selecting data.

        Returns:
            str or None
        """
        return self._get_property(LOCAL_TIME_PROPS, str)

    @local_time.setter
    def local_time(self, _local_time: str | None) -> None:
        self._set_property(LOCAL_TIME_PROPS, _local_time)

    @property
    def target_class(self) -> SolSysTargetClass | None:
        """Identifies the type of the target.
        Solar System bodies are defined without ambiguity by the couple target_class
        and target_name.
        Values for this class are derived from the `International Virtual
        Observatory Alliance <https://www.ivoa.net/documents/EPNTAP/20220822/REC-EPNTAP-2.0.html#tth_sEc2.1.3>`__target
        description parameter.

        Accepted values are:
        - asteroid
        - dwarf_planet
        - planet
        - satellite
        - comet
        - exoplanet
        - interplanetary_medium
        - sample
        - sky
        - spacecraft
        - spacejunk
        - star
        - calibration

        Returns:
            SolSysTargetClass or None
        """
        return self._get_property(TARGET_CLASS_PROPS, SolSysTargetClass)

    @target_class.setter
    def target_class(self, _target_class: SolSysTargetClass | None) -> None:
        self._set_property(TARGET_CLASS_PROPS, _target_class)

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def get_schema_uris(cls) -> list[str]:
        import warnings

        warnings.warn(
            "get_schema_urls is deprecated and will be removed in v2",
            DeprecationWarning,
        )

        return SCHEMA_URIS

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> SolSysExtension[T]:
        """Extends the given STAC Object with properties from the
        :stac-ext:`Solar System Extension <ssys>`.

        This extension can be applied to instances of
        :class:`~pystac.Item`, :class:`pystac.Catalog` or :class:`~pystac.Collection`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(SolSysExtension[T], ItemSolSysExtension(obj))
        elif isinstance(obj, pystac.Collection):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(SolSysExtension[T], CollectionSolSysExtension(obj))
        elif isinstance(obj, pystac.Catalog):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(SolSysExtension[T], CatalogSolSysExtension(obj))
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesSolSysExtension:
        """Returns the extended summaries object for the given collection."""
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesSolSysExtension(obj)


class ItemSolSysExtension(SolSysExtension[pystac.Item]):
    """A concrete implementation of :class:`SolSysExtension` on an
    :class:`~pystac.Item` that extends the properties of the Item to include properties
    defined in the :stac-ext:`Solar System Extension <ssys>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`SolSysExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: pystac.Item
    """The :class:`~pystac.Item` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Item` properties, including extension properties."""

    def __init__(self, item: pystac.Item) -> None:
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemSolSysExtension Item id={self.item.id}>"


class CollectionSolSysExtension(SolSysExtension[pystac.Collection]):
    """A concrete implementation of :class:`SolSysExtension` on an
    :class:`~pystac.Collection` that extends the properties of the
    Collection to include properties defined in
    the :stac-ext:`Solar System Extension <ssys>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`SolSysExtension.ext` on an :class:`~pystac.Collection` to extend it.
    """

    collection: pystac.Collection
    """The :class:`~pystac.Collection` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Collection` properties, including extension properties."""

    def __init__(self, collection: pystac.Collection) -> None:
        self.collection = collection
        self.properties = collection.extra_fields

    def __repr__(self) -> str:
        return f"<CollectionSolSysExtension Collection id={self.collection.id}>"


class CatalogSolSysExtension(SolSysExtension[pystac.Catalog]):
    """A concrete implementation of :class:`SolSysExtension` on an
    :class:`~pystac.catalog` that extends the properties of the
    catalog to include properties defined in
    the :stac-ext:`Solar System Extension <ssys>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`SolSysExtension.ext` on an :class:`~pystac.catalog` to extend it.
    """

    catalog: pystac.Catalog
    """The :class:`~pystac.catalog` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.catalog` properties, including extension properties."""

    def __init__(self, catalog: pystac.Catalog) -> None:
        self.catalog = catalog
        self.properties = catalog.extra_fields

    def __repr__(self) -> str:
        return f"<catalogSolSysExtension catalog id={self.catalog.id}>"


class SummariesSolSysExtension(SummariesExtension):
    """A concrete implementation of :class:`~pystac.extensions.base.SummariesExtension`
    that extends the ``summaries`` field of a :class:`~pystac.Collection` to include
    properties defined in the :stac-ext:`Solar System Extension <ssys>`.
    """

    @property
    def targets(self) -> list[str] | None:
        """Get or sets the summary of :attr:`SolSysExtension.targets` values
        for this Collection.
        """

        return self.summaries.get_list(TARGETS_PROPS)

    @targets.setter
    def targets(self, v: list[str] | None) -> None:
        self._set_summary(TARGETS_PROPS, v)

    @property
    def local_time(self) -> list[str] | None:
        """Get or sets the summary of :attr:`SolSYsExtension.local_time` values
        for this Collection.
        """
        return self.summaries.get_list(LOCAL_TIME_PROPS)

    @local_time.setter
    def local_time(self, v: list[str] | None) -> None:
        self._set_summary(LOCAL_TIME_PROPS, v)

    @property
    def target_class(self) -> list[SolSysTargetClass] | None:
        """Get or sets the summary of :attr:`SolSysExtension.target_class` values
        for this Collection.
        """
        return self.summaries.get_list(TARGET_CLASS_PROPS)

    @target_class.setter
    def target_class(self, v: list[SolSysTargetClass] | None) -> None:
        self._set_summary(TARGET_CLASS_PROPS, v)


class SolSysExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"ssys", *[uri for uri in SCHEMA_URIS if uri != SCHEMA_URI]}
    stac_object_types = {
        pystac.STACObjectType.ITEM,
        pystac.STACObjectType.COLLECTION,
        pystac.STACObjectType.CATALOG,
    }

    def migrate(
        self, obj: dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        return super().migrate(obj, version, info)


SSYS_EXTENSION_HOOKS: ExtensionHooks = SolSysExtensionHooks()
