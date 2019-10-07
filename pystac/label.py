"""STAC Model classes for Label extension.
"""
from copy import (copy, deepcopy)

from pystac import STACError
from pystac.item import Item
from pystac.link import Link

class LabelType:
    VECTOR = 'vector'
    RASTER = 'raster'
    ALL = [VECTOR, RASTER]

class LabelItem(Item):
    def __init__(self,
                 id,
                 geometry,
                 bbox,
                 datetime,
                 properties,
                 label_description,
                 label_type,
                 label_property=None,
                 label_classes=None,
                 stac_extensions=None,
                 href=None,
                 label_task=None,
                 label_method=None,
                 label_overview=None):
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
        self.label_property = label_property
        self.label_classes = label_classes
        self.label_description = label_description
        self.label_type = label_type
        self.label_task = label_task
        self.label_method = label_method
        self.label_overview = label_overview

        # Be kind if folks didn't use lists for some properties
        if self.label_property is not None:
            if not type(self.label_property) is list:
                self.label_property = [self.label_property]

        if self.label_method is not None:
            if not type(self.label_method) is list:
                self.label_method = [self.label_method]

        if self.label_task is not None:
            if not type(self.label_task) is list:
                self.label_task = [self.label_task]

        # Some light validation
        if not self.label_type in LabelType.ALL:
            raise STACError("label_type must be one of "
                            "{}; was {}".format(LabelType.ALL, self.label_type))

        if self.label_type == LabelType.VECTOR:
            if self.label_property is None:
                raise STACError('label_property must be set for vector label type')

        if self.label_task is not None:
            for task in self.label_task:
                if task in ['classification', 'detection', 'segmentation']:
                    if self.label_classes is None:
                        raise STACError('label_classes must be set '
                                        'for task "{}"'.format(self.label_task))

    def __repr__(self):
        return '<LabelItem id={}>'.format(self.id)

    def to_dict(self, include_self_link=True):
        d = super(LabelItem, self).to_dict(include_self_link)
        d['properties']['label:description'] = self.label_description
        d['properties']['label:type'] = self.label_type
        d['properties']['label:property'] = self.label_property
        if self.label_classes:
            d['properties']['label:classes'] = [classes.to_dict() for classes in self.label_classes]
        if self.label_task is not None:
            d['properties']['label:task'] = self.label_task
        if self.label_method is not None:
            d['properties']['label:method'] = self.label_method
        if self.label_overview is not None:
            d['properties']['label:overview'] = [ov.to_dict() for ov in self.label_overview]

        return d

    def add_source(self, source_item, title=None, assets=None):
        properties = None
        if assets is not None:
            properties = { 'label:assets': assets }
        link = Link('source',
                    source_item,
                    title=title,
                    media_type='application/json',
                    properties=properties)
        self.add_link(link)

    def add_labels(self, href, title=None, media_type=None, properties=None):
        self.add_asset("labels",
                       href=href,
                       title=title,
                       media_type=media_type,
                       properties=properties)

    def add_geojson_labels(self, href, title=None, properties=None):
        self.add_labels(href,
                        title=title,
                        properties=properties,
                        media_type='application/geo+json')

    def clone(self):
        clone =  LabelItem(id=self.id,
                           geometry=deepcopy(self.geometry),
                           bbox=copy(self.bbox),
                           datetime=copy(self.datetime),
                           properties=deepcopy(self.properties),
                           label_description=self.label_description,
                           label_type=self.label_type,
                           label_property=self.label_property,
                           label_classes=copy(self.label_classes),
                           stac_extensions=copy(self.stac_extensions),
                           label_task=self.label_task,
                           label_method=self.label_method,
                           label_overview=deepcopy(self.label_overview))
        for link in self.links:
            clone.add_link(link.clone())

        clone.assets = dict([(k, a.clone()) for (k, a) in self.assets.items()])
        return clone

    @staticmethod
    def from_dict(d):
        item = Item.from_dict(d)
        props = item.properties

        label_property = props.get('label:property')
        label_classes = props.get('label:classes')
        if label_classes is not None:
            label_classes = [LabelClasses.from_dict(classes) for classes in label_classes]
        label_description = props['label:description']
        label_type = props['label:type']
        label_task = props.get('label:task')
        label_method = props.get('label:method')
        label_overview = props.get('label:overview')
        if label_overview is not None:
            if type(label_overview) is list:
                label_overview = [LabelOverview.from_dict(ov) for ov in label_overview]
            else:
                # Read STAC with mistaken single overview object (should be list)
                label_overview = LabelOverview.from_dict(label_overview)

        li = LabelItem(id=item.id,
                       geometry=item.geometry,
                       bbox=item.bbox,
                       datetime=item.datetime,
                       properties=item.properties,
                       label_description=label_description,
                       label_type=label_type,
                       label_property=label_property,
                       label_classes=label_classes,
                       stac_extensions=item.stac_extensions,
                       label_task=label_task,
                       label_method=label_method,
                       label_overview=label_overview)

        for link in item.links:
            li.add_link(link)
        li.assets = copy(item.assets)

        return li

    def _object_links(self):
        return super()._object_links() + ['source']

class LabelClasses:
    def __init__(self, classes, name=None):
        self.name = name
        self.classes = classes

    def to_dict(self):
        return { 'name': self.name, 'classes': self.classes }

    @staticmethod
    def from_dict(d):
        return LabelClasses(name=d['name'], classes=d['classes'])

class LabelOverview:
    def __init__(self, property_key, counts=None, statistics=None):
        self.property_key = property_key
        self.counts = counts
        self.statistics = statistics

    def merge_counts(self, other):
        assert(self.property_key == other.property_key)

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
                        if not c.name in count_by_prop:
                            count_by_prop[c.name] = c.count
                        else:
                            count_by_prop[c.name] += c.count
                add_counts(self.counts)
                add_counts(other.counts)
                new_counts = [LabelCount(k, v)
                              for k, v in count_by_prop.items()]
        return LabelOverview(self.property_key, counts=new_counts)

    def to_dict(self):
        d = { 'property_key': self.property_key }
        if self.counts:
            d['counts'] = [c.to_dict() for c in self.counts]
        if self.statistics:
            d['statistics'] = [s.to_dict() for s in self.statistics]

        return d

    @staticmethod
    def from_dict(d):
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
        self.name = name
        self.count = count

    def to_dict(self):
        return { 'name': self.name,
                 'count': self.count }

    @staticmethod
    def from_dict(d):
        return LabelCount(d['name'], d['count'])

class LabelStatistics:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def to_dict(self):
        return { 'name': self.name,
                 'value': self.value }

    @staticmethod
    def from_dict(d):
        return LabelStatistics(d['name'], d['value'])
