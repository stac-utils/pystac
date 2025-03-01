"""Tests for pystac.tests.extensions.scientific."""

import unittest
from datetime import datetime, timedelta

import pytest

import pystac
from pystac import ExtensionTypeError, Item
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


class ItemScientificExtensionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.item = make_item()
        self.example_item_uri = TestCases.get_path("data-files/scientific/item.json")

    @pytest.mark.vcr()
    def test_doi(self) -> None:
        ScientificExtension.ext(self.item).apply(DOI)
        assert DOI == ScientificExtension.ext(self.item).doi
        assert scientific.DOI_PROP in self.item.properties
        link = self.item.get_links(ScientificRelType.CITE_AS)[0]
        assert DOI_URL == link.get_href()
        self.item.validate()

        # Check that setting the doi does not cause extra links.

        # Same doi.
        ScientificExtension.ext(self.item).doi = DOI
        assert 1 == len(self.item.get_links(ScientificRelType.CITE_AS))
        self.item.validate()

        # Different doi.
        ScientificExtension.ext(self.item).doi = PUB1_DOI
        assert 1 == len(self.item.get_links(ScientificRelType.CITE_AS))
        link = self.item.get_links(ScientificRelType.CITE_AS)[0]
        assert PUB1_DOI_URL == link.get_href()
        self.item.validate()

    @pytest.mark.vcr()
    def test_citation(self) -> None:
        ScientificExtension.ext(self.item).apply(citation=CITATION)
        assert CITATION == ScientificExtension.ext(self.item).citation
        assert scientific.CITATION_PROP in self.item.properties
        assert not self.item.get_links(ScientificRelType.CITE_AS)
        self.item.validate()

    @pytest.mark.vcr()
    def test_publications_one(self) -> None:
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.item).apply(publications=publications)
        assert [1] == [int("1")]
        assert publications == ScientificExtension.ext(self.item).publications
        assert scientific.PUBLICATIONS_PROP in self.item.properties

        links = self.item.get_links(ScientificRelType.CITE_AS)
        doi_urls = [link.get_href() for link in links]
        expected = [PUB1_DOI_URL]
        self.assertCountEqual(expected, doi_urls)
        self.item.validate()

    @pytest.mark.vcr()
    def test_publications(self) -> None:
        ScientificExtension.ext(self.item).apply(publications=PUBLICATIONS)
        assert PUBLICATIONS == ScientificExtension.ext(self.item).publications
        assert scientific.PUBLICATIONS_PROP in self.item.properties

        links = self.item.get_links(ScientificRelType.CITE_AS)
        doi_urls = [link.get_href() for link in links]
        expected = [PUB1_DOI_URL, PUB2_DOI_URL]
        self.assertCountEqual(expected, doi_urls)
        self.item.validate()

    @pytest.mark.vcr()
    def test_remove_publication_one(self) -> None:
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.item).apply(DOI, publications=publications)
        ScientificExtension.ext(self.item).remove_publication(publications[0])
        assert not ScientificExtension.ext(self.item).publications
        links = self.item.get_links(ScientificRelType.CITE_AS)
        assert 1 == len(links)
        assert DOI_URL == links[0].target
        self.item.validate()

    @pytest.mark.vcr()
    def test_remove_all_publications_one(self) -> None:
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.item).apply(DOI, publications=publications)
        ScientificExtension.ext(self.item).remove_publication()
        assert not ScientificExtension.ext(self.item).publications
        links = self.item.get_links(ScientificRelType.CITE_AS)
        assert 1 == len(links)
        assert DOI_URL == links[0].target
        self.item.validate()

    @pytest.mark.vcr()
    def test_remove_publication_forward(self) -> None:
        ScientificExtension.ext(self.item).apply(DOI, publications=PUBLICATIONS)

        ScientificExtension.ext(self.item).remove_publication(PUBLICATIONS[0])
        assert  [PUBLICATIONS[1]] == ScientificExtension.ext(self.item).publications
        links = self.item.get_links(ScientificRelType.CITE_AS)
        assert 2 == len(links)
        assert DOI_URL == links[0].target
        assert PUB2_DOI_URL == links[1].target
        self.item.validate()

        ScientificExtension.ext(self.item).remove_publication(PUBLICATIONS[1])
        assert not ScientificExtension.ext(self.item).publications
        links = self.item.get_links(ScientificRelType.CITE_AS)
        assert 1 == len(links)
        assert DOI_URL == links[0].target
        self.item.validate()

    @pytest.mark.vcr()
    def test_remove_publication_reverse(self) -> None:
        ScientificExtension.ext(self.item).apply(DOI, publications=PUBLICATIONS)

        ScientificExtension.ext(self.item).remove_publication(PUBLICATIONS[1])
        assert  [PUBLICATIONS[0]] == ScientificExtension.ext(self.item).publications
        links = self.item.get_links(ScientificRelType.CITE_AS)
        assert 2 == len(links)
        assert PUB1_DOI_URL == links[1].target

        self.item.validate()
        ScientificExtension.ext(self.item).remove_publication(PUBLICATIONS[0])
        links = self.item.get_links(ScientificRelType.CITE_AS)
        assert 1 == len(links)
        assert DOI_URL == links[0].target
        self.item.validate()

    @pytest.mark.vcr()
    def test_remove_all_publications_with_some(self) -> None:
        ScientificExtension.ext(self.item).apply(DOI, publications=PUBLICATIONS)
        ScientificExtension.ext(self.item).remove_publication()
        assert not ScientificExtension.ext(self.item).publications
        links = self.item.get_links(ScientificRelType.CITE_AS)
        assert 1 == len(links)
        assert DOI_URL == links[0].target
        self.item.validate()

    @pytest.mark.vcr()
    def test_remove_all_publications_with_none(self) -> None:
        ScientificExtension.ext(self.item).apply(DOI)
        ScientificExtension.ext(self.item).remove_publication()
        assert not ScientificExtension.ext(self.item).publications
        links = self.item.get_links(ScientificRelType.CITE_AS)
        assert 1 == len(links)
        assert DOI_URL == links[0].target
        self.item.validate()

    def test_extension_not_implemented(self) -> None:
        # Should raise exception if Item does not include extension URI
        item = pystac.Item.from_file(self.example_item_uri)
        item.stac_extensions.remove(ScientificExtension.get_schema_uri())

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = ScientificExtension.ext(item)

    def test_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.example_item_uri)
        item.stac_extensions.remove(ScientificExtension.get_schema_uri())
        assert ScientificExtension.get_schema_uri() not in item.stac_extensions

        _ = ScientificExtension.ext(item, add_if_missing=True)

        assert ScientificExtension.get_schema_uri() in item.stac_extensions


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


class CollectionScientificExtensionTest(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.collection = make_collection()
        self.example_collection_uri = TestCases.get_path(
            "data-files/scientific/collection.json"
        )

    def test_stac_extensions(self) -> None:
        assert ScientificExtension.has_extension(self.collection)

    @pytest.mark.vcr()
    def test_doi(self) -> None:
        ScientificExtension.ext(self.collection).apply(DOI)
        assert DOI == ScientificExtension.ext(self.collection).doi
        assert scientific.DOI_PROP in self.collection.extra_fields
        link = self.collection.get_links(ScientificRelType.CITE_AS)[0]
        assert DOI_URL == link.get_href()
        self.collection.validate()

        # Check that setting the doi does not cause extra links.

        # Same doi.
        ScientificExtension.ext(self.collection).doi = DOI
        assert 1 == len(self.collection.get_links(ScientificRelType.CITE_AS))
        self.collection.validate()

        # Different doi.
        ScientificExtension.ext(self.collection).doi = PUB1_DOI
        assert 1 == len(self.collection.get_links(ScientificRelType.CITE_AS))
        link = self.collection.get_links(ScientificRelType.CITE_AS)[0]
        assert PUB1_DOI_URL == link.get_href()
        self.collection.validate()

    @pytest.mark.vcr()
    def test_citation(self) -> None:
        ScientificExtension.ext(self.collection).apply(citation=CITATION)
        assert CITATION == ScientificExtension.ext(self.collection).citation
        assert scientific.CITATION_PROP in self.collection.extra_fields
        assert not self.collection.get_links(ScientificRelType.CITE_AS)
        self.collection.validate()

    @pytest.mark.vcr()
    def test_publications_one(self) -> None:
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.collection).apply(publications=publications)
        assert  publications == ScientificExtension.ext(self.collection).publications
        assert scientific.PUBLICATIONS_PROP in self.collection.extra_fields

        links = self.collection.get_links(ScientificRelType.CITE_AS)
        doi_urls = [link.get_href() for link in links]
        expected = [PUB1_DOI_URL]
        self.assertCountEqual(expected, doi_urls)

        self.collection.validate()

    @pytest.mark.vcr()
    def test_publications(self) -> None:
        ScientificExtension.ext(self.collection).apply(publications=PUBLICATIONS)
        assert  PUBLICATIONS == ScientificExtension.ext(self.collection).publications
        assert scientific.PUBLICATIONS_PROP in self.collection.extra_fields

        links = self.collection.get_links(ScientificRelType.CITE_AS)
        doi_urls = [link.get_href() for link in links]
        expected = [PUB1_DOI_URL, PUB2_DOI_URL]
        self.assertCountEqual(expected, doi_urls)

        self.collection.validate()

    @pytest.mark.vcr()
    def test_remove_publication_one(self) -> None:
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.collection).apply(DOI, publications=publications)
        ScientificExtension.ext(self.collection).remove_publication(publications[0])
        assert not ScientificExtension.ext(self.collection).publications
        links = self.collection.get_links(ScientificRelType.CITE_AS)
        assert 1 == len(links)
        assert DOI_URL == links[0].target
        self.collection.validate()

    @pytest.mark.vcr()
    def test_remove_all_publications_one(self) -> None:
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.collection).apply(DOI, publications=publications)
        ScientificExtension.ext(self.collection).remove_publication()
        assert not ScientificExtension.ext(self.collection).publications
        links = self.collection.get_links(ScientificRelType.CITE_AS)
        assert 1 == len(links)
        assert DOI_URL == links[0].target
        self.collection.validate()

    @pytest.mark.vcr()
    def test_remove_publication_forward(self) -> None:
        ScientificExtension.ext(self.collection).apply(DOI, publications=PUBLICATIONS)

        ScientificExtension.ext(self.collection).remove_publication(PUBLICATIONS[0])
        assert  [PUBLICATIONS[1]] == ScientificExtension.ext(self.collection).publications 
        links = self.collection.get_links(ScientificRelType.CITE_AS)
        assert 2 == len(links)
        assert DOI_URL == links[0].target
        assert PUB2_DOI_URL == links[1].target
        self.collection.validate()

        ScientificExtension.ext(self.collection).remove_publication(PUBLICATIONS[1])
        assert not ScientificExtension.ext(self.collection).publications
        links = self.collection.get_links(ScientificRelType.CITE_AS)
        assert 1 == len(links)
        assert DOI_URL == links[0].target
        self.collection.validate()

    @pytest.mark.vcr()
    def test_remove_publication_reverse(self) -> None:
        ScientificExtension.ext(self.collection).apply(DOI, publications=PUBLICATIONS)

        ScientificExtension.ext(self.collection).remove_publication(PUBLICATIONS[1])
        assert  [PUBLICATIONS[0]] == ScientificExtension.ext(self.collection).publications 
        links = self.collection.get_links(ScientificRelType.CITE_AS)
        assert 2 == len(links)
        assert PUB1_DOI_URL == links[1].target

        self.collection.validate()
        ScientificExtension.ext(self.collection).remove_publication(PUBLICATIONS[0])
        links = self.collection.get_links(ScientificRelType.CITE_AS)
        assert 1 == len(links)
        assert DOI_URL == links[0].target
        self.collection.validate()

    @pytest.mark.vcr()
    def test_remove_all_publications_with_some(self) -> None:
        ScientificExtension.ext(self.collection).apply(DOI, publications=PUBLICATIONS)
        ScientificExtension.ext(self.collection).remove_publication()
        assert not ScientificExtension.ext(self.collection).publications
        links = self.collection.get_links(ScientificRelType.CITE_AS)
        assert 1 == len(links)
        assert DOI_URL == links[0].target
        self.collection.validate()

    @pytest.mark.vcr()
    def test_remove_all_publications_with_none(self) -> None:
        ScientificExtension.ext(self.collection).apply(DOI)
        ScientificExtension.ext(self.collection).remove_publication()
        assert not ScientificExtension.ext(self.collection).publications
        links = self.collection.get_links(ScientificRelType.CITE_AS)
        assert 1 == len(links)
        assert DOI_URL == links[0].target
        self.collection.validate()

    def test_extension_not_implemented(self) -> None:
        # Should raise exception if Collection does not include extension URI
        collection = pystac.Collection.from_file(self.example_collection_uri)
        collection.stac_extensions.remove(ScientificExtension.get_schema_uri())

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = ScientificExtension.ext(collection)

    def test_ext_add_to(self) -> None:
        collection = pystac.Collection.from_file(self.example_collection_uri)
        collection.stac_extensions.remove(ScientificExtension.get_schema_uri())
        assert  ScientificExtension.get_schema_uri() not in collection.stac_extensions 

        _ = ScientificExtension.ext(collection, add_if_missing=True)

        assert ScientificExtension.get_schema_uri() in collection.stac_extensions

    def test_should_raise_exception_when_passing_invalid_extension_object(
        self,
    ) -> None:
        with pytest.raises(
            ExtensionTypeError,
            match=r"^ScientificExtension does not apply to type 'object'$"
        ):
            # calling it wrong on purpose so -----------v
            ScientificExtension.ext(object()) # type: ignore


class SummariesScientificTest(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
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


@pytest.fixture
def ext_item() -> pystac.Item:
    path = TestCases.get_path("data-files/scientific/item.json")
    return pystac.Item.from_file(path)


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
