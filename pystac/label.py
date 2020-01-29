"""STAC Model classes for Label extension.
"""
from copy import (copy, deepcopy)

from pystac import STACError
from pystac.item import (Item, Asset)
from pystac.link import Link


class LabelType:
    """Enumerates valid label types (RASTER or VECTOR)."""
    VECTOR = 'vector'
    RASTER = 'raster'

    ALL = [VECTOR, RASTER]
    """Convenience attribute for checking if values are valid label types"""


class LabelItem(Item):
    """A Label Item represents a polygon, set of polygons, or raster data defining
    labels and label metadata and should be part of a Collection.

    Args:
        id (str): Provider identifier. Must be unique within the STAC.
        geometry (dict): Defines the full footprint of the asset represented by this item,
            formatted according to `RFC 7946, section 3.1 (GeoJSON)
            <https://tools.ietf.org/html/rfc7946>`_.
        bbox (List[float]):  Bounding Box of the asset represented by this item using
            either 2D or 3D geometries. The length of the array must be 2*n where n is the
            number of dimensions.
        datetime (Datetime): Datetime associated with this item.
        properties (dict): A dictionary of additional metadata for the item.
        label_desecription (str): A description of the label, how it was created,
            and what it is recommended for
        label_type (str): An ENUM of either vector label type or raster label type. Use
            one of :class:`~pystac.LabelType`.
        label_properties (dict or None): These are the names of the property field(s) in each
            Feature of the label asset's FeatureCollection that contains the classes
            (keywords from label:classes if the property defines classes).
            If labels are rasters, this should be None.
        label_classes (List[LabelClass]): Optional, but reqiured if ussing categorical data.
            A list of LabelClasses defining the list of possible class names for each
            label:properties. (e.g., tree, building, car, hippo)
        label_tasks (str): Recommended to be a subset of 'regression', 'classification',
            'detection', or 'segmentation', but may be an arbitrary value.
        label_methods: Recommended to be a subset of 'automated' or 'manual',
            but may be an arbitrary value.
        label_overviews (List[LabelOverview]): Optional list of LabelOverview classes
            that store counts (for classification-type data) or summary statistics (for
            continuous numerical/regression data).
        stac_extensions (List[str]): Optional list of extensions the Item implements.
        href (str or None): Optional HREF for this item, which be set as the item's
            self link's HREF.
        collection (Collection): Optional Collection that this item is a part of.

    Attributes:
        id (str): Provider identifier. Unique within the STAC.
        geometry (dict): Defines the full footprint of the asset represented by this item,
            formatted according to `RFC 7946, section 3.1 (GeoJSON)
            <https://tools.ietf.org/html/rfc7946>`_.
        bbox (List[float]):  Bounding Box of the asset represented by this item using
            either 2D or 3D geometries. The length of the array is 2*n where n is the
            number of dimensions.
        datetime (Datetime): Datetime associated with this item.
        properties (dict): A dictionary of additional metadata for the item.
        label_desecription (str): A description of the label, how it was created,
            and what it is recommended for
        label_type (str): An ENUM of either vector label type or raster label type (one
            of :class:`~pystac.LabelType`).
        label_properties (dict or None): These are the names of the property field(s) in each
            Feature of the label asset's FeatureCollection that contains the classes
            (keywords from label:classes if the property defines classes).
            If labels are rasters, this should be None.
        label_classes (List[LabelClass]): Optional, but reqiured if ussing categorical data.
            A list of LabelClasses defining the list of possible class names for each
            label:properties. (e.g., tree, building, car, hippo)
        label_tasks (str): Tasks these labels apply to. Usually a subset of 'regression',
            'classification', 'detection', or 'segmentation', but may be an arbitrary value.
        label_methods: Methods used for labeling. Usually a subset of 'automated' or 'manual',
            but may be an arbitrary value.
        label_overviews (List[LabelOverview]): Optional list of LabelOverview classes
            that store counts (for classification-type data) or summary statistics (for
            continuous numerical/regression data).
        stac_extensions (List[str] or None): Optional list of extensions the Item implements.
        collection_id (str or None): The Collection ID that this item belongs to, if any.

    See:
        `Item fields in the label extension spec <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/label#item-fields>`_
    """ # noqa E501

    def __init__(self,
                 id,
                 geometry,
                 bbox,
                 datetime,
                 properties,
                 label_description,
                 label_type,
                 label_properties=None,
                 label_classes=None,
                 label_tasks=None,
                 label_methods=None,
                 label_overviews=None,
                 stac_extensions=None,
                 href=None,
                 collection=None):
        if stac_extensions is None:
            stac_extensions = []
        if 'label' not in stac_extensions:
            stac_extensions.append('label')
        super(LabelItem, self).__init__(id=id,
                                        geometry=geometry,
                                        bbox=bbox,
                                        datetime=datetime,
                                        properties=properties,
                                        stac_extensions=stac_extensions,
                                        href=href)
        self.label_properties = label_properties
        self.label_classes = label_classes
        self.label_description = label_description
        self.label_type = label_type
        self.label_tasks = label_tasks
        self.label_methods = label_methods
        self.label_overviews = label_overviews

        # Be kind if folks didn't use lists for some properties
        if self.label_properties is not None:
            if not type(self.label_properties) is list:
                self.label_properties = [self.label_properties]

        if self.label_methods is not None:
            if not type(self.label_methods) is list:
                self.label_methods = [self.label_methods]

        if self.label_tasks is not None:
            if not type(self.label_tasks) is list:
                self.label_tasks = [self.label_tasks]

        # Some light validation
        if self.label_type not in LabelType.ALL:
            raise STACError("label_type must be one of "
                            "{}; was {}".format(LabelType.ALL,
                                                self.label_type))

    def __repr__(self):
        return '<LabelItem id={}>'.format(self.id)

    def to_dict(self, include_self_link=True):
        d = super(LabelItem, self).to_dict(include_self_link)
        d['properties']['label:description'] = self.label_description
        d['properties']['label:type'] = self.label_type
        d['properties']['label:properties'] = self.label_properties
        if self.label_classes:
            d['properties']['label:classes'] = [
                classes.to_dict() for classes in self.label_classes
            ]
        if self.label_tasks is not None:
            d['properties']['label:tasks'] = self.label_tasks
        if self.label_methods is not None:
            d['properties']['label:methods'] = self.label_methods
        if self.label_overviews is not None:
            d['properties']['label:overviews'] = [
                ov.to_dict() for ov in self.label_overviews
            ]

        return deepcopy(d)

    def add_source(self, source_item, title=None, assets=None):
        """Adds a link to a source item.

        Args:
            source_item (Item): Source imagery that the LabelItem applys to.
            title (str): Optional title for the link.
            assets (List[str]): Optional list of assets that deterime what
                assets in the source item this label item data appliees to.
        """
        properties = None
        if assets is not None:
            properties = {'label:assets': assets}
        link = Link('source',
                    source_item,
                    title=title,
                    media_type='application/json',
                    properties=properties)
        self.add_link(link)

    def get_sources(self):
        """Gets any source items that describe the source imagery used to generate
        this LabelItem.

        Returns:
            Generator[Items]: A possibly empty list of source imagery items. Determined by
            links of this LabelItem that have ``rel=='source'``.
        """
        return self.get_stac_objects('source')

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

        self.add_asset(
            "labels",
            Asset(href=href,
                  title=title,
                  media_type=media_type,
                  properties=properties))

    def add_geojson_labels(self, href, title=None, properties=None):
        """Adds a GeoJSON label asset to this LabelItem.

        Args:
            href (str): Link to the asset object. Relative and absolute links are both allowed.
            title (str): Optional displayed title for clients and users.
            properties (dict): Optional, additional properties for this asset. This is used by
                extensions as a way to serialize and deserialize properties on asset
                object JSON.
        """
        self.add_labels(href,
                        title=title,
                        properties=properties,
                        media_type='application/geo+json')

    def clone(self):
        clone = LabelItem(id=self.id,
                          geometry=deepcopy(self.geometry),
                          bbox=copy(self.bbox),
                          datetime=copy(self.datetime),
                          properties=deepcopy(self.properties),
                          label_description=self.label_description,
                          label_type=self.label_type,
                          label_properties=self.label_properties,
                          label_classes=copy(self.label_classes),
                          stac_extensions=copy(self.stac_extensions),
                          label_tasks=self.label_tasks,
                          label_methods=self.label_methods,
                          label_overviews=deepcopy(self.label_overviews))
        for link in self.links:
            clone.add_link(link.clone())

        clone.assets = dict([(k, a.clone()) for (k, a) in self.assets.items()])
        return clone

    def _object_links(self):
        return super()._object_links() + ['source']

    @classmethod
    def from_dict(cls, d, href=None, root=None):
        item = Item.from_dict(d, href=href, root=root)
        return cls.from_item(item)

    @classmethod
    def from_item(cls, item):
        """Creates a LabelItem from an Item.

        Args:
            item (Item): The Item to create an LabelItem from.

        Returns:
            LabelItem: A new LabelItem from item. If the item
                item is already an LabelItem, simply returns a clone of item.
        """
        if isinstance(item, LabelItem):
            return item.clone()

        props = item.properties

        label_properties = props.get('label:properties')
        if label_properties is None:
            # Allow for pre-0.8.1 non-pluralized form
            label_properties = props.get('label:property')

        label_classes = props.get('label:classes')
        if label_classes is not None:
            label_classes = [
                LabelClasses.from_dict(classes) for classes in label_classes
            ]
        label_description = props['label:description']
        label_type = props['label:type']
        label_tasks = props.get('label:tasks')
        if label_tasks is None:
            # Allow for pre-0.8.1 non-pluralized form
            label_tasks = props.get('label:task')
        label_methods = props.get('label:methods')
        if label_methods is None:
            # Allow for pre-0.8.1 non-pluralized form
            label_methods = props.get('label:method')
        label_overviews = props.get('label:overviews')
        if label_overviews is None:
            # Allow for pre-0.8.1 non-pluralized form
            label_overviews = props.get('label:overview')
        if label_overviews is not None:
            if type(label_overviews) is list:
                label_overviews = [
                    LabelOverview.from_dict(ov) for ov in label_overviews
                ]
            else:
                # Read STAC with mistaken single overview object (should be list)
                label_overviews = LabelOverview.from_dict(label_overviews)

        li = LabelItem(id=item.id,
                       geometry=item.geometry,
                       bbox=item.bbox,
                       datetime=item.datetime,
                       properties=item.properties,
                       label_description=label_description,
                       label_type=label_type,
                       label_properties=label_properties,
                       label_classes=label_classes,
                       stac_extensions=item.stac_extensions,
                       label_tasks=label_tasks,
                       label_methods=label_methods,
                       label_overviews=label_overviews)

        for link in item.links:
            li.add_link(link)

        li.assets = copy(item.assets)
        for asset in li.assets.values():
            asset.set_owner(li)

        return li


class LabelClasses:
    """Defines the list of possible class names (e.g.,
       tree, building, car, hippo)

    Args:
        classes (List[str]): The different possible class values
        name (str): The property key within the asset's each Feature corresponding to
            class labels. If labels are raster-formatted, do not supply; required otherwise.

    Attributes:
        classes (List[str]): The different possible class values
        name (str or None): The property key within the asset's each Feature corresponding to
            class labels. If labels are raster-formatted, this is None.
    """
    def __init__(self, classes, name=None):
        self.name = name
        self.classes = classes

    def to_dict(self):
        """Generate a dictionary representing the JSON of this LabelClasses.

        Returns:
            dict: A serializion of the LabelClasses that can be written out as JSON.
        """
        return {'name': self.name, 'classes': self.classes}

    @staticmethod
    def from_dict(d):
        """Constructs a LabelClasses from a dict.

        Returns:
            LabelClasses: The LabelClasses deserialized from the JSON dict.
        """
        return LabelClasses(name=d.get('name'), classes=d['classes'])


class LabelOverview:
    """Stores counts (for classification-type data) or summary statistics (for
    continuous numerical/regression data).

    Either ``counts`` or ``statistics``, or both, can be placed in an overview;
    at least one is required.

    Args:
        property_key (str): The property key within the asset corresponding to class labels.
        counts (List[LabelCounts]): Optional list of LabelCounts.
        statistics (List[Statistics]): Optional list of Statistics.

    Attributes
        property_key (str): The property key within the asset corresponding to class labels.
        counts (List[LabelCounts] or None): Optional list of LabelCounts.
        statistics (List[Statistics] or None): Optional list of Statistics.
    """
    def __init__(self, property_key, counts=None, statistics=None):
        self.property_key = property_key
        self.counts = counts
        self.statistics = statistics

    def merge_counts(self, other):
        """Merges the counts associated with this overview with another overview.

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
                new_counts = [
                    LabelCount(k, v) for k, v in count_by_prop.items()
                ]
        return LabelOverview(self.property_key, counts=new_counts)

    def to_dict(self):
        """Generate a dictionary representing the JSON of this LabelOverview.

        Returns:
            dict: A serializion of the LabelOverview that can be written out as JSON.
        """
        d = {'property_key': self.property_key}
        if self.counts:
            d['counts'] = [c.to_dict() for c in self.counts]
        if self.statistics:
            d['statistics'] = [s.to_dict() for s in self.statistics]

        return d

    @staticmethod
    def from_dict(d):
        """Constructs a LabelOverview from a dict.

        Returns:
            LabelOverview: The LabelOverview deserialized from the JSON dict.
        """
        counts = d.get('counts')
        if counts is not None:
            counts = [LabelCount.from_dict(c) for c in counts]

        statistics = d.get('statistics')
        if statistics is not None:
            statistics = [LabelStatistics.from_dict(s) for s in statistics]

        return LabelOverview(d['property_key'],
                             counts=counts,
                             statistics=statistics)


class LabelCount:
    def __init__(self, name, count):
        """Contains counts for categorical data.

        Args:
            name (str): The different possible classes within the property.
            count (int): The number of occurrences of the class.

        Attributes:
            name (str): The different possible classes within the property.
            count (int): The number of occurrences of the class.
        """
        self.name = name
        self.count = count

    def to_dict(self):
        """Generate a dictionary representing the JSON of this LabelCount.

        Returns:
            dict: A serializion of the LabelCount that can be written out as JSON.
        """
        return {'name': self.name, 'count': self.count}

    @staticmethod
    def from_dict(d):
        """Constructs a LabelCount from a dict.

        Returns:
            LabelCount: The LabelCount deserialized from the JSON dict.
        """
        return LabelCount(d['name'], d['count'])


class LabelStatistics:
    def __init__(self, name, value):
        """Contains statistics for regression/continuous numeric value data.

        Args:
            name (str): The name of the statistic being reported.
            value (float): The value of the statistic

        Attributes:
            name (str): The name of the statistic being reported.
            value (float): The value of the statistic
        """
        self.name = name
        self.value = value

    def to_dict(self):
        """Generate a dictionary representing the JSON of this LabelStatistics.

        Returns:
            dict: A serializion of the LabelStatistics that can be written out as JSON.
        """
        return {'name': self.name, 'value': self.value}

    @staticmethod
    def from_dict(d):
        """Constructs a LabelStatistics from a dict.

        Returns:
            LabelStatistics: The LabelStatistics deserialized from the JSON dict.
        """
        return LabelStatistics(d['name'], d['value'])
