import json
from pystac.catalog import Catalog

from pystac import STACError
from pystac.collection import Collection
from pystac.stac_io import STAC_IO
from pystac.item import Item


class SingleFileSTAC(Catalog):
    """Provides a set of Collections and Items as a single file catalog. The single file
    is a self contained catalog that contains everything that would normally be in a
    linked set of STAC files.

    Args:
        id (str): Identifier for the Catalog. Must be unique within the STAC.
        description (str): Detailed multi-line description to fully explain the catalog.
            `CommonMark 0.28 syntax <http://commonmark.org/>`_ MAY be used for rich text
            representation.
        features (List[Item]): Optional initial list of items contained by
            this SingleFileSTAC.
        stac_extensions (List[str]): Optional list of extensions implemented.
        collections (List[Collection]): Optional initial list of collections contained
            by this SingleFileSTAC.
        search (Search): Optional search information associated with this SingleFileSTAC.

    Attributes:
        id (str): Identifier for the catalog.
        description (str): Detailed multi-line description to fully explain the catalog.
        features (List[Item]): Items contained by this SingleFileSTAC
        collections (List[Collection]): Collections contained
            by this SingleFileSTAC.
        search (Search): Optional search information associated with this SingleFileSTAC.
        links (List[Link]): A list of :class:`~pystac.Link` objects representing
            all links associated with this SingleFileSTAC.

    """
    def __init__(self,
                 id,
                 description,
                 features=None,
                 stac_extensions=None,
                 collections=None,
                 search=None):
        super().__init__(id, description, title=None, stac_extensions=stac_extensions)

        if features is None:
            self.features = []
        else:
            self.features = features

        if collections is None:
            self.collections = []
        else:
            self.collections = collections

        self.search = search

    def __repr__(self):
        return '<SingleFileSTAC with {} items and {} collections>'.format(
            len(self.features), len(self.collections))

    def get_collections(self):
        """Gets all the collections associated with this SingleFileSTAC.

        Returns:
            List[Collection]: The Collections of this SingleFileSTAC
        """
        return self.collections

    def add_collection(self, collection):
        """Adds a Collection to this SingleFileSTAC.

        Args:
            collection (Collection): The collection to add.
        """
        self.collections.append(collection)

    def add_collections(self, collections):
        """Adds Collections to this SingleFileSTAC.

        Args:
            collections (Iterable[Collection]): The collections to add.
        """
        for collection in collections:
            self.add_collection(collection)

    @staticmethod
    def from_file(uri):
        """Reads an SingleFileSTAC from a file.

        Args:
            href (str): The HREF to read the item from.

        Returns:
            SingleFileSTAC: SingleFileSTAC that was read from the given file.
        """

        d = json.loads(STAC_IO.read_text(uri))
        c = SingleFileSTAC.from_dict(d)
        return c

    @staticmethod
    def from_dict(d):
        """Constructs an SingleFileSTAC from a dict.

        Returns:
            SingleFileSTAC: The SingleFileSTAC deserialized from the JSON dict.
        """
        features = [Item.from_dict(feature) for feature in d['features']]
        collections = [Collection.from_dict(c) for c in d['collections']]
        stac_extensions = d.get('stac_extensions')

        # Tie together items to their collections
        collection_dict = dict([(c.id, c) for c in collections])
        for item in features:
            if item.collection_id is not None:
                if item.collection_id not in collection_dict:
                    raise STACError('Collection with id {} is referenced '
                                    'by item {}, but is not in the collections '
                                    'of this SingleFileSTAC'.format(item.collection_id, item.id))
                item.set_collection(collection_dict[item.collection_id])

        search_obj = None
        if 'search' in d.keys():
            sd = d['search']
            search_obj = Search(sd.get('endpoint'), sd.get('parameters'))
        return SingleFileSTAC(features, stac_extensions, collections, search_obj)

    def to_dict(self, include_self_link=False):
        """Generate a dictionary representing the JSON of this SingleFileSTAC.

        Args:
            include_self_link (bool): If True, writes the SingleFileSTAC's self link.
                Defaults to False.

        Returns:
            dict: A serializion of the SingleFileSTAC that can be written out as JSON.
        """

        d = super().to_dict(include_self_link=include_self_link)

        d['collections'] = [c.to_dict() for c in self.collections]
        d['features'] = [f.to_dict() for f in self.features]
        if self.search:
            d['search'] = self.search.to_dict()

        return d


class Search:
    """Contains search endpoint and parameters information for a search used to generate
    a Single File STAC.

    Args:
        endpoint (str): The root endpoint of a STAC API used for this search.
        parameters (dict): A dictionary of all the parameters used for the search.

    Attributes:
        endpoint (str): The root endpoint of a STAC API used for this search.
        parameters (dict): A dictionary of all the parameters used for the search.
    """
    def __init__(self, endpoint=None, parameters=None):
        self.endpoint = endpoint
        self.parameters = parameters

    @staticmethod
    def from_dict(d):
        return Search(d.get('endpoint'), d.get('parameters'))

    def to_dict(self):
        d = {}
        if self.endpoint is not None:
            d['endpoint'] = self.endpoint

        if self.parameters is not None:
            d['parameters'] = self.parameters

        return d
