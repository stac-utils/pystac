"""Implements the :stac-ext:`Label Extension <label>`."""

from pystac.extensions.base import ExtensionManagementMixin, SummariesExtension
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union, cast

import pystac
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import StringEnum, get_required, map_opt

SCHEMA_URI = "https://stac-extensions.github.io/label/v1.0.1/schema.json"

PREFIX = "label:"

PROPERTIES_PROP = PREFIX + "properties"
CLASSES_PROP = PREFIX + "classes"
DESCRIPTION_PROP = PREFIX + "description"
TYPE_PROP = PREFIX + "type"
TASKS_PROP = PREFIX + "tasks"
METHODS_PROP = PREFIX + "methods"
OVERVIEWS_PROP = PREFIX + "overviews"


class LabelRelType(StringEnum):
    """A list of rel types defined in the Label Extension.

    See the :stac-ext:`Label Extension Links <label#links-source-imagery>`
    documentation for details.
    """

    SOURCE = "source"
    """Used to indicate a link to the source item to which a label item applies."""


class LabelType(StringEnum):
    """Enumerates valid label types ("raster" or "vector")."""

    VECTOR = "vector"
    RASTER = "raster"

    ALL = [VECTOR, RASTER]
    """Convenience attribute for checking if values are valid label types"""


class LabelTask(StringEnum):
    """Enumerates recommended values for "label:tasks" field."""

    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    DETECTION = "detection"
    SEGMENTATION = "segmentation"


class LabelMethod(StringEnum):
    """Enumerates recommended values for "label:methods" field."""

    AUTOMATED = "automated"
    MANUAL = "manual"


class LabelClasses:
    """Defines the list of possible class names (e.g., tree, building, car, hippo).

    Use :meth:`LabelClasses.create` to create a new instance from property values.
    """

    properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Any]):
        self.properties = properties

    def apply(
        self,
        classes: Sequence[Union[str, int, float]],
        name: Optional[str] = None,
    ) -> None:
        """Sets the properties for this instance.

        Args:
            classes : The different possible class values.
            name : The property key within the asset's each Feature corresponding
                to class labels. If labels are raster-formatted, do not supply;
                required otherwise.
        """
        self.classes = classes
        self.name = name

    @classmethod
    def create(
        cls,
        classes: Sequence[Union[str, int, float]],
        name: Optional[str] = None,
    ) -> "LabelClasses":
        """Creates a new :class:`~LabelClasses` instance.

        Args:
            classes : The different possible class values.
            name : The property key within the asset's each Feature corresponding
                to class labels. If labels are raster-formatted, do not supply;
                required otherwise.
        """
        c = cls({})
        c.apply(classes, name)
        return c

    @property
    def classes(self) -> Sequence[Union[str, int, float]]:
        """Gets or sets the class values."""
        return get_required(self.properties.get("classes"), self, "classes")

    @classes.setter
    def classes(self, v: Sequence[Union[str, int, float]]) -> None:
        self.properties["classes"] = v

    @property
    def name(self) -> Optional[str]:
        """Gets or sets the property key within each Feature in the asset corresponding
        to class labels. If labels are raster-formatted, use ``None``.
        """
        return self.properties.get("name")

    @name.setter
    def name(self, v: Optional[str]) -> None:
        # The "name" property is required but may be null
        self.properties["name"] = v

    def __repr__(self) -> str:
        return "<ClassObject classes={}>".format(
            ",".join([str(x) for x in self.classes])
        )

    def __eq__(self, o: object) -> bool:
        if isinstance(o, LabelClasses):
            o = o.to_dict()

        if not isinstance(o, dict):
            return NotImplemented

        return self.to_dict() == o

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of this instance."""
        return self.properties


class LabelCount:
    """Contains counts for categorical data.

    Use :meth:`LabelCount.create` to create a new instance.
    """

    properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Any]):
        self.properties = properties

    def apply(self, name: str, count: int) -> None:
        """Sets the properties for this instance.

        Args:
            name : One of the different possible classes within the property.
            count : The number of occurrences of the class.
        """
        self.name = name
        self.count = count

    @classmethod
    def create(cls, name: str, count: int) -> "LabelCount":
        """Creates a :class:`LabelCount` instance.

        Args:
            name : One of the different possible classes within the property.
            count : The number of occurrences of the class.
        """
        x = cls({})
        x.apply(name, count)
        return x

    @property
    def name(self) -> str:
        """Gets or sets the class that this count represents."""
        return get_required(self.properties.get("name"), self, "name")

    @name.setter
    def name(self, v: str) -> None:

        self.properties["name"] = v

    @property
    def count(self) -> int:
        """Get or sets the number of occurrences of the class."""
        return get_required(self.properties.get("count"), self, "count")

    @count.setter
    def count(self, v: int) -> None:
        self.properties["count"] = v

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of this instance."""
        return self.properties

    def __eq__(self, o: object) -> bool:
        if isinstance(o, LabelCount):
            o = o.to_dict()

        if not isinstance(o, dict):
            return NotImplemented

        return self.to_dict() == o


class LabelStatistics:
    """Contains statistics for regression/continuous numeric value data.

    Use :meth:`LabelStatistics.create` to create a new instance.
    """

    properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    def apply(self, name: str, value: float) -> None:
        """Sets the property values for this instance.

        Args:
            name : The name of the statistic being reported.
            value : The value of the statistic
        """
        self.name = name
        self.value = value

    @classmethod
    def create(cls, name: str, value: float) -> "LabelStatistics":
        """Creates a new :class:`LabelStatistics` instance.

        Args:
            name : The name of the statistic being reported.
            value : The value of the statistic
        """
        x = cls({})
        x.apply(name, value)
        return x

    @property
    def name(self) -> str:
        """Gets or sets the name of the statistic being reported."""
        return get_required(self.properties.get("name"), self, "name")

    @name.setter
    def name(self, v: str) -> None:
        self.properties["name"] = v

    @property
    def value(self) -> float:
        """Gets or sets the value of the statistic."""
        return get_required(self.properties.get("value"), self, "value")

    @value.setter
    def value(self, v: float) -> None:
        self.properties["value"] = v

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of this LabelStatistics."""
        return self.properties

    def __eq__(self, o: object) -> bool:
        if isinstance(o, LabelStatistics):
            o = o.to_dict()

        if not isinstance(o, dict):
            return NotImplemented

        return self.to_dict() == o


class LabelOverview:
    """Stores counts (for classification-type data) or summary statistics (for
    continuous numerical/regression data).

    Use :meth:`LabelOverview.create` to create a new instance.
    """

    properties: Dict[str, Any]

    def __init__(self, properties: Dict[str, Any]):
        self.properties = properties

    def apply(
        self,
        property_key: Optional[str],
        counts: Optional[List[LabelCount]] = None,
        statistics: Optional[List[LabelStatistics]] = None,
    ) -> None:
        """Sets the properties for this instance.

        Either ``counts`` or ``statistics``, or both, can be placed in an overview;
        at least one is required.

        Args:
            property_key : The property key within the asset corresponding to
                class labels that these counts or statistics are referencing. If the
                label data is raster data, this should be None.
            counts: Optional list of :class:`LabelCounts` containing counts
                for categorical data.
            statistics: Optional list of :class:`LabelStatistics` containing statistics
                for regression/continuous numeric value data.
        """
        self.property_key = property_key
        self.counts = counts
        self.statistics = statistics

    @classmethod
    def create(
        cls,
        property_key: Optional[str],
        counts: Optional[List[LabelCount]] = None,
        statistics: Optional[List[LabelStatistics]] = None,
    ) -> "LabelOverview":
        """Creates a new instance.

        Either ``counts`` or ``statistics``, or both, can be placed in an overview;
        at least one is required.

        Args:
            property_key : The property key within the asset corresponding to
                class labels.
            counts: Optional list of :class:`LabelCounts` containing counts for
                categorical data.
            statistics: Optional list of :class:`LabelStatistics` containing statistics
                for regression/continuous numeric value data.
        """
        x = LabelOverview({})
        x.apply(property_key, counts, statistics)
        return x

    @property
    def property_key(self) -> Optional[str]:
        """Gets or sets the property key within the asset corresponding to class
        labels."""
        return self.properties.get("property_key")

    @property_key.setter
    def property_key(self, v: Optional[str]) -> None:
        self.properties["property_key"] = v

    @property
    def counts(self) -> Optional[List[LabelCount]]:
        """Gets or sets the list of :class:`LabelCounts` containing counts for
        categorical data."""
        counts = self.properties.get("counts")
        if counts is None:
            return None
        return [LabelCount(c) for c in counts]

    @counts.setter
    def counts(self, v: Optional[List[LabelCount]]) -> None:
        if v is None:
            self.properties.pop("counts", None)
        else:
            if not isinstance(v, list):
                raise pystac.STACError(
                    "counts must be a list! Invalid input: {}".format(v)
                )

            self.properties["counts"] = [c.to_dict() for c in v]

    @property
    def statistics(self) -> Optional[List[LabelStatistics]]:
        """Gets or sets the list of :class:`LabelStatistics` containing statistics for
        regression/continuous numeric value data."""
        statistics = self.properties.get("statistics")
        if statistics is None:
            return None

        return [LabelStatistics(s) for s in statistics]

    @statistics.setter
    def statistics(self, v: Optional[List[LabelStatistics]]) -> None:
        if v is None:
            self.properties.pop("statistics", None)
        else:
            self.properties["statistics"] = [s.to_dict() for s in v]

    def merge_counts(self, other: "LabelOverview") -> "LabelOverview":
        """Merges the counts associated with this overview with another overview.
        Creates a new instance.

        Args:
            other : The other LabelOverview to merge.

        Returns:
            A new LabelOverview with the counts merged. This will
            drop any statistics associated with either of the LabelOverviews.
        """
        assert self.property_key == other.property_key

        if self.counts is None:
            new_counts = other.counts
        else:
            if other.counts is None:
                new_counts = self.counts
            else:
                count_by_prop: Dict[str, int] = {}

                def add_counts(counts: List[LabelCount]) -> None:
                    for c in counts:
                        if c.name not in count_by_prop:
                            count_by_prop[c.name] = c.count
                        else:
                            count_by_prop[c.name] += c.count

                add_counts(self.counts)
                add_counts(other.counts)
                new_counts = [LabelCount.create(k, v) for k, v in count_by_prop.items()]
        return LabelOverview.create(self.property_key, counts=new_counts)

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of this LabelOverview."""
        return self.properties

    def __eq__(self, o: object) -> bool:
        if isinstance(o, LabelOverview):
            o = o.to_dict()

        if not isinstance(o, dict):
            return NotImplemented

        return self.to_dict() == o


class LabelExtension(ExtensionManagementMixin[Union[pystac.Item, pystac.Collection]]):
    """A class that can be used to extend the properties of an
    :class:`~pystac.Item` with properties from the :stac-ext:`Label Extension <label>`.

    To create an instance of :class:`LabeExtension`, use the
    :meth:`LabelExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> label_ext = LabelExtension.ext(item)
    """

    obj: pystac.Item
    schema_uri: str

    def __init__(self, item: pystac.Item) -> None:
        self.obj = item
        self.schema_uri = SCHEMA_URI

    def apply(
        self,
        label_description: str,
        label_type: LabelType,
        label_properties: Optional[List[str]] = None,
        label_classes: Optional[List[LabelClasses]] = None,
        label_tasks: Optional[List[Union[LabelTask, str]]] = None,
        label_methods: Optional[List[Union[LabelMethod, str]]] = None,
        label_overviews: Optional[List[LabelOverview]] = None,
    ) -> None:
        """Applies label extension properties to the extended Item.

        Args:
            label_description : A description of the label, how it was created,
                and what it is recommended for
            label_type : An Enum of either vector label type or raster label type. Use
                one of :class:`~pystac.LabelType`.
            label_properties : These are the names of the property field(s) in each
                Feature of the label asset's FeatureCollection that contains the classes
                (keywords from label:classes if the property defines classes).
                If labels are rasters, this should be None.
            label_classes : Optional, but required if using categorical data.
                A list of :class:`LabelClasses` instances defining the list of possible
                class names for each label:properties. (e.g., tree, building, car,
                hippo)
            label_tasks : Recommended to be a subset of 'regression', 'classification',
                'detection', or 'segmentation', but may be an arbitrary value.
            label_methods: Recommended to be a subset of 'automated' or 'manual',
                but may be an arbitrary value.
            label_overviews : Optional list of :class:`LabelOverview` instances
                that store counts (for classification-type data) or summary statistics
                (for continuous numerical/regression data).
        """
        self.label_description = label_description
        self.label_type = label_type
        self.label_properties = label_properties
        self.label_classes = label_classes
        self.label_tasks = label_tasks
        self.label_methods = label_methods
        self.label_overviews = label_overviews

    @property
    def label_description(self) -> str:
        """Gets or sets a description of the label, how it was created,
        and what it is recommended for."""
        return get_required(
            self.obj.properties.get(DESCRIPTION_PROP), self.obj, DESCRIPTION_PROP
        )

    @label_description.setter
    def label_description(self, v: str) -> None:
        self.obj.properties[DESCRIPTION_PROP] = v

    @property
    def label_type(self) -> LabelType:
        """Gets or sets an Enum of either vector label type or raster label type."""
        return LabelType(
            get_required(self.obj.properties.get(TYPE_PROP), self.obj, TYPE_PROP)
        )

    @label_type.setter
    def label_type(self, v: LabelType) -> None:
        self.obj.properties[TYPE_PROP] = v

    @property
    def label_properties(self) -> Optional[List[str]]:
        """Gets or sets the names of the property field(s) in each
        Feature of the label asset's FeatureCollection that contains the classes
        (keywords from label:classes if the property defines classes).
        If labels are rasters, this should be None."""
        return self.obj.properties.get(PROPERTIES_PROP)

    @label_properties.setter
    def label_properties(self, v: Optional[List[str]]) -> None:
        self.obj.properties[PROPERTIES_PROP] = v

    @property
    def label_classes(self) -> Optional[List[LabelClasses]]:
        """Gets or set a list of :class:`LabelClasses` defining the list of possible
        class names for each label:properties. (e.g., tree, building, car, hippo).

        Optional, but required if using categorical data."""
        label_classes = self.obj.properties.get(CLASSES_PROP)
        if label_classes is not None:
            return [LabelClasses(classes) for classes in label_classes]
        else:
            return None

    @label_classes.setter
    def label_classes(self, v: Optional[List[LabelClasses]]) -> None:
        if v is None:
            self.obj.properties.pop(CLASSES_PROP, None)
        else:
            if not isinstance(v, list):
                raise pystac.STACError(
                    "label_classes must be a list! Invalid input: {}".format(v)
                )

            classes = [x.to_dict() for x in v]
            self.obj.properties[CLASSES_PROP] = classes

    @property
    def label_tasks(self) -> Optional[List[Union[LabelTask, str]]]:
        """Gets or set a list of tasks these labels apply to. Usually a subset of 'regression',
        'classification', 'detection', or 'segmentation', but may be arbitrary
        values."""
        return self.obj.properties.get(TASKS_PROP)

    @label_tasks.setter
    def label_tasks(self, v: Optional[List[Union[LabelTask, str]]]) -> None:
        if v is None:
            self.obj.properties.pop(TASKS_PROP, None)
        else:
            self.obj.properties[TASKS_PROP] = v

    @property
    def label_methods(self) -> Optional[List[Union[LabelMethod, str]]]:
        """Gets or set a list of methods used for labeling.

        Usually a subset of 'automated' or 'manual', but may be arbitrary values."""
        return self.obj.properties.get("label:methods")

    @label_methods.setter
    def label_methods(self, v: Optional[List[Union[LabelMethod, str]]]) -> None:
        if v is None:
            self.obj.properties.pop("label:methods", None)
        else:
            self.obj.properties["label:methods"] = v

    @property
    def label_overviews(self) -> Optional[List[LabelOverview]]:
        """Gets or set a list of :class:`LabelOverview` instances
        that store counts (for classification-type data) or summary statistics (for
        continuous numerical/regression data)."""
        overviews = self.obj.properties.get(OVERVIEWS_PROP)
        if overviews is not None:
            return [LabelOverview(overview) for overview in overviews]
        else:
            return None

    @label_overviews.setter
    def label_overviews(self, v: Optional[List[LabelOverview]]) -> None:
        if v is None:
            self.obj.properties.pop(OVERVIEWS_PROP, None)
        else:
            self.obj.properties[OVERVIEWS_PROP] = [x.to_dict() for x in v]

    def __repr__(self) -> str:
        return "<LabelItemExt Item id={}>".format(self.obj.id)

    def add_source(
        self,
        source_item: pystac.Item,
        title: Optional[str] = None,
        assets: Optional[List[str]] = None,
    ) -> None:
        """Adds a link to a source item.

        Args:
            source_item : Source imagery that the LabelItem applies to.
            title : Optional title for the link.
            assets : Optional list of assets that determine what
                assets in the source item this label item data applies to.
        """
        extra_fields = None
        if assets is not None:
            extra_fields = {"label:assets": assets}
        link = pystac.Link(
            "source",
            source_item,
            title=title,
            media_type=pystac.MediaType.JSON,
            extra_fields=extra_fields,
        )
        self.obj.add_link(link)

    def get_sources(self) -> Iterable[pystac.Item]:
        """Gets any source items that describe the source imagery used to generate
        this LabelItem.

        Returns:
            A possibly empty list of source imagery items. Determined by links of this
            LabelItem that have ``rel=='source'``.
        """
        return map(lambda x: cast(pystac.Item, x), self.obj.get_stac_objects("source"))

    def add_labels(
        self,
        href: str,
        title: Optional[str] = None,
        media_type: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Adds a label asset to this LabelItem.

        Args:
            href : Link to the asset object. Relative and absolute links are both
                allowed.
            title : Optional displayed title for clients and users.
            media_type : Optional description of the media type. Registered Media
                Types are preferred. See :class:`~pystac.MediaType` for common
                media types.
            properties : Optional, additional properties for this asset. This is
                used by extensions as a way to serialize and deserialize properties on
                asset object JSON.
        """

        self.obj.add_asset(
            "labels",
            pystac.Asset(
                href=href, title=title, media_type=media_type, extra_fields=properties
            ),
        )

    def add_geojson_labels(
        self,
        href: str,
        title: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Adds a GeoJSON label asset to this LabelItem.

        Args:
            href : Link to the asset object. Relative and absolute links are both
                allowed.
            title : Optional displayed title for clients and users.
            properties : Optional, additional properties for this asset. This is
                used by extensions as a way to serialize and deserialize properties on
                asset object JSON.
        """
        self.add_labels(
            href,
            title=title,
            properties=properties,
            media_type=pystac.MediaType.GEOJSON,
        )

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: pystac.Item, add_if_missing: bool = False) -> "LabelExtension":
        """Extends the given STAC Object with properties from the :stac-ext:`Label
        Extension <label>`.

        This extension can be applied to instances of :class:`~pystac.Item`.
        """
        if isinstance(obj, pystac.Item):
            cls.validate_has_extension(obj, add_if_missing)
            return cls(obj)
        else:
            raise pystac.ExtensionTypeError(
                f"Label extension does not apply to type '{type(obj).__name__}'"
            )

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> "SummariesLabelExtension":
        """Returns the extended summaries object for the given collection."""
        cls.validate_has_extension(obj, add_if_missing)
        return SummariesLabelExtension(obj)


class SummariesLabelExtension(SummariesExtension):
    """A concrete implementation of :class:`~SummariesExtension` that extends
    the ``summaries`` field of a :class:`~pystac.Collection` to include properties
    defined in the :stac-ext:`Label Extension <label>`.
    """

    @property
    def label_properties(self) -> Optional[List[str]]:
        """Get or sets the summary of :attr:`LabelExtension.label_properties` values
        for this Collection.
        """

        return self.summaries.get_list(PROPERTIES_PROP)

    @label_properties.setter
    def label_properties(self, v: Optional[List[str]]) -> None:
        self._set_summary(PROPERTIES_PROP, v)

    @property
    def label_classes(self) -> Optional[List[LabelClasses]]:
        """Get or sets the summary of :attr:`LabelExtension.label_classes` values
        for this Collection.
        """

        return map_opt(
            lambda classes: [LabelClasses(c) for c in classes],
            self.summaries.get_list(CLASSES_PROP),
        )

    @label_classes.setter
    def label_classes(self, v: Optional[List[LabelClasses]]) -> None:
        self._set_summary(
            CLASSES_PROP, map_opt(lambda classes: [c.to_dict() for c in classes], v)
        )

    @property
    def label_type(self) -> Optional[List[LabelType]]:
        """Get or sets the summary of :attr:`LabelExtension.label_type` values
        for this Collection.
        """

        return self.summaries.get_list(TYPE_PROP)

    @label_type.setter
    def label_type(self, v: Optional[List[LabelType]]) -> None:
        self._set_summary(TYPE_PROP, v)

    @property
    def label_tasks(self) -> Optional[List[Union[LabelTask, str]]]:
        """Get or sets the summary of :attr:`LabelExtension.label_tasks` values
        for this Collection.
        """

        return self.summaries.get_list(TASKS_PROP)

    @label_tasks.setter
    def label_tasks(self, v: Optional[List[Union[LabelTask, str]]]) -> None:
        self._set_summary(TASKS_PROP, v)

    @property
    def label_methods(self) -> Optional[List[Union[LabelMethod, str]]]:
        """Get or sets the summary of :attr:`LabelExtension.label_methods` values
        for this Collection.
        """

        return self.summaries.get_list(METHODS_PROP)

    @label_methods.setter
    def label_methods(self, v: Optional[List[Union[LabelMethod, str]]]) -> None:
        self._set_summary(METHODS_PROP, v)


class LabelExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {
        "label",
        "https://stac-extensions.github.io/label/v1.0.0/schema.json",
    }
    stac_object_types = {pystac.STACObjectType.ITEM}

    def get_object_links(
        self, so: pystac.STACObject
    ) -> Optional[List[Union[str, pystac.RelType]]]:
        if isinstance(so, pystac.Item):
            return [LabelRelType.SOURCE]
        return None

    def migrate(
        self, obj: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        if info.object_type == pystac.STACObjectType.ITEM and version < "1.0.0":
            props = obj["properties"]
            # Migrate 0.8.0-rc1 non-pluralized forms
            # As it's a common mistake, convert for any pre-1.0.0 version.
            if "label:property" in props and PROPERTIES_PROP not in props:
                props[PROPERTIES_PROP] = props["label:property"]
                del props["label:property"]

            if "label:task" in props and TASKS_PROP not in props:
                props[TASKS_PROP] = props["label:task"]
                del props["label:task"]

            if "label:overview" in props and OVERVIEWS_PROP not in props:
                props[OVERVIEWS_PROP] = props["label:overview"]
                del props["label:overview"]

            if "label:method" in props and "label:methods" not in props:
                props["label:methods"] = props["label:method"]
                del props["label:method"]

        super().migrate(obj, version, info)


LABEL_EXTENSION_HOOKS: ExtensionHooks = LabelExtensionHooks()
