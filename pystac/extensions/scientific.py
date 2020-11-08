"""Implement the scientific extension.

https://github.com/radiantearth/stac-spec/tree/dev/extensions/scientific

For a description of Digital Object Identifiers (DOIs), see the DOI Handbook:

https://doi.org/10.1000/182
"""

import copy
from typing import Dict, List, Optional
from urllib import parse

import pystac
from pystac import Extensions
from pystac.extensions import base

# STAC fields strings.
PREFIX: str = 'sci:'
DOI: str = PREFIX + 'doi'
CITATION: str = PREFIX + 'citation'
PUBLICATIONS: str = PREFIX + 'publications'

# Link type.
CITE_AS: str = 'cite-as'

DOI_URL_BASE = 'https://doi.org/'


def doi_to_url(doi: str) -> str:
    return DOI_URL_BASE + parse.quote(doi)


class Publication:
    """Helper for Publication entries."""
    def __init__(self, doi: str, citation: str) -> None:
        self.doi = doi
        self.citation = citation

    def __eq__(self, other):
        if not isinstance(other, Publication):
            return NotImplemented

        return self.doi == other.doi and self.citation == other.citation

    def __repr__(self) -> str:
        return f'<Publication doi={self.doi} target={self.citation}>'

    def to_dict(self) -> Dict[str, str]:
        return copy.deepcopy({'doi': self.doi, 'citation': self.citation})

    @staticmethod
    def from_dict(d: Dict[str, str]):
        return Publication(d['doi'], d['citation'])

    def get_link(self) -> pystac.Link:
        return pystac.Link(CITE_AS, doi_to_url(self.doi))


def remove_link(links: List[pystac.Link], doi: str):
    url = doi_to_url(doi)
    for i, a_link in enumerate(links):
        if a_link.rel != CITE_AS:
            continue
        if a_link.target == url:
            del links[i]
            break


class ScientificItemExt(base.ItemExtension):
    """ScientificItemExt extends Item to add citations and DOIs to a STAC Item.

    Args:
        item (Item): The item to be extended.

    Attributes:
        item (Item): The item that is being extended.

    Note:
        Using ScientificItemExt to directly wrap an item will add the 'scientific'
        extension ID to the item's stac_extensions.
    """
    item: pystac.Item

    def __init__(self, an_item: pystac.Item) -> None:
        self.item = an_item

    def apply(self,
              doi: Optional[str] = None,
              citation: Optional[str] = None,
              publications: Optional[List[Publication]] = None) -> None:
        """Applies scientific extension properties to the extended Item.

        Args:
            doi (str): Optional DOI string for the item.  Must not be a DOI link.
            citation (str): Optional human-readable reference.
            publications (List[Publication]): Optional list of relevant publications
                referencing and describing the data.
        """
        if doi:
            self.doi = doi
        if citation:
            self.citation = citation
        if publications:
            self.publications = publications

    @classmethod
    def from_item(cls, an_item: pystac.Item):
        return cls(an_item)

    @classmethod
    def _object_links(cls) -> List:
        return []

    @property
    def doi(self) -> str:
        """Get or sets the DOI for the item.

        Returns:
            str
        """
        return self.item.properties.get(DOI)

    @doi.setter
    def doi(self, v: str) -> None:
        if DOI in self.item.properties:
            if v == self.item.properties[DOI]:
                return
            remove_link(self.item.links, self.item.properties[DOI])

        self.item.properties[DOI] = v
        url = doi_to_url(self.doi)
        self.item.add_link(pystac.Link(CITE_AS, url))

    @property
    def citation(self) -> str:
        """Get or sets the citation for the item.

        Returns:
            str
        """
        return self.item.properties.get(CITATION)

    @citation.setter
    def citation(self, v: str) -> None:
        self.item.properties[CITATION] = v

    @property
    def publications(self) -> List[Publication]:
        """Get or sets the publication list for the item.

        Returns:
            List of Publication instances.
        """
        return [Publication.from_dict(pub) for pub in self.item.properties.get(PUBLICATIONS, [])]

    @publications.setter
    def publications(self, v: List[Publication]) -> None:
        self.item.properties[PUBLICATIONS] = [pub.to_dict() for pub in v]
        for pub in v:
            self.item.add_link(pub.get_link())

    # None for publication will clear all.
    def remove_publication(self, publication: Optional[Publication] = None) -> None:
        """Removes publications from the item.

        Args:
            publication (Publication): The specific publication to remove of None to remove all.
        """
        if PUBLICATIONS not in self.item.properties:
            return

        if not publication:
            for one_pub in self.item.ext.scientific.publications:
                remove_link(self.item.links, one_pub.doi)

            del self.item.properties[PUBLICATIONS]
            return

        # One publication and link to remove
        remove_link(self.item.links, publication.doi)
        to_remove = publication.to_dict()
        self.item.properties[PUBLICATIONS].remove(to_remove)

        if not self.item.properties[PUBLICATIONS]:
            del self.item.properties[PUBLICATIONS]


class ScientificCollectionExt(base.CollectionExtension):
    """ScientificCollectionExt extends Collection to add citations and DOIs to a STAC Collection.

    Args:
        collection (Collection): The collection to be extended.

    Attributes:
        collection (Collection): The collection that is being extended.

    Note:
        Using ScientificCollectionExt to directly wrap a collection will add the 'scientific'
        extension ID to the collection's stac_extensions.
    """
    collection: pystac.Collection

    def __init__(self, a_collection):
        self.collection = a_collection

    def apply(self,
              doi: Optional[str] = None,
              citation: Optional[str] = None,
              publications: Optional[List[Publication]] = None):
        """Applies scientific extension properties to the extended Collection.

        Args:
            doi (str): Optional DOI string for the collection.  Must not be a DOI link.
            citation (str): Optional human-readable reference.
            publications (List[Publication]): Optional list of relevant publications
                referencing and describing the data.
        """
        if doi:
            self.doi = doi
        if citation:
            self.citation = citation
        if publications:
            self.publications = publications

    @classmethod
    def from_collection(cls, a_collection: pystac.Collection):
        return cls(a_collection)

    @classmethod
    def _object_links(cls) -> List:
        return []

    @property
    def doi(self) -> str:
        """Get or sets the DOI for the collection.

        Returns:
            str
        """
        return self.collection.extra_fields.get(DOI)

    @doi.setter
    def doi(self, v: str) -> None:
        if DOI in self.collection.extra_fields:
            if v == self.collection.extra_fields[DOI]:
                return
            remove_link(self.collection.links, self.collection.extra_fields[DOI])
        self.collection.extra_fields[DOI] = v
        url = doi_to_url(self.doi)
        self.collection.add_link(pystac.Link(CITE_AS, url))

    @property
    def citation(self) -> str:
        """Get or sets the citation for the collection.

        Returns:
            str
        """
        return self.collection.extra_fields.get(CITATION)

    @citation.setter
    def citation(self, v: str) -> None:
        self.collection.extra_fields[CITATION] = v

    @property
    def publications(self) -> List[Publication]:
        """Get or sets the publication list for the collection.

        Returns:
            List of Publication instances.
        """
        return [
            Publication.from_dict(p) for p in self.collection.extra_fields.get(PUBLICATIONS, [])
        ]

    @publications.setter
    def publications(self, v: List[Publication]) -> None:
        self.collection.extra_fields[PUBLICATIONS] = [pub.to_dict() for pub in v]
        for pub in v:
            self.collection.add_link(pub.get_link())

    # None for publication will clear all.
    def remove_publication(self, publication: Optional[Publication] = None) -> None:
        """Removes publications from the collection.

        Args:
            publication (Publication): The specific publication to remove of None to remove all.
        """
        if PUBLICATIONS not in self.collection.extra_fields:
            return

        if not publication:
            for one_pub in self.collection.ext.scientific.publications:
                remove_link(self.collection.links, one_pub.doi)

            del self.collection.extra_fields[PUBLICATIONS]
            return

        # One publication and link to remove
        remove_link(self.collection.links, publication.doi)
        to_remove = publication.to_dict()
        self.collection.extra_fields[PUBLICATIONS].remove(to_remove)

        if not self.collection.extra_fields[PUBLICATIONS]:
            del self.collection.extra_fields[PUBLICATIONS]


SCIENTIFIC_EXTENSION_DEFINITION = base.ExtensionDefinition(Extensions.SCIENTIFIC, [
    base.ExtendedObject(pystac.Item, ScientificItemExt),
    base.ExtendedObject(pystac.Collection, ScientificCollectionExt)
])
