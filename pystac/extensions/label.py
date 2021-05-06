"""Implements the Label extension.

https://github.com/stac-extensions/label
"""

from enum import Enum
from pystac.extensions.base import ExtensionManagementMixin
from typing import Any, Dict, Iterable, List, Optional, Set, Union, cast

import pystac
from pystac.serialization.identify import STACJSONDescription, STACVersionID
from pystac.extensions.hooks import ExtensionHooks

SCHEMA_URI = "https://stac-extensions.github.io/label/v1.0.0/schema.json"


class LabelType(str, Enum):
    """Enumerates valid label types (RASTER or VECTOR)."""

    def __str__(self) -> str:
        return str(self.value)

    VECTOR = "vector"
    RASTER = "raster"

    ALL = [VECTOR, RASTER]
    """Convenience attribute for checking if values are valid label types"""


class LabelClasses:
    """Defines the list of possible class names (e.g., tree, building, car, hippo)

    Use LabelClasses.create to create a new instance of LabelClasses from
    property values.
    """

    def __init__(self, properties: Dict[str, Any]):
        self.properties = properties

    def apply(
        self,
        classes: Union[List[str], List[int], List[float]],
        name: Optional[str] = None,
    ) -> None:
        """Sets the properties for this LabelClasses.

        Args:
            classes (List[str] or List[int] or List[float]): The different possible
                class values.
            name (str): The property key within the asset's each Feature corresponding
                to class labels. If labels are raster-formatted, do not supply;
                required otherwise.
        """
        self.classes = classes
        self.name = name

    @classmethod
    def create(
        cls,
        classes: Union[List[str], List[int], List[float]],
        name: Optional[str] = None,
    ) -> "LabelClasses":
        """Creates a new LabelClasses.

        Args:
            classes (List[str] or List[int] or List[float]): The different possible
                class values.
            name (str): The property key within the asset's each Feature corresponding
                to class labels. If labels are raster-formatted, do not supply;
                required otherwise.

        Returns:
            LabelClasses
        """
        c = cls({})
        c.apply(classes, name)
        return c

    @property
    def classes(self) -> Union[List[str], List[int], List[float]]:
        """Get or sets the class values.

        Returns:
            List[str] or List[int] or List[float]
        """
        result = self.properties.get("classes")
        if result is None:
            raise pystac.STACError(
                f"LabelClasses does not contain classes property: {self.properties}"
            )
        return result

    @classes.setter
    def classes(self, v: Union[List[str], List[int], List[float]]) -> None:
        if not type(v) is list:
            raise pystac.STACError(
                "classes must be a list! Invalid input: {}".format(v)
            )

        self.properties["classes"] = v

    @property
    def name(self) -> Optional[str]:
        """Get or sets the property key within the asset's each Feature corresponding to
        class labels. If labels are raster-formatted, do not supply; required otherwise.
        """
        return self.properties.get("name")

    @name.setter
    def name(self, v: Optional[str]) -> None:
        if v is not None:
            self.properties["name"] = v
        else:
            self.properties.pop("name", None)

    def __repr__(self) -> str:
        return "<LabelClasses classes={}>".format(
            ",".join([str(x) for x in self.classes])
        )

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of this LabelClasses.

        Returns:
            dict: The wrapped dict of the LabelClasses that can be written out as JSON.
        """
        return self.properties


class LabelCount:
    """Contains counts for categorical data.

    Use LabelCount.create to create a new LabelCount
    """

    def __init__(self, properties: Dict[str, Any]):
        self.properties = properties

    def apply(self, name: str, count: int) -> None:
        """Sets the properties for this LabelCount.

        Args:
            name (str): One of the different possible classes within the property.
            count (int): The number of occurrences of the class.
        """
        self.name = name
        self.count = count

    @classmethod
    def create(cls, name: str, count: int) -> "LabelCount":
        """Creates a LabelCount.

        Args:
            name (str): One of the different possible classes within the property.
            count (int): The number of occurrences of the class.
        """
        x = cls({})
        x.apply(name, count)
        return x

    @property
    def name(self) -> str:
        """Get or sets the class that this count represents.

        Returns:
            str
        """
        result = self.properties.get("name")
        if result is None:
            raise pystac.STACError(
                f"Label count has no name property: {self.properties}"
            )
        return result

    @name.setter
    def name(self, v: str) -> None:
        self.properties["name"] = v

    @property
    def count(self) -> int:
        """Get or sets the number of occurrences of the class.

        Returns:
            int
        """
        result = self.properties.get("count")
        if result is None:
            raise pystac.STACError(
                f"Label count has no count property: {self.properties}"
            )
        return result

    @count.setter
    def count(self, v: int) -> None:
        self.properties["count"] = v

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of this LabelCount.

        Returns:
            dict: The wrapped dict of the LabelCount that can be written out as JSON.
        """
        return {"name": self.name, "count": self.count}


class LabelStatistics:
    """Contains statistics for regression/continuous numeric value data.

    Use LabelStatistics.create to create a new instance.
    """

    def __init__(self, properties: Dict[str, Any]) -> None:
        self.properties = properties

    def apply(self, name: str, value: float) -> None:
        """Sets the property values for this instance.

        Args:
            name (str): The name of the statistic being reported.
            value (float): The value of the statistic
        """
        self.name = name
        self.value = value

    @classmethod
    def create(cls, name: str, value: float) -> "LabelStatistics":
        """Sets the property values for this instance.

        Args:
            name (str): The name of the statistic being reported.
            value (float): The value of the statistic
        """
        x = cls({})
        x.apply(name, value)
        return x

    @property
    def name(self) -> str:
        """Get or sets the name of the statistic being reported.

        Returns:
            str
        """
        result = self.properties.get("name")
        if result is None:
            raise pystac.STACError(
                f"Label statistics has no name property: {self.properties}"
            )
        return result

    @name.setter
    def name(self, v: str) -> None:
        self.properties["name"] = v

    @property
    def value(self) -> float:
        """Get or sets the value of the statistic

        Returns:
            float
        """
        result = self.properties.get("value")
        if result is None:
            raise pystac.STACError(
                f"Label statistics has no value property: {self.properties}"
            )
        return result

    @value.setter
    def value(self, v: float) -> None:
        self.properties["value"] = v

    def to_dict(self) -> Dict[str, Any]:
        """Returns the dictionary representing the JSON of this LabelStatistics.

        Returns:
            dict: The wrapped dict of the LabelStatistics that can be written out as
            JSON.
        """
        return {"name": self.name, "value": self.value}


class LabelOverview:
    """Stores counts (for classification-type data) or summary statistics (for
    continuous numerical/regression data).

    Use LabelOverview.create to create a new LabelOverview.
    """

    def __init__(self, properties: Dict[str, Any]):
        self.properties = properties

    def apply(
        self,
        property_key: Optional[str],
        counts: Optional[List[LabelCount]] = None,
        statistics: Optional[List[LabelStatistics]] = None,
    ) -> None:
        """Sets the properties for this LabelOverview.

        Either ``counts`` or ``statistics``, or both, can be placed in an overview;
        at least one is required.

        Args:
            property_key (str): The property key within the asset corresponding to
                class labels that these counts or statistics are referencing. If the
                label data is raster data, this should be None.
            counts: Optional list of LabelCounts containing counts
                for categorical data.
            statistics: Optional list of statistics containing statistics for
                regression/continuous numeric value data.
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
        """Creates a new LabelOverview.

        Either ``counts`` or ``statistics``, or both, can be placed in an overview;
        at least one is required.

        Args:
            property_key (str): The property key within the asset corresponding to
                class labels.
            counts: Optional list of LabelCounts containing counts for
                categorical data.
            statistics: Optional list of Statistics containing statistics for
                regression/continuous numeric value data.
        """
        x = LabelOverview({})
        x.apply(property_key, counts, statistics)
        return x

    @property
    def property_key(self) -> Optional[str]:
        """Get or sets the property key within the asset corresponding to class labels.

        Returns:
            str
        """
        return self.properties.get("property_key")

    @property_key.setter
    def property_key(self, v: Optional[str]) -> None:
        self.properties["property_key"] = v

    @property
    def counts(self) -> Optional[List[LabelCount]]:
        """Get or sets the list of LabelCounts containing counts for categorical data.

        Returns:
            List[LabelCount]
        """
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
        """Get or sets the list of Statistics containing statistics for
        regression/continuous numeric value data.

        Returns:
            List[Statistics]
        """
        statistics = self.properties.get("statistics")
        if statistics is None:
            return None

        return [LabelStatistics(s) for s in statistics]

    @statistics.setter
    def statistics(self, v: Optional[List[LabelStatistics]]) -> None:
        if v is None:
            self.properties.pop("statistics", None)
        else:
            if not isinstance(v, list):
                raise pystac.STACError(
                    "statistics must be a list! Invalid input: {}".format(v)
                )

            self.properties["statistics"] = [s.to_dict() for s in v]

    def merge_counts(self, other: "LabelOverview") -> "LabelOverview":
        """Merges the counts associated with this overview with another overview.
        Creates a new LabelOverview.

        Args:
            other (LabelOverview): The other LabelOverview to merge.

        Returns:
            LabelOverview: A new LabelOverview with the counts merged. This will
            drop any statistics associated with either of the LabelOverviews.
        """
        assert self.property_key == other.property_key

        new_counts = None
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
        """Returns the dictionary representing the JSON of this LabelOverview.

        Returns:
            dict: The wrapped dict of the LabelOverview that can be written out as JSON.
        """
        return self.properties


class LabelExtension(ExtensionManagementMixin[pystac.Item]):
    """A LabelItemExt is the extension of the Item in the label extension which
    represents a polygon, set of polygons, or raster data defining
    labels and label metadata and should be part of a Collection.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The Item that is being extended.

    See:
        `Item fields in the label extension spec <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/label#item-fields>`_

    Note:
        Using LabelItemExt to directly wrap an item will add the 'label' extension ID to
        the item's stac_extensions.
    """  # noqa E501

    def __init__(self, item: pystac.Item) -> None:
        self.obj = item
        self.schema_uri = SCHEMA_URI

    def apply(
        self,
        label_description: str,
        label_type: LabelType,
        label_properties: Optional[List[str]] = None,
        label_classes: Optional[List[LabelClasses]] = None,
        label_tasks: Optional[List[str]] = None,
        label_methods: Optional[List[str]] = None,
        label_overviews: Optional[List[LabelOverview]] = None,
    ) -> None:
        """Applies label extension properties to the extended Item.

        Args:
            label_description (str): A description of the label, how it was created,
                and what it is recommended for
            label_type (str): An ENUM of either vector label type or raster label type. Use
                one of :class:`~pystac.LabelType`.
            label_properties (list or None): These are the names of the property field(s) in each
                Feature of the label asset's FeatureCollection that contains the classes
                (keywords from label:classes if the property defines classes).
                If labels are rasters, this should be None.
            label_classes (List[LabelClass]): Optional, but required if using categorical data.
                A list of LabelClasses defining the list of possible class names for each
                label:properties. (e.g., tree, building, car, hippo)
            label_tasks (List[str]): Recommended to be a subset of 'regression', 'classification',
                'detection', or 'segmentation', but may be an arbitrary value.
            label_methods: Recommended to be a subset of 'automated' or 'manual',
                but may be an arbitrary value.
            label_overviews (List[LabelOverview]): Optional list of LabelOverview classes
                that store counts (for classification-type data) or summary statistics (for
                continuous numerical/regression data).
        """  # noqa E501
        self.label_description = label_description
        self.label_type = label_type
        self.label_properties = label_properties
        self.label_classes = label_classes
        self.label_tasks = label_tasks
        self.label_methods = label_methods
        self.label_overviews = label_overviews

    @property
    def label_description(self) -> str:
        """Get or sets a description of the label, how it was created,
        and what it is recommended for.

        Returns:
            str
        """
        result = self.obj.properties.get("label:description")
        if result is None:
            raise pystac.STACError(f"label:description not set for item {self.obj.id}")
        return result

    @label_description.setter
    def label_description(self, v: str) -> None:
        self.obj.properties["label:description"] = v

    @property
    def label_type(self) -> LabelType:
        """Gets or sets an ENUM of either vector label type or raster label type."""
        result = self.obj.properties.get("label:type")
        if result is None:
            raise pystac.STACError(f"label:type is not set for item {self.obj.id}")
        return LabelType(result)

    @label_type.setter
    def label_type(self, v: LabelType) -> None:
        if v not in LabelType.ALL:
            raise pystac.STACError(
                "label_type must be one of "
                "{}. Invalid input: {}".format(LabelType.ALL, v)
            )

        self.obj.properties["label:type"] = v

    @property
    def label_properties(self) -> Optional[List[str]]:
        """Label Properties

        Gets or sets the names of the property field(s) in each
        Feature of the label asset's FeatureCollection that contains the classes
        (keywords from label:classes if the property defines classes).
        If labels are rasters, this should be None.

        Returns:
            List[str] or None
        """
        return self.obj.properties.get("label:properties")

    @label_properties.setter
    def label_properties(self, v: Optional[List[str]]) -> None:
        if v is not None:
            if not isinstance(v, list):
                raise pystac.STACError(
                    "label_properties must be a list! Invalid input: {}".format(v)
                )

        self.obj.properties["label:properties"] = v

    @property
    def label_classes(self) -> Optional[List[LabelClasses]]:
        """Get or set a list of LabelClasses defining the list of possible class names for each
        label:properties. (e.g., tree, building, car, hippo).

        Optional, but required if using categorical data.

        Returns:
            List[LabelClasses] or None
        """
        label_classes = self.obj.properties.get("label:classes")
        if label_classes is not None:
            return [LabelClasses(classes) for classes in label_classes]
        else:
            return None

    @label_classes.setter
    def label_classes(self, v: Optional[List[LabelClasses]]) -> None:
        if v is None:
            self.obj.properties.pop("label:classes", None)
        else:
            if not isinstance(v, list):
                raise pystac.STACError(
                    "label_classes must be a list! Invalid input: {}".format(v)
                )

            classes = [x.to_dict() for x in v]
            self.obj.properties["label:classes"] = classes

    @property
    def label_tasks(self) -> Optional[List[str]]:
        """Get or set a list of tasks these labels apply to. Usually a subset of 'regression',
            'classification', 'detection', or 'segmentation', but may be arbitrary
            values.

        Returns:
            List[str] or None
        """
        return self.obj.properties.get("label:tasks")

    @label_tasks.setter
    def label_tasks(self, v: Optional[List[str]]) -> None:
        if v is None:
            self.obj.properties.pop("label:tasks", None)
        else:
            if not isinstance(v, list):
                raise pystac.STACError(
                    "label_tasks must be a list! Invalid input: {}".format(v)
                )

            self.obj.properties["label:tasks"] = v

    @property
    def label_methods(self) -> Optional[List[str]]:
        """Get or set a list of methods used for labeling.

        Usually a subset of 'automated' or 'manual', but may be arbitrary values.

        Returns:
            List[str] or None
        """
        return self.obj.properties.get("label:methods")

    @label_methods.setter
    def label_methods(self, v: Optional[List[str]]) -> None:
        if v is None:
            self.obj.properties.pop("label:methods", None)
        else:
            if not isinstance(v, list):
                raise pystac.STACError(
                    "label_methods must be a list! Invalid input: {}".format(v)
                )

            self.obj.properties["label:methods"] = v

    @property
    def label_overviews(self) -> Optional[List[LabelOverview]]:
        """Get or set a list of LabelOverview classes
        that store counts (for classification-type data) or summary statistics (for
        continuous numerical/regression data).

        Returns:
            List[LabelOverview] or None
        """
        overviews = self.obj.properties.get("label:overviews")
        if overviews is not None:
            return [LabelOverview(overview) for overview in overviews]
        else:
            return None

    @label_overviews.setter
    def label_overviews(self, v: Optional[List[LabelOverview]]) -> None:
        if v is None:
            self.obj.properties.pop("label:overviews", None)
        else:
            if not isinstance(v, list):
                raise pystac.STACError(
                    "label_overviews must be a list! Invalid input: {}".format(v)
                )

            overviews = [x.to_dict() for x in v]
            self.obj.properties["label:overviews"] = overviews

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
            source_item (Item): Source imagery that the LabelItem applies to.
            title (str): Optional title for the link.
            assets (List[str]): Optional list of assets that determine what
                assets in the source item this label item data applies to.
        """
        properties = None
        if assets is not None:
            properties = {"label:assets": assets}
        link = pystac.Link(
            "source",
            source_item,
            title=title,
            media_type="application/json",
            properties=properties,
        )
        self.obj.add_link(link)

    def get_sources(self) -> Iterable[pystac.Item]:
        """Gets any source items that describe the source imagery used to generate
        this LabelItem.

        Returns:
            Generator[Items]: A possibly empty list of source imagery items. Determined
            by links of this LabelItem that have ``rel=='source'``.
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
            href (str): Link to the asset object. Relative and absolute links are both
                allowed.
            title (str): Optional displayed title for clients and users.
            media_type (str): Optional description of the media type. Registered Media
                Types are preferred. See :class:`~pystac.MediaType` for common
                media types.
            properties (dict): Optional, additional properties for this asset. This is
                used by extensions as a way to serialize and deserialize properties on
                asset object JSON.
        """

        self.obj.add_asset(
            "labels",
            pystac.Asset(
                href=href, title=title, media_type=media_type, properties=properties
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
            href (str): Link to the asset object. Relative and absolute links are both
                allowed.
            title (str): Optional displayed title for clients and users.
            properties (dict): Optional, additional properties for this asset. This is
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
    def ext(cls, obj: pystac.Item) -> "LabelExtension":
        return cls(obj)


class LabelExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: Set[str] = set(["label"])
    stac_object_types: Set[pystac.STACObjectType] = set([pystac.STACObjectType.ITEM])

    def get_object_links(self, so: pystac.STACObject) -> Optional[List[str]]:
        if isinstance(so, pystac.Item):
            return ["source"]
        return None

    def migrate(
        self, obj: Dict[str, Any], version: STACVersionID, info: STACJSONDescription
    ) -> None:
        if info.object_type == pystac.STACObjectType.ITEM and version < "1.0.0":
            props = obj["properties"]
            # Migrate 0.8.0-rc1 non-pluralized forms
            # As it's a common mistake, convert for any pre-1.0.0 version.
            if "label:property" in props and "label:properties" not in props:
                props["label:properties"] = props["label:property"]
                del props["label:property"]

            if "label:task" in props and "label:tasks" not in props:
                props["label:tasks"] = props["label:task"]
                del props["label:task"]

            if "label:overview" in props and "label:overviews" not in props:
                props["label:overviews"] = props["label:overview"]
                del props["label:overview"]

            if "label:method" in props and "label:methods" not in props:
                props["label:methods"] = props["label:method"]
                del props["label:method"]

        super().migrate(obj, version, info)


LABEL_EXTENSION_HOOKS: ExtensionHooks = LabelExtensionHooks()
