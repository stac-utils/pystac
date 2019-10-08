import json
from datetime import datetime
from datetime import timezone
import dateutil.parser
from copy import copy
import json

from pystac import STACError, STAC_IO
from pystac.catalog import Catalog
from pystac.link import (Link, LinkType)
from pystac.io import STAC_IO
from pystac.utils import (make_absolute_href, is_absolute_href)

class Collection(Catalog):
    DEFAULT_FILE_NAME = "collection.json"

    def __init__(self,
                 id,
                 description,
                 extent,
                 title=None,
                 href=None,
                 license='proprietary',
                 stac_extensions=None,
                 keywords=None,
                 version=None,
                 providers=None,
                 properties=None,
                 summaries=None):
        super(Collection, self).__init__(id, description, title, href)
        self.extent = extent
        self.license = license

        self.stac_extensions = stac_extensions
        self.keywords = keywords
        self.version = version
        self.providers = providers
        self.properties = properties
        self.summaries = summaries

    def __repr__(self):
        return '<Collection id={}>'.format(self.id)

    def add_item(self, item, title=None):
        super(Collection, self).add_item(item, title)
        item.set_collection(self)

    def to_dict(self, include_self_link=True):
        d = super(Collection, self).to_dict(include_self_link)
        d['extent'] = self.extent.to_dict()
        d['license'] = self.license
        if self.stac_extensions is not None:
            d['stac_extensions'] = self.stac_extensions
        if self.keywords is not None:
            d['keywords'] = self.keywords
        if self.version is not None:
            d['version'] = self.version
        if self.providers is not None:
            d['providers'] = list(map(lambda x: x.to_dict(), self.providers))
        if self.properties is not None:
            d['properties'] = self.properties
        if self.summaries is not None:
            d['summaries'] = self.summaries

        return d

    def clone(self):
        clone = Collection(id=self.id,
                           description=self.description,
                           extent=self.extent.clone(),
                           title=self.title,
                           license=self.license,
                           stac_extensions = self.stac_extensions,
                           keywords = self.keywords,
                           version=self.version,
                           providers=self.providers,
                           properties=self.properties,
                           summaries=self.summaries)

        clone._resolved_objects.set(clone)

        clone.add_links([l.clone() for l in self.links])

        return clone

    @staticmethod
    def from_dict(d):
        id = d['id']
        description = d['description']
        license = d['license']
        extent = Extent.from_dict(d['extent'])
        title = d.get('title')
        stac_extensions = d.get('stac_extensions')
        keywords = d.get('keywords')
        version = d.get('version')
        providers = d.get('providers')
        if providers is not None:
            providers = list(map(lambda x: Provider.from_dict(x), providers))
        properties = d.get('properties')
        summaries = d.get('summaries')

        collection = Collection(id=id,
                                description=description,
                                extent=extent,
                                title=title,
                                license=license,
                                stac_extensions=stac_extensions,
                                keywords=keywords,
                                version=version,
                                providers=providers,
                                properties=properties,
                                summaries=summaries)

        for l in d['links']:
            if not l['rel'] == 'root':
                collection.add_link(Link.from_dict(l))
            else:
                # If a root link was included, we want to inheret
                # whether it was relative or not.
                if not is_absolute_href(l['href']):
                    collection.get_single_link('root').link_type = LinkType.RELATIVE


        return collection

    @staticmethod
    def from_file(uri):
        if not is_absolute_href(uri):
            uri = make_absolute_href(uri)
        d = json.loads(STAC_IO.read_text(uri))
        c = Collection.from_dict(d)
        c.set_self_href(uri)
        return c


class Extent:
    def __init__(self, spatial, temporal):
        self.spatial = spatial
        self.temporal = temporal

    def to_dict(self):
        return {
            'spatial': self.spatial.to_dict(),
            'temporal': self.temporal.to_dict()
        }

    def clone(self):
        return Extent(spatial=copy(self.spatial),
                      temporal=copy(self.temporal))

    @staticmethod
    def from_dict(d):
        return Extent(SpatialExtent.from_dict(d['spatial']),
                      TemporalExtent.from_dict(d['temporal']))


class SpatialExtent:
    def __init__(self, bboxes):
        self.bboxes = bboxes

    def to_dict(self):
        return { 'bbox' : self.bboxes }

    def clone(self):
        return SpatialExtent(self.bboxes)

    @staticmethod
    def from_dict(d):
        return SpatialExtent(bboxes=d['bbox'])

    @staticmethod
    def from_coordinates(coordinates):
        def process_coords(l, xmin=None, ymin=None, xmax=None, ymax=None):
            for coord in l:
                if type(coord[0]) is list:
                    xmin, ymin, xmax, ymax = process_coords(coord, xmin, ymin, xmax, ymax)
                else:
                    x, y = coord
                    if xmin is None or x < xmin:
                        xmin = x
                    elif xmax is None or xmax < x:
                        xmax = x
                    if ymin is None or y < ymin:
                        ymin = y
                    elif ymax is None or ymax < y:
                        ymax = y
            return xmin, ymin, xmax, ymax

        xmin, ymin, xmax, ymax = process_coords(coordinates)

        return SpatialExtent([[xmin, ymin, xmax, ymax]])


class TemporalExtent:
    """Temporal extent. Assumes all times in UTC"""
    def __init__(self, intervals):
        for i in intervals:
            if i[0] is None and i[1] is None:
                raise STACError('TemporalExtent interval must have either '
                                'a start or an end time, or both')
        self.intervals = intervals

    def to_dict(self):
        encoded_intervals = []
        for i in self.intervals:
            start = None
            end = None

            if i[0]:
                start = '{}Z'.format(i[0].replace(microsecond=0, tzinfo=None).isoformat())

            if i[1]:
                end = '{}Z'.format(i[1].replace(microsecond=0, tzinfo=None).isoformat())

            encoded_intervals.append([start, end])

        return { 'interval': encoded_intervals }

    def clone(self):
        return TemporalExtent(intervals=copy(self.intervals))

    @staticmethod
    def from_dict(d):
        """Parses temporal extent from list of strings"""
        parsed_intervals = []
        for i in d['interval']:
            start = None
            end = None

            if i[0]:
                start = dateutil.parser.parse(i[0])
            if i[1]:
                end = dateutil.parser.parse(i[1])
            parsed_intervals.append([start, end])

        return TemporalExtent(intervals=parsed_intervals)

    @staticmethod
    def from_now():
        return TemporalExtent(intervals=[[datetime.utcnow().replace(microsecond=0), None]])


class Provider:
    def __init__(self, name, description=None, roles=None, url=None):
        self.name = name
        self.description = description
        self.roles = roles
        self.url = url

    def to_dict(self):
        d = { 'name': self.name }
        if self.description is not None:
            d['description'] = self.description
        if self.roles is not None:
            d['roles'] = self.roles
        if self.url is not None:
            d['url'] = self.url

        return d

    @staticmethod
    def from_dict(d):
        return Provider(name=d['name'],
                        description=d.get('description'),
                        roles=d.get('roles'),
                        url=d.get('url'))
