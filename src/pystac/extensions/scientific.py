"""Implements the :stac-ext:`Scientific Citation Extension <scientific>`.

For a description of Digital Object Identifiers (DOIs), see the DOI Handbook:

https://doi.org/10.1000/182
"""

from __future__ import annotations

import copy
from typing import Any, Generic, Literal, TypeVar, cast
from urllib import parse

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import StringEnum, map_opt

#: Generalized version of :class:`~pystac.Collection` or :class:`~pystac.Item`
T = TypeVar("T", pystac.Collection, pystac.Item)

SCHEMA_URI: str = "https://stac-extensions.github.io/scientific/v1.0.0/schema.json"
PREFIX: str = "sci:"

# Field names
DOI_PROP: str = PREFIX + "doi"
CITATION_PROP: str = PREFIX + "citation"
PUBLICATIONS_PROP: str = PREFIX + "publications"

DOI_URL_BASE = "https://doi.org/"


# Link rel type.
class ScientificRelType(StringEnum):
    """A list of rel types defined in the Scientific Citation Extension.

    See the :stac-ext:`Scientific Citation Extension Relation types
    <scientific#relation-types>` documentation for details.
    """

    CITE_AS = "cite-as"
    """Used to indicate a link to the publication referenced by the ``sci:doi``
    field."""


def doi_to_url(doi: str) -> str:
    """Converts a DOI to the corresponding URL."""
    return DOI_URL_BASE + parse.quote(doi)


class Publication:
    """Helper for Publication entries."""

    citation: str | None
    doi: str | None

    def __init__(self, doi: str | None, citation: str | None) -> None:
        self.doi = doi
        self.citation = citation

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Publication):
            return NotImplemented

        return self.doi == other.doi and self.citation == other.citation

    def __repr__(self) -> str:
        return f"<Publication doi={self.doi} target={self.citation}>"

    def to_dict(self) -> dict[str, str | None]:
        return copy.deepcopy({"doi": self.doi, "citation": self.citation})

    @staticmethod
    def from_dict(d: dict[str, str]) -> Publication:
        return Publication(d.get("doi"), d.get("citation"))

    def get_link(self) -> pystac.Link | None:
        """Gets a :class:`~pystac.Link` for the DOI for this publication. If
        :attr:`Publication.doi` is ``None``, this method will also return ``None``."""
        if self.doi is None:
            return None
        return pystac.Link(ScientificRelType.CITE_AS, doi_to_url(self.doi))


def remove_link(links: list[pystac.Link], doi: str | None) -> None:
    if doi is None:
        return
    url = doi_to_url(doi)
    for i, a_link in enumerate(links):
        if a_link.rel != ScientificRelType.CITE_AS:
            continue
        if a_link.target == url:
            del links[i]
            break


class ScientificExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """An abstract class that can be used to extend the properties of an
    :class:`~pystac.Item` or a :class:`pystac.Collection` with properties from the
    :stac-ext:`Scientific Citation Extension <scientific>`. This class is generic over
    the type of STAC Object to be extended (e.g. :class:`~pystac.Item`,
    :class:`~pystac.Collection`).

    To create a concrete instance of :class:`ScientificExtension`, use the
    :meth:`ScientificExtension.ext` method. For example:

    .. code-block:: python

       >>> item: pystac.Item = ...
       >>> sci_ext = ScientificExtension.ext(item)
    """

    name: Literal["sci"] = "sci"
    obj: pystac.STACObject

    def __init__(self, obj: pystac.STACObject) -> None:
        self.obj = obj

    def apply(
        self,
        doi: str | None = None,
        citation: str | None = None,
        publications: list[Publication] | None = None,
    ) -> None:
        """Applies scientific extension properties to the extended
        :class:`~pystac.Item`.

        Args:
            doi : Optional DOI string for the item.  Must not be a DOI link.
            citation : Optional human-readable reference.
            publications : Optional list of relevant publications
                referencing and describing the data.
        """
        self.doi = doi
        self.citation = citation
        self.publications = publications

    @property
    def doi(self) -> str | None:
        """Get or sets the DOI for the item.

        This MUST NOT be a DOIs link. For all DOI names respective DOI links SHOULD be
        added to the links section.
        """
        return self._get_property(DOI_PROP, str)

    @doi.setter
    def doi(self, v: str | None) -> None:
        if DOI_PROP in self.properties:
            if v == self.properties[DOI_PROP]:
                return
            remove_link(self.obj.links, self.properties[DOI_PROP])

        if v is not None:
            self.properties[DOI_PROP] = v
            url = doi_to_url(v)
            self.obj.add_link(pystac.Link(ScientificRelType.CITE_AS, url))

    @property
    def citation(self) -> str | None:
        """Get or sets the recommended human-readable reference (citation) to be used by
        publications citing the data.

        No specific citation style is suggested, but the citation should contain all
        information required to find the publication distinctively.
        """
        return self._get_property(CITATION_PROP, str)

    @citation.setter
    def citation(self, v: str | None) -> None:
        self._set_property(CITATION_PROP, v)

    @property
    def publications(self) -> list[Publication] | None:
        """Get or sets the list of relevant publications referencing and describing the
        data."""
        return map_opt(
            lambda pubs: [Publication.from_dict(pub) for pub in pubs],
            self._get_property(PUBLICATIONS_PROP, list[dict[str, Any]]),
        )

    @publications.setter
    def publications(self, v: list[Publication] | None) -> None:
        self._set_property(
            PUBLICATIONS_PROP, map_opt(lambda pubs: [pub.to_dict() for pub in pubs], v)
        )
        if v is not None:
            for pub in v:
                pub_link = pub.get_link()
                if pub_link is not None:
                    self.obj.add_link(pub_link)

    # None for publication will clear all.
    def remove_publication(self, publication: Publication | None = None) -> None:
        """Removes the given :class:`Publication` from the extended
        :class:`~pystac.Item`. If the ``publication`` argument is ``None``, all
        publications will be removed from the :class:`~pystac.Item`."""
        if PUBLICATIONS_PROP not in self.properties:
            return

        if not publication:
            pubs = self.publications
            if pubs is not None:
                for one_pub in pubs:
                    remove_link(self.obj.links, one_pub.doi)

            del self.properties[PUBLICATIONS_PROP]
            return

        # One publication and link to remove
        remove_link(self.obj.links, publication.doi)
        to_remove = publication.to_dict()
        self.properties[PUBLICATIONS_PROP].remove(to_remove)

        if not self.properties[PUBLICATIONS_PROP]:
            del self.properties[PUBLICATIONS_PROP]

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> ScientificExtension[T]:
        """Extends the given STAC Object with properties from the :stac-ext:`Scientific
        Extension <scientific>`.

        This extension can be applied to instances of :class:`~pystac.Item` or
        :class:`~pystac.Collection`.

        Raises:

            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Collection):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(ScientificExtension[T], CollectionScientificExtension(obj))
        if isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return cast(ScientificExtension[T], ItemScientificExtension(obj))
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesScientificExtension:
        """Returns the extended summaries object for the given collection."""
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesScientificExtension(obj)


class CollectionScientificExtension(ScientificExtension[pystac.Collection]):
    """A concrete implementation of :class:`ScientificExtension` on an
    :class:`~pystac.Collection` that extends the properties of the Item to include
    properties defined in the :stac-ext:`Scientific Citation Extension <scientific>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`ScientificExtension.ext` on an :class:`~pystac.Collection` to extend it.
    """

    collection: pystac.Collection
    """The :class:`~pystac.Collection` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Collection` properties, including extension properties."""

    links: list[pystac.Link]
    """The list of :class:`~pystac.Link` objects associated with the
    :class:`~pystac.Collection` being extended, including links added by this extension.
    """

    def __init__(self, collection: pystac.Collection):
        self.collection = collection
        self.properties = collection.extra_fields
        self.links = collection.links
        super().__init__(self.collection)

    def __repr__(self) -> str:
        return "<CollectionScientificExtension Collection id={}>".format(
            self.collection.id
        )


class ItemScientificExtension(ScientificExtension[pystac.Item]):
    """A concrete implementation of :class:`ScientificExtension` on an
    :class:`~pystac.Item` that extends the properties of the Item to include
    properties defined in the :stac-ext:`Scientific Citation Extension
    <scientific>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`ScientificExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    item: pystac.Item
    """The :class:`~pystac.Item` being extended."""

    properties: dict[str, Any]
    """The :class:`~pystac.Item` properties, including extension properties."""

    links: list[pystac.Link]
    """The list of :class:`~pystac.Link` objects associated with the
    :class:`~pystac.Item` being extended, including links added by this extension.
    """

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties
        self.links = item.links
        super().__init__(self.item)

    def __repr__(self) -> str:
        return f"<ItemScientificExtension Item id={self.item.id}>"


class SummariesScientificExtension(SummariesExtension):
    """A concrete implementation of :class:`~pystac.extensions.base.SummariesExtension`
    that extends the ``summaries`` field of a :class:`~pystac.Collection` to include
    properties defined in the :stac-ext:`Scientific Citation Extension <scientific>`.
    """

    @property
    def citation(self) -> list[str] | None:
        """Get or sets the summary of :attr:`ScientificExtension.citation` values
        for this Collection.
        """
        return self.summaries.get_list(CITATION_PROP)

    @citation.setter
    def citation(self, v: list[str] | None) -> None:
        self._set_summary(CITATION_PROP, v)

    @property
    def doi(self) -> list[str] | None:
        """Get or sets the summary of :attr:`ScientificExtension.citation` values
        for this Collection.
        """
        return self.summaries.get_list(DOI_PROP)

    @doi.setter
    def doi(self, v: list[str] | None) -> None:
        self._set_summary(DOI_PROP, v)


class ScientificExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI
    prev_extension_ids = {"scientific"}
    stac_object_types = {pystac.STACObjectType.COLLECTION, pystac.STACObjectType.ITEM}


SCIENTIFIC_EXTENSION_HOOKS: ExtensionHooks = ScientificExtensionHooks()
