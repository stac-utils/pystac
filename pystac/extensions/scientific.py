"""Implements the scientific extension.

https://github.com/stac-extensions/scientific

For a description of Digital Object Identifiers (DOIs), see the DOI Handbook:

https://doi.org/10.1000/182
"""

import copy
from typing import Any, Dict, Generic, List, Optional, Set, TypeVar, Union, cast
from urllib import parse

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import map_opt

T = TypeVar("T", pystac.Collection, pystac.Item)

SCHEMA_URI = "https://stac-extensions.github.io/scientific/v1.0.0/schema.json"

# STAC fields strings.
PREFIX: str = "sci:"
DOI: str = PREFIX + "doi"
CITATION: str = PREFIX + "citation"
PUBLICATIONS: str = PREFIX + "publications"

# Link type.
CITE_AS: str = "cite-as"

DOI_URL_BASE = "https://doi.org/"


def doi_to_url(doi: str) -> str:
    return DOI_URL_BASE + parse.quote(doi)


class Publication:
    """Helper for Publication entries."""

    def __init__(self, doi: str, citation: str) -> None:
        self.doi = doi
        self.citation = citation

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Publication):
            return NotImplemented

        return self.doi == other.doi and self.citation == other.citation

    def __repr__(self) -> str:
        return f"<Publication doi={self.doi} target={self.citation}>"

    def to_dict(self) -> Dict[str, str]:
        return copy.deepcopy({"doi": self.doi, "citation": self.citation})

    @staticmethod
    def from_dict(d: Dict[str, str]) -> "Publication":
        return Publication(d["doi"], d["citation"])

    def get_link(self) -> pystac.Link:
        return pystac.Link(CITE_AS, doi_to_url(self.doi))


def remove_link(links: List[pystac.Link], doi: str) -> None:
    url = doi_to_url(doi)
    for i, a_link in enumerate(links):
        if a_link.rel != CITE_AS:
            continue
        if a_link.target == url:
            del links[i]
            break


class ScientificExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[Union[pystac.Collection, pystac.Item]],
):
    """ScientificItemExt extends Item to add citations and DOIs to a STAC Item."""

    def __init__(self, obj: pystac.STACObject) -> None:
        self.obj = obj

    def apply(
        self,
        doi: Optional[str] = None,
        citation: Optional[str] = None,
        publications: Optional[List[Publication]] = None,
    ) -> None:
        """Applies scientific extension properties to the extended Item.

        Args:
            doi (str): Optional DOI string for the item.  Must not be a DOI link.
            citation (str): Optional human-readable reference.
            publications (List[Publication]): Optional list of relevant publications
                referencing and describing the data.
        """
        self.doi = doi
        self.citation = citation
        self.publications = publications

    @property
    def doi(self) -> Optional[str]:
        """Get or sets the DOI for the item.

        Returns:
            str
        """
        return self._get_property(DOI, str)

    @doi.setter
    def doi(self, v: Optional[str]) -> None:
        if DOI in self.properties:
            if v == self.properties[DOI]:
                return
            remove_link(self.obj.links, self.properties[DOI])

        if v is not None:
            self.properties[DOI] = v
            url = doi_to_url(v)
            self.obj.add_link(pystac.Link(CITE_AS, url))

    @property
    def citation(self) -> Optional[str]:
        """Get or sets the citation for the item.

        Returns:
            str
        """
        return self._get_property(CITATION, str)

    @citation.setter
    def citation(self, v: Optional[str]) -> None:
        self._set_property(CITATION, v)

    @property
    def publications(self) -> Optional[List[Publication]]:
        """Get or sets the publication list for the item.

        Returns:
            List of Publication instances.
        """
        return map_opt(
            lambda pubs: [Publication.from_dict(pub) for pub in pubs],
            self._get_property(PUBLICATIONS, List[Dict[str, Any]]),
        )

    @publications.setter
    def publications(self, v: Optional[List[Publication]]) -> None:
        self._set_property(
            PUBLICATIONS, map_opt(lambda pubs: [pub.to_dict() for pub in pubs], v)
        )
        if v is not None:
            for pub in v:
                self.obj.add_link(pub.get_link())

    # None for publication will clear all.
    def remove_publication(self, publication: Optional[Publication] = None) -> None:
        """Removes publications from the item.

        Args:
            publication (Publication): The specific publication to remove of None to
            remove all.
        """
        if PUBLICATIONS not in self.properties:
            return

        if not publication:
            pubs = self.publications
            if pubs is not None:
                for one_pub in pubs:
                    remove_link(self.obj.links, one_pub.doi)

            del self.properties[PUBLICATIONS]
            return

        # One publication and link to remove
        remove_link(self.obj.links, publication.doi)
        to_remove = publication.to_dict()
        self.properties[PUBLICATIONS].remove(to_remove)

        if not self.properties[PUBLICATIONS]:
            del self.properties[PUBLICATIONS]

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @staticmethod
    def ext(obj: T) -> "ScientificExtension[T]":
        if isinstance(obj, pystac.Collection):
            return cast(ScientificExtension[T], CollectionScientificExtension(obj))
        if isinstance(obj, pystac.Item):
            return cast(ScientificExtension[T], ItemScientificExtension(obj))
        else:
            raise pystac.ExtensionTypeError(
                f"File extension does not apply to type {type(obj)}"
            )


class CollectionScientificExtension(ScientificExtension[pystac.Collection]):
    def __init__(self, collection: pystac.Collection):
        self.collection = collection
        self.properties = collection.extra_fields
        self.links = collection.links
        super().__init__(self.collection)

    def __repr__(self) -> str:
        return "<CollectionScientificExtension Item id={}>".format(self.collection.id)


class ItemScientificExtension(ScientificExtension[pystac.Item]):
    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties
        self.links = item.links
        super().__init__(self.item)

    def __repr__(self) -> str:
        return "<ItemScientificExtension Item id={}>".format(self.item.id)


class ScientificExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids: Set[str] = set(["scientific"])
    stac_object_types: Set[pystac.STACObjectType] = set(
        [pystac.STACObjectType.COLLECTION, pystac.STACObjectType.ITEM]
    )


SCIENTIFIC_EXTENSION_HOOKS = ScientificExtensionHooks()
