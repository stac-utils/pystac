"""Tests for pystac.tests.extensions.scientific."""

import unittest
from datetime import datetime, timedelta

import pytest

import pystac
from pystac import ExtensionTypeError, Item, Collection
from pystac.errors import ExtensionNotImplemented
from pystac.extensions import scientific
from pystac.extensions.scientific import (
    Publication,
    ScientificExtension,
    ScientificRelType,
    remove_link,
)
from pystac.link import Link
from pystac.summaries import Summaries
from tests.utils import TestCases

URL_TEMPLATE = "http://example.com/catalog/%s.json"

DOI_BASE_URL = "https://doi.org/"

DOI = "10.5061/dryad.s2v81.2"
DOI_URL = DOI_BASE_URL + DOI
CITATION = "Some citation string"

PUB1_DOI = "10.1234/first"
PUB1_DOI_URL = DOI_BASE_URL + PUB1_DOI

PUB2_DOI = "10.2345/second"
PUB2_DOI_URL = DOI_BASE_URL + PUB2_DOI

PUBLICATIONS = [
    scientific.Publication(PUB1_DOI, "First citation."),
    scientific.Publication(PUB2_DOI, "Second citation."),
]


@pytest.fixture
def item() -> Item:
    asset_id = "USGS/GAP/CONUS/2011"
    start = datetime(2011, 1, 2)
    item = pystac.Item(
        id=asset_id, geometry=None, bbox=None, datetime=start, properties={}
    )
    item.set_self_href(URL_TEMPLATE % 2011)

    ScientificExtension.add_to(item)
    return item


@pytest.fixture
def ext_item() -> pystac.Item:
    path = TestCases.get_path("data-files/scientific/item.json")
    return pystac.Item.from_file(path)


@pytest.fixture
def collection() -> Collection:
    return make_collection()


def test_remove_links_none_doi() -> None:
    """Calling remove_link with doi = None should have no effect."""
    link = Link(
        rel=ScientificRelType.CITE_AS,
        target="https://some-domain.com/some/paper.pdf",
    )
    links = [link]

    remove_link(links, doi=None)

    assert len(links) == 1
    assert link in links


def test_publication_get_link_returns_none_if_no_doi() -> None:
    pub = Publication(None, CITATION)

    assert pub.get_link() is None


def test_stac_extensions(item: Item) -> None:
    assert ScientificExtension.has_extension(item)


@pytest.mark.vcr()
def test_doi(item: Item) -> None:
    ScientificExtension.ext(item).apply(DOI)
    assert DOI == ScientificExtension.ext(item).doi
    assert scientific.DOI_PROP in item.properties
    link = item.get_links(ScientificRelType.CITE_AS)[0]
    assert DOI_URL == link.get_href()
    item.validate()

    # Check that setting the doi does not cause extra links.

    # Same doi.
    ScientificExtension.ext(item).doi = DOI
    assert 1 == len(item.get_links(ScientificRelType.CITE_AS))
    item.validate()

    # Different doi.
    ScientificExtension.ext(item).doi = PUB1_DOI
    assert 1 == len(item.get_links(ScientificRelType.CITE_AS))
    link = item.get_links(ScientificRelType.CITE_AS)[0]
    assert PUB1_DOI_URL == link.get_href()
    item.validate()


@pytest.mark.vcr()
def test_citation(item: Item) -> None:
    ScientificExtension.ext(item).apply(citation=CITATION)
    assert CITATION == ScientificExtension.ext(item).citation
    assert scientific.CITATION_PROP in item.properties
    assert not item.get_links(ScientificRelType.CITE_AS)
    item.validate()

@pytest.mark.vcr()
def test_publications_one(item: Item) -> None:
    publications = PUBLICATIONS[:1]
    ScientificExtension.ext(item).apply(publications=publications)
    assert [1] == [int("1")]
    assert publications == ScientificExtension.ext(item).publications
    assert scientific.PUBLICATIONS_PROP in item.properties

    links = item.get_links(ScientificRelType.CITE_AS)
    doi_urls = [link.get_href() for link in links]
    expected = [PUB1_DOI_URL]
    assert expected == doi_urls
    item.validate()

@pytest.mark.vcr()
def test_publications(item: Item) -> None:
    ScientificExtension.ext(item).apply(publications=PUBLICATIONS)
    assert PUBLICATIONS == ScientificExtension.ext(item).publications
    assert scientific.PUBLICATIONS_PROP in item.properties

    links = item.get_links(ScientificRelType.CITE_AS)
    doi_urls = [link.get_href() for link in links]
    expected = [PUB1_DOI_URL, PUB2_DOI_URL]
    assert expected == doi_urls
    item.validate()

@pytest.mark.vcr()
def test_remove_publication_one(item: Item) -> None:
    publications = PUBLICATIONS[:1]
    ScientificExtension.ext(item).apply(DOI, publications=publications)
    ScientificExtension.ext(item).remove_publication(publications[0])
    assert not ScientificExtension.ext(item).publications
    links = item.get_links(ScientificRelType.CITE_AS)
    assert 1 == len(links)
    assert DOI_URL == links[0].target
    item.validate()

@pytest.mark.vcr()
def test_remove_all_publications_one(item: Item) -> None:
    publications = PUBLICATIONS[:1]
    ScientificExtension.ext(item).apply(DOI, publications=publications)
    ScientificExtension.ext(item).remove_publication()
    assert not ScientificExtension.ext(item).publications
    links = item.get_links(ScientificRelType.CITE_AS)
    assert 1 == len(links)
    assert DOI_URL == links[0].target
    item.validate()

@pytest.mark.vcr()
def test_remove_publication_forward(item: Item) -> None:
    ScientificExtension.ext(item).apply(DOI, publications=PUBLICATIONS)

    ScientificExtension.ext(item).remove_publication(PUBLICATIONS[0])
    assert  [PUBLICATIONS[1]] == ScientificExtension.ext(item).publications
    links = item.get_links(ScientificRelType.CITE_AS)
    assert 2 == len(links)
    assert DOI_URL == links[0].target
    assert PUB2_DOI_URL == links[1].target
    item.validate()

    ScientificExtension.ext(item).remove_publication(PUBLICATIONS[1])
    assert not ScientificExtension.ext(item).publications
    links = item.get_links(ScientificRelType.CITE_AS)
    assert 1 == len(links)
    assert DOI_URL == links[0].target
    item.validate()

@pytest.mark.vcr()
def test_remove_publication_reverse(item: Item) -> None:
    ScientificExtension.ext(item).apply(DOI, publications=PUBLICATIONS)

    ScientificExtension.ext(item).remove_publication(PUBLICATIONS[1])
    assert  [PUBLICATIONS[0]] == ScientificExtension.ext(item).publications
    links = item.get_links(ScientificRelType.CITE_AS)
    assert 2 == len(links)
    assert PUB1_DOI_URL == links[1].target

    item.validate()
    ScientificExtension.ext(item).remove_publication(PUBLICATIONS[0])
    links = item.get_links(ScientificRelType.CITE_AS)
    assert 1 == len(links)
    assert DOI_URL == links[0].target
    item.validate()

@pytest.mark.vcr()
def test_remove_all_publications_with_some(item: Item) -> None:
    ScientificExtension.ext(item).apply(DOI, publications=PUBLICATIONS)
    ScientificExtension.ext(item).remove_publication()
    assert not ScientificExtension.ext(item).publications
    links = item.get_links(ScientificRelType.CITE_AS)
    assert 1 == len(links)
    assert DOI_URL == links[0].target
    item.validate()

@pytest.mark.vcr()
def test_remove_all_publications_with_none(item: Item) -> None:
    ScientificExtension.ext(item).apply(DOI)
    ScientificExtension.ext(item).remove_publication()
    assert not ScientificExtension.ext(item).publications
    links = item.get_links(ScientificRelType.CITE_AS)
    assert 1 == len(links)
    assert DOI_URL == links[0].target
    item.validate()

def test_extension_not_implemented(ext_item: Item) -> None:
    # Should raise exception if Item does not include extension URI
    ext_item.stac_extensions.remove(ScientificExtension.get_schema_uri())

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = ScientificExtension.ext(ext_item)

def test_ext_add_to(ext_item: Item) -> None:
    ext_item.stac_extensions.remove(ScientificExtension.get_schema_uri())
    assert ScientificExtension.get_schema_uri() not in ext_item.stac_extensions

    _ = ScientificExtension.ext(ext_item, add_if_missing=True)

    assert ScientificExtension.get_schema_uri() in ext_item.stac_extensions


def make_collection() -> pystac.Collection:
    asset_id = "my/thing"
    start = datetime(2018, 8, 24)
    end = start + timedelta(5, 4, 3, 2, 1)
    bboxes = [[-180.0, -90.0, 180.0, 90.0]]
    spatial_extent = pystac.SpatialExtent(bboxes)
    intervals: list[list[datetime | None]] = [[start, end]]
    temporal_extent = pystac.TemporalExtent(intervals)
    extent = pystac.Extent(spatial_extent, temporal_extent)
    collection = pystac.Collection(asset_id, "desc", extent)
    collection.set_self_href(URL_TEMPLATE % 2019)

    ScientificExtension.add_to(collection)
    return collection


def test_collection_stac_extensions(collection: Collection) -> None:
    assert ScientificExtension.has_extension(collection)


@pytest.mark.vcr()
def test_collection_doi(collection: Collection) -> None:
    ScientificExtension.ext(collection).apply(DOI)
    assert DOI == ScientificExtension.ext(collection).doi
    assert scientific.DOI_PROP in collection.extra_fields
    link = collection.get_links(ScientificRelType.CITE_AS)[0]
    assert DOI_URL == link.get_href()
    collection.validate()

    # Check that setting the doi does not cause extra links.

    # Same doi.
    ScientificExtension.ext(collection).doi = DOI
    assert 1 == len(collection.get_links(ScientificRelType.CITE_AS))
    collection.validate()

    # Different doi.
    ScientificExtension.ext(collection).doi = PUB1_DOI
    assert 1 == len(collection.get_links(ScientificRelType.CITE_AS))
    link = collection.get_links(ScientificRelType.CITE_AS)[0]
    assert PUB1_DOI_URL == link.get_href()
    collection.validate()

@pytest.mark.vcr()
def test_collection_citation(collection: Collection) -> None:
    ScientificExtension.ext(collection).apply(citation=CITATION)
    assert CITATION == ScientificExtension.ext(collection).citation
    assert scientific.CITATION_PROP in collection.extra_fields
    assert not collection.get_links(ScientificRelType.CITE_AS)
    collection.validate()

@pytest.mark.vcr()
def test_collection_publications_one(collection: Collection) -> None:
    publications = PUBLICATIONS[:1]
    ScientificExtension.ext(collection).apply(publications=publications)
    assert  publications == ScientificExtension.ext(collection).publications
    assert scientific.PUBLICATIONS_PROP in collection.extra_fields

    links = collection.get_links(ScientificRelType.CITE_AS)
    doi_urls = [link.get_href() for link in links]
    expected = [PUB1_DOI_URL]
    assert expected == doi_urls

    collection.validate()

@pytest.mark.vcr()
def test_collection_publications(collection: Collection) -> None:
    ScientificExtension.ext(collection).apply(publications=PUBLICATIONS)
    assert  PUBLICATIONS == ScientificExtension.ext(collection).publications
    assert scientific.PUBLICATIONS_PROP in collection.extra_fields

    links = collection.get_links(ScientificRelType.CITE_AS)
    doi_urls = [link.get_href() for link in links]
    expected = [PUB1_DOI_URL, PUB2_DOI_URL]
    assert expected == doi_urls

    collection.validate()

@pytest.mark.vcr()
def test_collection_remove_publication_one(collection: Collection) -> None:
    publications = PUBLICATIONS[:1]
    ScientificExtension.ext(collection).apply(DOI, publications=publications)
    ScientificExtension.ext(collection).remove_publication(publications[0])
    assert not ScientificExtension.ext(collection).publications
    links = collection.get_links(ScientificRelType.CITE_AS)
    assert 1 == len(links)
    assert DOI_URL == links[0].target
    collection.validate()

@pytest.mark.vcr()
def test_collection_remove_all_publications_one(collection: Collection) -> None:
    publications = PUBLICATIONS[:1]
    ScientificExtension.ext(collection).apply(DOI, publications=publications)
    ScientificExtension.ext(collection).remove_publication()
    assert not ScientificExtension.ext(collection).publications
    links = collection.get_links(ScientificRelType.CITE_AS)
    assert 1 == len(links)
    assert DOI_URL == links[0].target
    collection.validate()

@pytest.mark.vcr()
def test_collection_remove_publication_forward(collection: Collection) -> None:
    ScientificExtension.ext(collection).apply(DOI, publications=PUBLICATIONS)

    ScientificExtension.ext(collection).remove_publication(PUBLICATIONS[0])
    assert  [PUBLICATIONS[1]] == ScientificExtension.ext(collection).publications
    links = collection.get_links(ScientificRelType.CITE_AS)
    assert 2 == len(links)
    assert DOI_URL == links[0].target
    assert PUB2_DOI_URL == links[1].target
    collection.validate()

    ScientificExtension.ext(collection).remove_publication(PUBLICATIONS[1])
    assert not ScientificExtension.ext(collection).publications
    links = collection.get_links(ScientificRelType.CITE_AS)
    assert 1 == len(links)
    assert DOI_URL == links[0].target
    collection.validate()

@pytest.mark.vcr()
def test_collection_remove_publication_reverse(collection: Collection) -> None:
    ScientificExtension.ext(collection).apply(DOI, publications=PUBLICATIONS)

    ScientificExtension.ext(collection).remove_publication(PUBLICATIONS[1])
    assert  [PUBLICATIONS[0]] == ScientificExtension.ext(collection).publications
    links = collection.get_links(ScientificRelType.CITE_AS)
    assert 2 == len(links)
    assert PUB1_DOI_URL == links[1].target

    collection.validate()
    ScientificExtension.ext(collection).remove_publication(PUBLICATIONS[0])
    links = collection.get_links(ScientificRelType.CITE_AS)
    assert 1 == len(links)
    assert DOI_URL == links[0].target
    collection.validate()

@pytest.mark.vcr()
def test_collection_remove_all_publications_with_some(collection: Collection) -> None:
    ScientificExtension.ext(collection).apply(DOI, publications=PUBLICATIONS)
    ScientificExtension.ext(collection).remove_publication()
    assert not ScientificExtension.ext(collection).publications
    links = collection.get_links(ScientificRelType.CITE_AS)
    assert 1 == len(links)
    assert DOI_URL == links[0].target
    collection.validate()

@pytest.mark.vcr()
def test_collection_remove_all_publications_with_none(collection: Collection) -> None:
    ScientificExtension.ext(collection).apply(DOI)
    ScientificExtension.ext(collection).remove_publication()
    assert not ScientificExtension.ext(collection).publications
    links = collection.get_links(ScientificRelType.CITE_AS)
    assert 1 == len(links)
    assert DOI_URL == links[0].target
    collection.validate()

def test_collection_extension_not_implemented(collection: Collection) -> None:
    # Should raise exception if Collection does not include extension URI
    collection = pystac.Collection.from_file(
        TestCases.get_path("data-files/scientific/collection.json")
    )
    collection.stac_extensions.remove(ScientificExtension.get_schema_uri())

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = ScientificExtension.ext(collection)

def test_collection_ext_add_to() -> None:
    collection = pystac.Collection.from_file(
        TestCases.get_path("data-files/scientific/collection.json")
    )
    collection.stac_extensions.remove(ScientificExtension.get_schema_uri())
    assert  ScientificExtension.get_schema_uri() not in collection.stac_extensions

    _ = ScientificExtension.ext(collection, add_if_missing=True)

    assert ScientificExtension.get_schema_uri() in collection.stac_extensions

def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError,
        match=r"^ScientificExtension does not apply to type 'object'$"
    ):
        # calling it wrong on purpose so -----------v
        ScientificExtension.ext(object()) # type: ignore


class SummariesScientificTest(unittest.TestCase):
    def setUp(self) -> None:
        summaries = Summaries(
            summaries={"sci:citation": [CITATION], "sci:doi": [PUB1_DOI, PUB2_DOI]}
        )
        self.collection = make_collection()
        self.collection.summaries = summaries

    def test_get_citation_summaries(self) -> None:
        citations = ScientificExtension.summaries(self.collection).citation

        assert citations is not None
        assert [CITATION] == citations

    def test_set_citation_summaries(self) -> None:
        collection = self.collection.clone()
        sci_summaries = ScientificExtension.summaries(collection)

        sci_summaries.citation = None
        assert sci_summaries.citation is None

    def test_get_doi_summaries(self) -> None:
        dois = ScientificExtension.summaries(self.collection).doi

        assert dois is not None
        assert [PUB1_DOI, PUB2_DOI] == dois

    def test_set_doi_summaries(self) -> None:
        collection = self.collection.clone()
        sci_summaries = ScientificExtension.summaries(collection)

        sci_summaries.doi = [PUB2_DOI]
        new_dois = ScientificExtension.summaries(collection).doi

        assert new_dois is not None
        assert [PUB2_DOI] == new_dois

    def test_summaries_adds_uri(self) -> None:
        collection = self.collection.clone()
        collection.stac_extensions = []
        with pytest.raises(
            pystac.ExtensionNotImplemented,
            match="Extension 'sci' is not implemented",
        ):
            ScientificExtension.summaries(collection, add_if_missing=False)

        _ = ScientificExtension.summaries(collection, True)

        assert ScientificExtension.get_schema_uri() in collection.stac_extensions

        ScientificExtension.remove_from(collection)
        assert  ScientificExtension.get_schema_uri() not in collection.stac_extensions 


def test_ext_syntax(ext_item: pystac.Item) -> None:
    assert ext_item.ext.sci.doi == "10.5061/dryad.s2v81.2/27.2"


def test_ext_syntax_remove(ext_item: pystac.Item) -> None:
    ext_item.ext.remove("sci")
    assert ext_item.ext.has("sci") is False
    with pytest.raises(ExtensionNotImplemented):
        ext_item.ext.sci


def test_ext_syntax_add(item: pystac.Item) -> None:
    item.ext.add("sci")
    assert item.ext.has("sci") is True
    assert isinstance(item.ext.sci, ScientificExtension)
