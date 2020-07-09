from datetime import datetime
import dateutil.parser
from copy import (copy, deepcopy)

from pystac import STACError
from pystac.catalog import Catalog
from pystac.link import Link
from pystac.utils import datetime_to_str


class Collection(Catalog):
    """A Collection extends the Catalog spec with additional metadata that helps
    enable discovery.

    Args:
        id (str): Identifier for the collection. Must be unique within the STAC.
        description (str): Detailed multi-line description to fully explain the collection.
            `CommonMark 0.28 syntax <http://commonmark.org/>`_ MAY be used for rich text
            representation.
        extent (Extent): Spatial and temporal extents that describe the bounds of
            all items contained within this Collection.
        title (str or None): Optional short descriptive one-line title for the collection.
        stac_extensions (List[str]): Optional list of extensions the Collection implements.
        href (str or None): Optional HREF for this collection, which be set as the collection's
            self link's HREF.
        license (str):  Collection's license(s) as a `SPDX License identifier
            <https://spdx.org/licenses/>`_ or `expression
            <https://spdx.org/spdx-specification-21-web-version#h.jxpfx0ykyb60>`_. Defaults
            to 'proprietary'.
        keywords (List[str]): Optional list of keywords describing the collection.
        version (str): Optional version of the Collection.
        providers (List[Provider]): Optional list of providers of this Collection.
        properties (dict): Optional dict of common fields across referenced items.
        summaries (dict): An optional map of property summaries,
            either a set of values or statistics such as a range.

    Attributes:
        id (str): Identifier for the collection.
        description (str): Detailed multi-line description to fully explain the collection.
        extent (Extent): Spatial and temporal extents that describe the bounds of
            all items contained within this Collection.
        title (str or None): Optional short descriptive one-line title for the collection.
        stac_extensions (List[str]): Optional list of extensions the Collection implements.
        keywords (List[str] or None): Optional list of keywords describing the collection.
        version (str or None): Optional version of the Collection.
        providers (List[Provider] or None): Optional list of providers of this Collection.
        properties (dict or None): Optional dict of common fields across referenced items.
        summaries (dict or None): An optional map of property summaries,
            either a set of values or statistics such as a range.
        links (List[Link]): A list of :class:`~pystac.Link` objects representing
            all links associated with this Collection.
    """
    DEFAULT_FILE_NAME = "collection.json"
    """Default file name that will be given to this STAC object in a cononical format."""
    def __init__(self,
                 id,
                 description,
                 extent,
                 title=None,
                 stac_extensions=None,
                 href=None,
                 license='proprietary',
                 keywords=None,
                 version=None,
                 providers=None,
                 properties=None,
                 summaries=None):
        super(Collection, self).__init__(id, description, title, stac_extensions, href)
        self.extent = extent
        self.license = license

        self.stac_extensions = stac_extensions
        self.keywords = keywords
        self.version = version
        self.providers = providers
        self.properties = properties
        self.summaries = summaries

    def set_self_href(self, href):
        """Sets the absolute HREF that is represented by the ``rel == 'self'``
        :class:`~pystac.Link`.

        Args:
            str: The absolute HREF of this object. If the given HREF
                is not absolute, it will be transformed to an absolute
                HREF based on the current working directory.

        Note:
            Overridden for collections so that the root's ResolutionObjectCache can properly
            update the HREF cache.
        """
        root = self.get_root()
        if root is not None:
            root._resolved_objects.remove(self)

        super().set_self_href(href)

        if root is not None:
            root._resolved_objects.cache(self)

        return self

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

        return deepcopy(d)

    def clone(self):
        clone = Collection(id=self.id,
                           description=self.description,
                           extent=self.extent.clone(),
                           title=self.title,
                           license=self.license,
                           stac_extensions=self.stac_extensions,
                           keywords=self.keywords,
                           version=self.version,
                           providers=self.providers,
                           properties=self.properties,
                           summaries=self.summaries)

        clone._resolved_objects.cache(clone)

        for link in self.links:
            if link.rel == 'root':
                # Collection __init__ sets correct root to clone; don't reset
                # if the root link points to self
                root_is_self = link.is_resolved() and link.target is self
                if not root_is_self:
                    clone.set_root(None)
                    clone.add_link(link.clone())
            else:
                clone.add_link(link.clone())

        return clone

    @classmethod
    def from_dict(cls, d, href=None, root=None):
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

        has_self_link = False
        for link in d['links']:
            has_self_link |= link['rel'] == 'self'
            if link['rel'] == 'root':
                # Remove the link that's generated in Catalog's constructor.
                collection.remove_links('root')

            collection.add_link(Link.from_dict(link))

        if not has_self_link and href is not None:
            collection.add_link(Link.self_href(href))

        return collection


class Extent:
    """Describes the spatio-temporal extents of a Collection.

    Args:
        spatial (SpatialExtent): Potential spatial extent covered by the collection.
        temporal (TemporalExtent): Potential temporal extent covered by the collection.

    Attributes:
        spatial (SpatialExtent): Potential spatial extent covered by the collection.
        temporal (TemporalExtent): Potential temporal extent covered by the collection.
    """
    def __init__(self, spatial, temporal):
        self.spatial = spatial
        self.temporal = temporal

    def to_dict(self):
        """Generate a dictionary representing the JSON of this Extent.

        Returns:
            dict: A serializion of the Extent that can be written out as JSON.
        """
        d = {'spatial': self.spatial.to_dict(), 'temporal': self.temporal.to_dict()}

        return deepcopy(d)

    def clone(self):
        """Clones this object.

        Returns:
            Extent: The clone of this extent.
        """
        return Extent(spatial=copy(self.spatial), temporal=copy(self.temporal))

    @staticmethod
    def from_dict(d):
        """Constructs an Extent from a dict.

        Returns:
            Extent: The Extent deserialized from the JSON dict.
        """

        # Handle pre-0.8 spatial extents
        spatial_extent_dict = d['spatial']
        if isinstance(spatial_extent_dict, list):
            spatial_extent_dict = {'bbox': [spatial_extent_dict]}

        # Handle pre-0.8 temporal extents
        temporal_extent_dict = d['temporal']
        if isinstance(temporal_extent_dict, list):
            temporal_extent_dict = {'interval': [temporal_extent_dict]}

        return Extent(SpatialExtent.from_dict(spatial_extent_dict),
                      TemporalExtent.from_dict(temporal_extent_dict))


class SpatialExtent:
    """Describes the spatial extent of a Collection.

    Args:
        bboxes (List[List[float]]): A list of bboxes that represent the spatial
            extent of the collection. Each bbox can be 2D or 3D. The length of the bbox
            array must be 2*n where n is the number of dimensions. For example, a
            2D Collection with only one bbox would be [[xmin, ymin, xmax, ymax]]

    Attributes:
        bboxes (List[List[float]]): A list of bboxes that represent the spatial
            extent of the collection. Each bbox can be 2D or 3D. The length of the bbox
            array must be 2*n where n is the number of dimensions. For example, a
            2D Collection with only one bbox would be [[xmin, ymin, xmax, ymax]]
    """
    def __init__(self, bboxes):
        self.bboxes = bboxes

    def to_dict(self):
        """Generate a dictionary representing the JSON of this SpatialExtent.

        Returns:
            dict: A serializion of the SpatialExtent that can be written out as JSON.
        """
        d = {'bbox': self.bboxes}
        return deepcopy(d)

    def clone(self):
        """Clones this object.

        Returns:
            SpatialExtent: The clone of this object.
        """
        return SpatialExtent(self.bboxes)

    @staticmethod
    def from_dict(d):
        """Constructs an SpatialExtent from a dict.

        Returns:
            SpatialExtent: The SpatialExtent deserialized from the JSON dict.
        """
        return SpatialExtent(bboxes=d['bbox'])

    @staticmethod
    def from_coordinates(coordinates):
        """Constructs a SpatialExtent from a set of coordinates.

        This method will only produce a single bbox that covers all points
        in the coordinate set.

        Args:
            coordinates (List[float]): Coordinates to derive the bbox from.

        Returns:
            SpatialExtent: A SpatialExtent with a single bbox that covers the
            given coordinates.
        """
        def process_coords(link, xmin=None, ymin=None, xmax=None, ymax=None):
            for coord in link:
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
    """Describes the temporal extent of a Collection.

    Args:
        intervals (List[List[datetime]]):  A list of two datetimes wrapped in a list,
        representing the temporal extent of a Collection. Open date ranges are supported
        by setting either the start (the first element of the interval) or the end (the
        second element of the interval) to None.


    Attributes:
        intervals (List[List[datetime]]):  A list of two datetimes wrapped in a list,
        representing the temporal extent of a Collection. Open date ranges are represented
        by either the start (the first element of the interval) or the end (the
        second element of the interval) being None.

    Note:
        Datetimes are required to be in UTC.
    """
    def __init__(self, intervals):
        for i in intervals:
            if i[0] is None and i[1] is None:
                raise STACError('TemporalExtent interval must have either '
                                'a start or an end time, or both')
        self.intervals = intervals

    def to_dict(self):
        """Generate a dictionary representing the JSON of this TemporalExtent.

        Returns:
            dict: A serializion of the TemporalExtent that can be written out as JSON.
        """
        encoded_intervals = []
        for i in self.intervals:
            start = None
            end = None

            if i[0]:
                start = datetime_to_str(i[0])

            if i[1]:
                end = datetime_to_str(i[1])

            encoded_intervals.append([start, end])

        d = {'interval': encoded_intervals}
        return deepcopy(d)

    def clone(self):
        """Clones this object.

        Returns:
            TemporalExtent: The clone of this object.
        """
        return TemporalExtent(intervals=copy(self.intervals))

    @staticmethod
    def from_dict(d):
        """Constructs an TemporalExtent from a dict.

        Returns:
            TemporalExtent: The TemporalExtent deserialized from the JSON dict.
        """
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
        """Constructs an TemporalExtent with a single open interval that has
        the start time as the current time.

        Returns:
            TemporalExtent: The resulting TemporalExtent.
        """
        return TemporalExtent(intervals=[[datetime.utcnow().replace(microsecond=0), None]])


class Provider:
    """Provides information about a provider of STAC data. A provider is any of the
    organizations that captured or processed the content of the collection and therefore
    influenced the data offered by this collection. May also include information about the
    final storage provider hosting the data.

    Args:
        name (str): The name of the organization or the individual.
        description (str): Optional multi-line description to add further provider
            information such as processing details for processors and producers,
            hosting details for hosts or basic contact information.
        roles (List[str]): Optional roles of the provider. Any of
            licensor, producer, processor or host.
        url (str): Optional homepage on which the provider describes the dataset
            and publishes contact information.

    Attributes:
        name (str): The name of the organization or the individual.
        description (str): Optional multi-line description to add further provider
            information such as processing details for processors and producers,
            hosting details for hosts or basic contact information.
        roles (List[str]): Optional roles of the provider. Any of
            licensor, producer, processor or host.
        url (str): Optional homepage on which the provider describes the dataset
            and publishes contact information.
    """
    def __init__(self, name, description=None, roles=None, url=None):
        self.name = name
        self.description = description
        self.roles = roles
        self.url = url

    def to_dict(self):
        """Generate a dictionary representing the JSON of this Provider.

        Returns:
            dict: A serializion of the Provider that can be written out as JSON.
        """
        d = {'name': self.name}
        if self.description is not None:
            d['description'] = self.description
        if self.roles is not None:
            d['roles'] = self.roles
        if self.url is not None:
            d['url'] = self.url

        return deepcopy(d)

    @staticmethod
    def from_dict(d):
        """Constructs an Provider from a dict.

        Returns:
            TemporalExtent: The Provider deserialized from the JSON dict.
        """
        return Provider(name=d['name'],
                        description=d.get('description'),
                        roles=d.get('roles'),
                        url=d.get('url'))
