"""Implement the scientific extension.

https://github.com/radiantearth/stac-spec/tree/dev/extensions/scientific
"""

# TODO(schwehr): Document.

import copy
import re

import pystac
from pystac import collection
from pystac import Extensions
from pystac import item
from pystac.extensions import base

PREFIX = 'sci:'
DOI = PREFIX + 'doi'
CITATION = PREFIX + 'citation'
PUBLICATIONS = PREFIX + 'publications'

# Link type.
CITE_AS = 'cite-as'

# TODO(schwehr): What is the correct regex for doi?
# https://github.com/radiantearth/stac-spec/issues/910
DOI_REGEX = r'10[.][0-9]{4}([.][0-9]+)*/.+'
DOI_URL_BASE = 'https://doi.org/'


def validate_doi(doi_str):
    match = re.match(DOI_REGEX, doi_str)
    if not match:
        raise pystac.STACError('bad doi')


class Publication:
    """Helper for Publication entries."""
    def __init__(self, doi, citation):
        validate_doi(doi)
        self.doi = doi
        self.citation = citation

    def __eq__(self, other):
        if not isinstance(other, Publication):
            return NotImplemented

        return self.doi == other.doi and self.citation == other.citation

    def __repr__(self):
        return f'<Publication doi={self.doi} target={self.citation}>'

    def to_dict(self):
        return copy.deepcopy({'doi': self.doi, 'citation': self.citation})

    @staticmethod
    def from_dict(d):
        return Publication(d['doi'], d['citation'])

    def get_link(self):
        url = DOI_URL_BASE + self.doi
        return pystac.link.Link(CITE_AS, url)


class ScientificItemExt(base.ItemExtension):
    """Add an citation and dois to a STAC Item."""
    def __init__(self, an_item):
        self.item = an_item

    def apply(self, doi=None, citation=None, publications=None):
        if doi:
            self.doi = doi
        if citation:
            self.citation = citation
        if publications:
            self.publications = publications

    @classmethod
    def from_item(cls, an_item):
        return cls(an_item)

    @classmethod
    def _object_links(cls):
        return []

    @property
    def doi(self):
        return self.item.properties.get(DOI)

    @doi.setter
    def doi(self, v):
        self.item.properties[DOI] = v
        url = DOI_URL_BASE + self.doi
        self.item.add_link(pystac.link.Link(CITE_AS, url))

    @property
    def citation(self):
        return self.item.properties.get(CITATION)

    @citation.setter
    def citation(self, v):
        self.item.properties[CITATION] = v

    @property
    def publications(self):
        return [Publication.from_dict(pub) for pub in self.item.properties.get(PUBLICATIONS)]

    @publications.setter
    def publications(self, v):
        self.item.properties[PUBLICATIONS] = [pub.to_dict() for pub in v]
        for pub in v:
            self.item.add_link(pub.get_link())


class ScientificCollectionExt(base.CollectionExtension):
    """Add an citation and dois to a STAC Collection."""
    def __init__(self, a_collection):
        self.collection = a_collection

    def apply(self, doi=None, citation=None, publications=None):
        if doi:
            self.doi = doi
        if citation:
            self.citation = citation
        if publications:
            self.publications = publications

    @classmethod
    def from_collection(cls, a_collection):
        return cls(a_collection)

    @classmethod
    def _object_links(cls):
        return []

    @property
    def doi(self):
        return self.collection.extra_fields.get(DOI)

    @doi.setter
    def doi(self, v):
        self.collection.extra_fields[DOI] = v
        url = DOI_URL_BASE + self.doi
        self.collection.add_link(pystac.link.Link(CITE_AS, url))

    @property
    def citation(self):
        return self.collection.extra_fields.get(CITATION)

    @citation.setter
    def citation(self, v):
        self.collection.extra_fields[CITATION] = v

    @property
    def publications(self):
        return [Publication.from_dict(p) for p in self.collection.extra_fields.get(PUBLICATIONS)]

    @publications.setter
    def publications(self, v):
        self.collection.extra_fields[PUBLICATIONS] = [pub.to_dict() for pub in v]
        for pub in v:
            self.collection.add_link(pub.get_link())


SCIENTIFIC_EXTENSION_DEFINITION = base.ExtensionDefinition(Extensions.SCIENTIFIC, [
    base.ExtendedObject(item.Item, ScientificItemExt),
    base.ExtendedObject(collection.Collection, ScientificCollectionExt)
])
