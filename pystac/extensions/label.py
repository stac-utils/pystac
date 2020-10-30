"""STAC Model classes for Label extension.
"""
from pystac import STACError
from pystac.extensions import Extensions
from pystac.extensions.base import (ItemExtension, ExtensionDefinition, ExtendedObject)
from pystac.item import (Item, Asset)
from pystac.link import Link


class LabelType:
    """Enumerates valid label types (RASTER or VECTOR)."""
    VECTOR = 'vector'
    RASTER = 'raster'

    ALL = [VECTOR, RASTER]
    """Convenience attribute for checking if values are valid label types"""


class LabelItemExt(ItemExtension):
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
    """ # noqa E501

    def __init__(self, item):
        if item.stac_extensions is None:
            item.stac_extensions = [Extensions.LABEL]
        elif Extensions.LABEL not in item.stac_extensions:
            item.stac_extensions.append(Extensions.LABEL)

        self.item = item

    def apply(self,
              label_description,
              label_type,
              label_properties=None,
              label_classes=None,
              label_tasks=None,
              label_methods=None,
              label_overviews=None):
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
            label_classes (List[LabelClass]): Optional, but reqiured if ussing categorical data.
                A list of LabelClasses defining the list of possible class names for each
                label:properties. (e.g., tree, building, car, hippo)
            label_tasks (List[str]): Recommended to be a subset of 'regression', 'classification',
                'detection', or 'segmentation', but may be an arbitrary value.
            label_methods: Recommended to be a subset of 'automated' or 'manual',
                but may be an arbitrary value.
            label_overviews (List[LabelOverview]): Optional list of LabelOverview classes
                that store counts (for classification-type data) or summary statistics (for
                continuous numerical/regression data).
        """ # noqa E501
        self.label_description = label_description
        self.label_type = label_type
        self.label_properties = label_properties
        self.label_classes = label_classes
        self.label_tasks = label_tasks
        self.label_methods = label_methods
        self.label_overviews = label_overviews

    @property
    def label_description(self):
        """Get or sets a description of the label, how it was created,
        and what it is recommended for.

        Returns:
            str
        """
        return self.item.properties.get('label:description')

    @label_description.setter
    def label_description(self, v):
        self.item.properties['label:description'] = v

    @property
    def label_type(self):
        """Gets or sets an ENUM of either vector label type or raster label type (one
        of :class:`~pystac.LabelType`).

        Returns:
            str
        """
        return self.item.properties.get('label:type')

    @label_type.setter
    def label_type(self, v):
        if v not in LabelType.ALL:
            raise STACError("label_type must be one of "
                            "{}. Invalid input: {}".format(LabelType.ALL, v))

        self.item.properties['label:type'] = v

    @property
    def label_properties(self):
        """Label Properties

        Gets or sets the names of the property field(s) in each
        Feature of the label asset's FeatureCollection that contains the classes
        (keywords from label:classes if the property defines classes).
        If labels are rasters, this should be None.

        Returns:
            List[str] or None
        """
        return self.item.properties.get('label:properties')

    @label_properties.setter
    def label_properties(self, v):
        if v is not None:
            if not type(v) is list:
                raise STACError("label_properties must be a list! Invalid input: {}".format(v))

        self.item.properties['label:properties'] = v

    @property
    def label_classes(self):
        """Get or set a list of LabelClasses defining the list of possible class names for each
        label:properties. (e.g., tree, building, car, hippo).

        Optional, but reqiured if using categorical data.

        Returns:
            List[LabelClasses] or None
        """
        label_classes = self.item.properties.get('label:classes')
        if label_classes is not None:
            return [LabelClasses(classes) for classes in label_classes]
        else:
            return None

    @label_classes.setter
    def label_classes(self, v):
        if v is None:
            self.item.properties.pop('label:classes', None)
        else:
            if not type(v) is list:
                raise STACError("label_classes must be a list! Invalid input: {}".format(v))

            classes = [x.to_dict() for x in v]
            self.item.properties['label:classes'] = classes

    @property
    def label_tasks(self):
        """Get or set a list of tasks these labels apply to. Usually a subset of 'regression',
            'classification', 'detection', or 'segmentation', but may be arbitrary values.

        Returns:
            List[str] or None
        """
        return self.item.properties.get('label:tasks')

    @label_tasks.setter
    def label_tasks(self, v):
        if v is None:
            self.item.properties.pop('label:tasks', None)
        else:
            if not type(v) is list:
                raise STACError("label_tasks must be a list! Invalid input: {}".format(v))

            self.item.properties['label:tasks'] = v

    @property
    def label_methods(self):
        """Get or set a list of methods used for labeling. Usually a subset of 'automated' or 'manual',
            but may be arbitrary values.

        Returns:
            List[str] or None
        """
        return self.item.properties.get('label:methods')

    @label_methods.setter
    def label_methods(self, v):
        if v is None:
            self.item.properties.pop('label:methods', None)
        else:
            if not type(v) is list:
                raise STACError("label_methods must be a list! Invalid input: {}".format(v))

            self.item.properties['label:methods'] = v

    @property
    def label_overviews(self):
        """Get or set a list of LabelOverview classes
        that store counts (for classification-type data) or summary statistics (for
        continuous numerical/regression data).

        Returns:
            List[LabelOverview] or None
        """
        overviews = self.item.properties.get('label:overviews')
        if overviews is not None:
            return [LabelOverview(overview) for overview in overviews]
        else:
            return None

    @label_overviews.setter
    def label_overviews(self, v):
        if v is None:
            self.item.properties.pop('label:overviews', None)
        else:
            if not type(v) is list:
                raise STACError("label_overviews must be a list! Invalid input: {}".format(v))

            overviews = [x.to_dict() for x in v]
            self.item.properties['label:overviews'] = overviews

    def __repr__(self):
        return '<LabelItemExt Item id={}>'.format(self.item.id)

    def add_source(self, source_item, title=None, assets=None):
        """Adds a link to a source item.

        Args:
            source_item (Item): Source imagery that the LabelItem applies to.
            title (str): Optional title for the link.
            assets (List[str]): Optional list of assets that determine what
                assets in the source item this label item data applies to.
        """
        properties = None
        if assets is not None:
            properties = {'label:assets': assets}
        link = Link('source',
                    source_item,
                    title=title,
                    media_type='application/json',
                    properties=properties)
        self.item.add_link(link)

    def get_sources(self):
        """Gets any source items that describe the source imagery used to generate
        this LabelItem.

        Returns:
            Generator[Items]: A possibly empty list of source imagery items. Determined by
            links of this LabelItem that have ``rel=='source'``.
        """
        return self.item.get_stac_objects('source')

    def add_labels(self, href, title=None, media_type=None, properties=None):
        """Adds a label asset to this LabelItem.

        Args:
            href (str): Link to the asset object. Relative and absolute links are both allowed.
            title (str): Optional displayed title for clients and users.
            media_type (str): Optional description of the media type. Registered Media Types
               are preferred. See :class:`~pystac.MediaType` for common media types.
            properties (dict): Optional, additional properties for this asset. This is used by
                extensions as a way to serialize and deserialize properties on asset
                object JSON.
        """

        self.item.add_asset(
            "labels", Asset(href=href, title=title, media_type=media_type, properties=properties))

    def add_geojson_labels(self, href, title=None, properties=None):
        """Adds a GeoJSON label asset to this LabelItem.

        Args:
            href (str): Link to the asset object. Relative and absolute links are both allowed.
            title (str): Optional displayed title for clients and users.
            properties (dict): Optional, additional properties for this asset. This is used by
                extensions as a way to serialize and deserialize properties on asset
                object JSON.
        """
        self.add_labels(href, title=title, properties=properties, media_type='application/geo+json')

    @classmethod
    def _object_links(cls):
        return ['source']

    @classmethod
    def from_item(cls, item):
        return cls(item)


class LabelClasses:
    """Defines the list of possible class names (e.g., tree, building, car, hippo)

    Use LabelClasses.create to create a new instance of LabelClasses from property values.
    """
    def __init__(self, properties):
        self.properties = properties

    def apply(self, classes, name=None):
        """Sets the properties for this LabelClasses.

        Args:
            classes (List[str] or List[int] or List[float]): The different possible class values.
            name (str): The property key within the asset's each Feature corresponding to
                class labels. If labels are raster-formatted, do not supply; required otherwise.
        """
        self.classes = classes
        self.name = name

    @classmethod
    def create(cls, classes, name=None):
        """Creates a new LabelClasses.

        Args:
            classes (List[str] or List[int] or List[float]): The different possible class values.
            name (str): The property key within the asset's each Feature corresponding to
                class labels. If labels are raster-formatted, do not supply; required otherwise.

        Returns:
            LabelClasses
        """
        c = cls({})
        c.apply(classes, name)
        return c

    @property
    def classes(self):
        """Get or sets the class values.

        Returns:
            List[str] or List[int] or List[float]
        """
        return self.properties.get('classes')

    @classes.setter
    def classes(self, v):
        if not type(v) is list:
            raise STACError("classes must be a list! Invalid input: {}".format(v))

        self.properties['classes'] = v

    @property
    def name(self):
        """Get or sets the property key within the asset's each Feature corresponding to
        class labels. If labels are raster-formatted, do not supply; required otherwise.

        Returns:
            str
        """
        return self.properties.get('name')

    @name.setter
    def name(self, v):
        if v is not None:
            self.properties['name'] = v
        else:
            self.properties.pop('name', None)

    def __repr__(self):
        return '<LabelClasses classes={}>'.format(','.join(self.classes))

    def to_dict(self):
        """Returns the dictionary representing the JSON of this LabelClasses.

        Returns:
            dict: The wrapped dict of the LabelClasses that can be written out as JSON.
        """
        return self.properties


class LabelOverview:
    """Stores counts (for classification-type data) or summary statistics (for
    continuous numerical/regression data).

    Use LabelOverview.create to create a new LabelOverview.
    """
    def __init__(self, properties):
        self.properties = properties

    def apply(self, property_key, counts=None, statistics=None):
        """Sets the properties for this LabelOverview.

        Either ``counts`` or ``statistics``, or both, can be placed in an overview;
        at least one is required.

        Args:
            property_key (str): The property key within the asset corresponding to class labels.
            counts (List[LabelCounts]): Optional list of LabelCounts containing counts
                for categorical data.
            statistics (List[Statistics]): Optional list of Statistics containing statistics for
                regression/continuous numeric value data.
        """
        self.property_key = property_key
        self.counts = counts
        self.statistics = statistics

    @classmethod
    def create(cls, property_key, counts=None, statistics=None):
        """Creates a new LabelOverview.

        Either ``counts`` or ``statistics``, or both, can be placed in an overview;
        at least one is required.

        Args:
            property_key (str): The property key within the asset corresponding to class labels.
            counts (List[LabelCounts]): Optional list of LabelCounts containing counts for
                categorical data.
            statistics (List[Statistics]): Optional list of Statistics containing statistics for
                regression/continuous numeric value data.
        """
        x = LabelOverview({})
        x.apply(property_key, counts, statistics)
        return x

    @property
    def property_key(self):
        """Get or sets the property key within the asset corresponding to class labels.

        Returns:
            str
        """
        return self.properties.get('property_key')

    @property_key.setter
    def property_key(self, v):
        self.properties['property_key'] = v

    @property
    def counts(self):
        """Get or sets the list of LabelCounts containing counts for categorical data.

        Returns:
            List[LabelCount]
        """
        counts = self.properties.get('counts')
        if counts is not None:
            counts = [LabelCount(c) for c in counts]
        return counts

    @counts.setter
    def counts(self, v):
        if v is None:
            self.properties.pop('counts', None)
        else:
            if not type(v) is list:
                raise STACError("counts must be a list! Invalid input: {}".format(v))

            self.properties['counts'] = [c.to_dict() for c in v]

    @property
    def statistics(self):
        """Get or sets the list of Statistics containing statistics for
        regression/continuous numeric value data.

        Returns:
            List[Statistics]
        """
        statistics = self.properties.get('statistics')
        if statistics is not None:
            statistics = [LabelStatistics(s) for s in statistics]

        return statistics

    @statistics.setter
    def statistics(self, v):
        if v is None:
            self.properties.pop('statistics', None)
        else:
            if not type(v) is list:
                raise STACError("statistics must be a list! Invalid input: {}".format(v))

            self.properties['statistics'] = [s.to_dict() for s in v]

    def merge_counts(self, other):
        """Merges the counts associated with this overview with another overview.
        Creates a new LabelOverview.

        Args:
            other (LabelOverview): The other LabelOverview to merge.

        Returns:
            LabelOverview: A new LabelOverview with the counts merged. This will
            drop any statistics associated with either of the LabelOverviews.
        """
        assert (self.property_key == other.property_key)

        new_counts = None
        if self.counts is None:
            new_counts = other.counts
        else:
            if other.counts is None:
                new_counts = self.counts
            else:
                count_by_prop = {}

                def add_counts(counts):
                    for c in counts:
                        if c.name not in count_by_prop:
                            count_by_prop[c.name] = c.count
                        else:
                            count_by_prop[c.name] += c.count

                add_counts(self.counts)
                add_counts(other.counts)
                new_counts = [LabelCount(k, v) for k, v in count_by_prop.items()]
        return LabelOverview.create(self.property_key, counts=new_counts)

    def to_dict(self):
        """Returns the dictionary representing the JSON of this LabelOverview.

        Returns:
            dict: The wrapped dict of the LabelOverview that can be written out as JSON.
        """
        return self.properties


class LabelCount:
    """Contains counts for categorical data.

    Use LabelCount.create to create a new LabelCount
    """
    def __init__(self, properties):
        self.properties = properties

    def apply(self, name, count):
        """Sets the properties for this LabelCount.

        Args:
            name (str): One of the different possible classes within the property.
            count (int): The number of occurrences of the class.
        """
        self.name = name
        self.count = count

    @classmethod
    def create(cls, name, count):
        """Creates a LabelCount.

        Args:
            name (str): One of the different possible classes within the property.
            count (int): The number of occurrences of the class.
        """
        x = cls({})
        x.apply(name, count)
        return x

    @property
    def name(self):
        """Get or sets the class that this count represents.

        Returns:
            str
        """
        return self.properties.get('name')

    @name.setter
    def name(self, v):
        self.properties['name'] = v

    @property
    def count(self):
        """Get or sets the number of occurrences of the class.

        Returns:
            int
        """
        return self.properties.get('count')

    @count.setter
    def count(self, v):
        self.properties['count'] = v

    def to_dict(self):
        """Returns the dictionary representing the JSON of this LabelCount.

        Returns:
            dict: The wrapped dict of the LabelCount that can be written out as JSON.
        """
        return {'name': self.name, 'count': self.count}


class LabelStatistics:
    """Contains statistics for regression/continuous numeric value data.

    Use LabelStatistics.create to create a new instance.
    """
    def __init__(self, properties):
        self.properties = properties

    def apply(self, name, value):
        """Sets the property values for this instance.

        Args:
            name (str): The name of the statistic being reported.
            value (float): The value of the statistic
        """
        self.name = name
        self.value = value

    @classmethod
    def create(cls, name, value):
        """Sets the property values for this instance.

        Args:
            name (str): The name of the statistic being reported.
            value (float): The value of the statistic
        """
        x = cls({})
        x.apply(name, value)
        return x

    @property
    def name(self):
        """Get or sets the name of the statistic being reported.

        Returns:
            str
        """
        return self.properties.get('name')

    @name.setter
    def name(self, v):
        self.properties['name'] = v

    @property
    def value(self):
        """Get or sets the value of the statistic

        Returns:
            int or float
        """
        return self.properties.get('value')

    @value.setter
    def value(self, v):
        self.properties['value'] = v

    def to_dict(self):
        """Returns the dictionary representing the JSON of this LabelStatistics.

        Returns:
            dict: The wrapped dict of the LabelStatistics that can be written out as JSON.
        """
        return {'name': self.name, 'value': self.value}


LABEL_EXTENSION_DEFINITION = ExtensionDefinition(Extensions.LABEL,
                                                 [ExtendedObject(Item, LabelItemExt)])
