"""Tests for pystac.tests.extensions.scientific."""

import datetime

from pystac import ExtensionTypeError
from pystac.link import Link
from pystac.collection import Summaries
import unittest
from typing import List, Optional

import pystac
from pystac.extensions import scientific
from pystac.extensions.scientific import (
    Publication,
    ScientificExtension,
    ScientificRelType,
    remove_link,
)
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


def make_item() -> pystac.Item:
    asset_id = "USGS/GAP/CONUS/2011"
    start = datetime.datetime(2011, 1, 2)
    item = pystac.Item(
        id=asset_id, geometry=None, bbox=None, datetime=start, properties={}
    )
    item.set_self_href(URL_TEMPLATE % 2011)

    ScientificExtension.add_to(item)
    return item


class TestRemoveLinks(unittest.TestCase):
    def test_remove_none_doi(self) -> None:
        """Calling remove_link with doi = None should have no effect."""
        link = Link(
            rel=ScientificRelType.CITE_AS,
            target="https://some-domain.com/some/paper.pdf",
        )
        links = [link]

        remove_link(links, doi=None)

        self.assertEqual(len(links), 1)
        self.assertIn(link, links)


class TestPublication(unittest.TestCase):
    def test_get_link_returns_none_if_no_doi(self) -> None:
        pub = Publication(None, CITATION)

        self.assertIsNone(pub.get_link())


class ItemScientificExtensionTest(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.item = make_item()
        self.example_item_uri = TestCases.get_path("data-files/scientific/item.json")

    def test_stac_extensions(self) -> None:
        self.assertTrue(ScientificExtension.has_extension(self.item))

    def test_doi(self) -> None:
        ScientificExtension.ext(self.item).apply(DOI)
        self.assertEqual(DOI, ScientificExtension.ext(self.item).doi)
        self.assertIn(scientific.DOI_PROP, self.item.properties)
        link = self.item.get_links(ScientificRelType.CITE_AS)[0]
        self.assertEqual(DOI_URL, link.get_href())
        self.item.validate()

        # Check that setting the doi does not cause extra links.

        # Same doi.
        ScientificExtension.ext(self.item).doi = DOI
        self.assertEqual(1, len(self.item.get_links(ScientificRelType.CITE_AS)))
        self.item.validate()

        # Different doi.
        ScientificExtension.ext(self.item).doi = PUB1_DOI
        self.assertEqual(1, len(self.item.get_links(ScientificRelType.CITE_AS)))
        link = self.item.get_links(ScientificRelType.CITE_AS)[0]
        self.assertEqual(PUB1_DOI_URL, link.get_href())
        self.item.validate()

    def test_citation(self) -> None:
        ScientificExtension.ext(self.item).apply(citation=CITATION)
        self.assertEqual(CITATION, ScientificExtension.ext(self.item).citation)
        self.assertIn(scientific.CITATION_PROP, self.item.properties)
        self.assertFalse(self.item.get_links(ScientificRelType.CITE_AS))
        self.item.validate()

    def test_publications_one(self) -> None:
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.item).apply(publications=publications)
        self.assertEqual([1], [int("1")])
        self.assertEqual(publications, ScientificExtension.ext(self.item).publications)
        self.assertIn(scientific.PUBLICATIONS_PROP, self.item.properties)

        links = self.item.get_links(ScientificRelType.CITE_AS)
        doi_urls = [link.get_href() for link in links]
        expected = [PUB1_DOI_URL]
        self.assertCountEqual(expected, doi_urls)
        self.item.validate()

    def test_publications(self) -> None:
        ScientificExtension.ext(self.item).apply(publications=PUBLICATIONS)
        self.assertEqual(PUBLICATIONS, ScientificExtension.ext(self.item).publications)
        self.assertIn(scientific.PUBLICATIONS_PROP, self.item.properties)

        links = self.item.get_links(ScientificRelType.CITE_AS)
        doi_urls = [link.get_href() for link in links]
        expected = [PUB1_DOI_URL, PUB2_DOI_URL]
        self.assertCountEqual(expected, doi_urls)
        self.item.validate()

    def test_remove_publication_one(self) -> None:
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.item).apply(DOI, publications=publications)
        ScientificExtension.ext(self.item).remove_publication(publications[0])
        self.assertFalse(ScientificExtension.ext(self.item).publications)
        links = self.item.get_links(ScientificRelType.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()

    def test_remove_all_publications_one(self) -> None:
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.item).apply(DOI, publications=publications)
        ScientificExtension.ext(self.item).remove_publication()
        self.assertFalse(ScientificExtension.ext(self.item).publications)
        links = self.item.get_links(ScientificRelType.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()

    def test_remove_publication_forward(self) -> None:
        ScientificExtension.ext(self.item).apply(DOI, publications=PUBLICATIONS)

        ScientificExtension.ext(self.item).remove_publication(PUBLICATIONS[0])
        self.assertEqual(
            [PUBLICATIONS[1]], ScientificExtension.ext(self.item).publications
        )
        links = self.item.get_links(ScientificRelType.CITE_AS)
        self.assertEqual(2, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.assertEqual(PUB2_DOI_URL, links[1].target)
        self.item.validate()

        ScientificExtension.ext(self.item).remove_publication(PUBLICATIONS[1])
        self.assertFalse(ScientificExtension.ext(self.item).publications)
        links = self.item.get_links(ScientificRelType.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()

    def test_remove_publication_reverse(self) -> None:
        ScientificExtension.ext(self.item).apply(DOI, publications=PUBLICATIONS)

        ScientificExtension.ext(self.item).remove_publication(PUBLICATIONS[1])
        self.assertEqual(
            [PUBLICATIONS[0]], ScientificExtension.ext(self.item).publications
        )
        links = self.item.get_links(ScientificRelType.CITE_AS)
        self.assertEqual(2, len(links))
        self.assertEqual(PUB1_DOI_URL, links[1].target)

        self.item.validate()
        ScientificExtension.ext(self.item).remove_publication(PUBLICATIONS[0])
        links = self.item.get_links(ScientificRelType.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()

    def test_remove_all_publications_with_some(self) -> None:
        ScientificExtension.ext(self.item).apply(DOI, publications=PUBLICATIONS)
        ScientificExtension.ext(self.item).remove_publication()
        self.assertFalse(ScientificExtension.ext(self.item).publications)
        links = self.item.get_links(ScientificRelType.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()

    def test_remove_all_publications_with_none(self) -> None:
        ScientificExtension.ext(self.item).apply(DOI)
        ScientificExtension.ext(self.item).remove_publication()
        self.assertFalse(ScientificExtension.ext(self.item).publications)
        links = self.item.get_links(ScientificRelType.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
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
        self.assertNotIn(ScientificExtension.get_schema_uri(), item.stac_extensions)

        _ = ScientificExtension.ext(item, add_if_missing=True)

        self.assertIn(ScientificExtension.get_schema_uri(), item.stac_extensions)


def make_collection() -> pystac.Collection:
    asset_id = "my/thing"
    start = datetime.datetime(2018, 8, 24)
    end = start + datetime.timedelta(5, 4, 3, 2, 1)
    bboxes = [[-180.0, -90.0, 180.0, 90.0]]
    spatial_extent = pystac.SpatialExtent(bboxes)
    intervals: List[List[Optional[datetime.datetime]]] = [[start, end]]
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
        self.assertTrue(ScientificExtension.has_extension(self.collection))

    def test_doi(self) -> None:
        ScientificExtension.ext(self.collection).apply(DOI)
        self.assertEqual(DOI, ScientificExtension.ext(self.collection).doi)
        self.assertIn(scientific.DOI_PROP, self.collection.extra_fields)
        link = self.collection.get_links(ScientificRelType.CITE_AS)[0]
        self.assertEqual(DOI_URL, link.get_href())
        self.collection.validate()

        # Check that setting the doi does not cause extra links.

        # Same doi.
        ScientificExtension.ext(self.collection).doi = DOI
        self.assertEqual(1, len(self.collection.get_links(ScientificRelType.CITE_AS)))
        self.collection.validate()

        # Different doi.
        ScientificExtension.ext(self.collection).doi = PUB1_DOI
        self.assertEqual(1, len(self.collection.get_links(ScientificRelType.CITE_AS)))
        link = self.collection.get_links(ScientificRelType.CITE_AS)[0]
        self.assertEqual(PUB1_DOI_URL, link.get_href())
        self.collection.validate()

    def test_citation(self) -> None:
        ScientificExtension.ext(self.collection).apply(citation=CITATION)
        self.assertEqual(CITATION, ScientificExtension.ext(self.collection).citation)
        self.assertIn(scientific.CITATION_PROP, self.collection.extra_fields)
        self.assertFalse(self.collection.get_links(ScientificRelType.CITE_AS))
        self.collection.validate()

    def test_publications_one(self) -> None:
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.collection).apply(publications=publications)
        self.assertEqual(
            publications, ScientificExtension.ext(self.collection).publications
        )
        self.assertIn(scientific.PUBLICATIONS_PROP, self.collection.extra_fields)

        links = self.collection.get_links(ScientificRelType.CITE_AS)
        doi_urls = [link.get_href() for link in links]
        expected = [PUB1_DOI_URL]
        self.assertCountEqual(expected, doi_urls)

        self.collection.validate()

    def test_publications(self) -> None:
        ScientificExtension.ext(self.collection).apply(publications=PUBLICATIONS)
        self.assertEqual(
            PUBLICATIONS, ScientificExtension.ext(self.collection).publications
        )
        self.assertIn(scientific.PUBLICATIONS_PROP, self.collection.extra_fields)

        links = self.collection.get_links(ScientificRelType.CITE_AS)
        doi_urls = [link.get_href() for link in links]
        expected = [PUB1_DOI_URL, PUB2_DOI_URL]
        self.assertCountEqual(expected, doi_urls)

        self.collection.validate()

    def test_remove_publication_one(self) -> None:
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.collection).apply(DOI, publications=publications)
        ScientificExtension.ext(self.collection).remove_publication(publications[0])
        self.assertFalse(ScientificExtension.ext(self.collection).publications)
        links = self.collection.get_links(ScientificRelType.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()

    def test_remove_all_publications_one(self) -> None:
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.collection).apply(DOI, publications=publications)
        ScientificExtension.ext(self.collection).remove_publication()
        self.assertFalse(ScientificExtension.ext(self.collection).publications)
        links = self.collection.get_links(ScientificRelType.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()

    def test_remove_publication_forward(self) -> None:
        ScientificExtension.ext(self.collection).apply(DOI, publications=PUBLICATIONS)

        ScientificExtension.ext(self.collection).remove_publication(PUBLICATIONS[0])
        self.assertEqual(
            [PUBLICATIONS[1]], ScientificExtension.ext(self.collection).publications
        )
        links = self.collection.get_links(ScientificRelType.CITE_AS)
        self.assertEqual(2, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.assertEqual(PUB2_DOI_URL, links[1].target)
        self.collection.validate()

        ScientificExtension.ext(self.collection).remove_publication(PUBLICATIONS[1])
        self.assertFalse(ScientificExtension.ext(self.collection).publications)
        links = self.collection.get_links(ScientificRelType.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()

    def test_remove_publication_reverse(self) -> None:
        ScientificExtension.ext(self.collection).apply(DOI, publications=PUBLICATIONS)

        ScientificExtension.ext(self.collection).remove_publication(PUBLICATIONS[1])
        self.assertEqual(
            [PUBLICATIONS[0]], ScientificExtension.ext(self.collection).publications
        )
        links = self.collection.get_links(ScientificRelType.CITE_AS)
        self.assertEqual(2, len(links))
        self.assertEqual(PUB1_DOI_URL, links[1].target)

        self.collection.validate()
        ScientificExtension.ext(self.collection).remove_publication(PUBLICATIONS[0])
        links = self.collection.get_links(ScientificRelType.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()

    def test_remove_all_publications_with_some(self) -> None:
        ScientificExtension.ext(self.collection).apply(DOI, publications=PUBLICATIONS)
        ScientificExtension.ext(self.collection).remove_publication()
        self.assertFalse(ScientificExtension.ext(self.collection).publications)
        links = self.collection.get_links(ScientificRelType.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()

    def test_remove_all_publications_with_none(self) -> None:
        ScientificExtension.ext(self.collection).apply(DOI)
        ScientificExtension.ext(self.collection).remove_publication()
        self.assertFalse(ScientificExtension.ext(self.collection).publications)
        links = self.collection.get_links(ScientificRelType.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
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
        self.assertNotIn(
            ScientificExtension.get_schema_uri(), collection.stac_extensions
        )

        _ = ScientificExtension.ext(collection, add_if_missing=True)

        self.assertIn(ScientificExtension.get_schema_uri(), collection.stac_extensions)

    def test_should_raise_exception_when_passing_invalid_extension_object(
        self,
    ) -> None:
        self.assertRaisesRegex(
            ExtensionTypeError,
            r"^Scientific extension does not apply to type 'object'$",
            ScientificExtension.ext,
            object(),
        )


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
        self.assertListEqual([CITATION], citations)

    def test_set_citation_summaries(self) -> None:
        collection = self.collection.clone()
        sci_summaries = ScientificExtension.summaries(collection)

        sci_summaries.citation = None
        self.assertIsNone(sci_summaries.citation)

    def test_get_doi_summaries(self) -> None:
        dois = ScientificExtension.summaries(self.collection).doi

        assert dois is not None
        self.assertListEqual([PUB1_DOI, PUB2_DOI], dois)

    def test_set_doi_summaries(self) -> None:
        collection = self.collection.clone()
        sci_summaries = ScientificExtension.summaries(collection)

        sci_summaries.doi = [PUB2_DOI]
        new_dois = ScientificExtension.summaries(self.collection).doi

        assert new_dois is not None
        self.assertListEqual([PUB2_DOI], new_dois)
