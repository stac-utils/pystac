"""Tests for pystac.tests.extensions.scientific."""

import datetime
import unittest

import pystac
from pystac.extensions import scientific
from pystac.extensions.scientific import ScientificExtension

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


class ItemScientificExtensionTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.item = make_item()

    def test_stac_extensions(self):
        self.assertTrue(ScientificExtension.has_extension(self.item))

    def test_doi(self):
        ScientificExtension.ext(self.item).apply(DOI)
        self.assertEqual(DOI, ScientificExtension.ext(self.item).doi)
        self.assertIn(scientific.DOI, self.item.properties)
        link = self.item.get_links(scientific.CITE_AS)[0]
        self.assertEqual(DOI_URL, link.get_href())
        self.item.validate()

        # Check that setting the doi does not cause extra links.

        # Same doi.
        ScientificExtension.ext(self.item).doi = DOI
        self.assertEqual(1, len(self.item.get_links(scientific.CITE_AS)))
        self.item.validate()

        # Different doi.
        ScientificExtension.ext(self.item).doi = PUB1_DOI
        self.assertEqual(1, len(self.item.get_links(scientific.CITE_AS)))
        link = self.item.get_links(scientific.CITE_AS)[0]
        self.assertEqual(PUB1_DOI_URL, link.get_href())
        self.item.validate()

    def test_citation(self):
        ScientificExtension.ext(self.item).apply(citation=CITATION)
        self.assertEqual(CITATION, ScientificExtension.ext(self.item).citation)
        self.assertIn(scientific.CITATION, self.item.properties)
        self.assertFalse(self.item.get_links(scientific.CITE_AS))
        self.item.validate()

    def test_publications_one(self):
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.item).apply(publications=publications)
        self.assertEqual([1], [int("1")])
        self.assertEqual(publications, ScientificExtension.ext(self.item).publications)
        self.assertIn(scientific.PUBLICATIONS, self.item.properties)

        links = self.item.get_links(scientific.CITE_AS)
        doi_urls = [link.get_href() for link in links]
        expected = [PUB1_DOI_URL]
        self.assertCountEqual(expected, doi_urls)
        self.item.validate()

    def test_publications(self):
        ScientificExtension.ext(self.item).apply(publications=PUBLICATIONS)
        self.assertEqual(PUBLICATIONS, ScientificExtension.ext(self.item).publications)
        self.assertIn(scientific.PUBLICATIONS, self.item.properties)

        links = self.item.get_links(scientific.CITE_AS)
        doi_urls = [link.get_href() for link in links]
        expected = [PUB1_DOI_URL, PUB2_DOI_URL]
        self.assertCountEqual(expected, doi_urls)
        self.item.validate()

    def test_remove_publication_one(self):
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.item).apply(DOI, publications=publications)
        ScientificExtension.ext(self.item).remove_publication(publications[0])
        self.assertFalse(ScientificExtension.ext(self.item).publications)
        links = self.item.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()

    def test_remove_all_publications_one(self):
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.item).apply(DOI, publications=publications)
        ScientificExtension.ext(self.item).remove_publication()
        self.assertFalse(ScientificExtension.ext(self.item).publications)
        links = self.item.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()

    def test_remove_publication_forward(self):
        ScientificExtension.ext(self.item).apply(DOI, publications=PUBLICATIONS)

        ScientificExtension.ext(self.item).remove_publication(PUBLICATIONS[0])
        self.assertEqual(
            [PUBLICATIONS[1]], ScientificExtension.ext(self.item).publications
        )
        links = self.item.get_links(scientific.CITE_AS)
        self.assertEqual(2, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.assertEqual(PUB2_DOI_URL, links[1].target)
        self.item.validate()

        ScientificExtension.ext(self.item).remove_publication(PUBLICATIONS[1])
        self.assertFalse(ScientificExtension.ext(self.item).publications)
        links = self.item.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()

    def test_remove_publication_reverse(self):
        ScientificExtension.ext(self.item).apply(DOI, publications=PUBLICATIONS)

        ScientificExtension.ext(self.item).remove_publication(PUBLICATIONS[1])
        self.assertEqual(
            [PUBLICATIONS[0]], ScientificExtension.ext(self.item).publications
        )
        links = self.item.get_links(scientific.CITE_AS)
        self.assertEqual(2, len(links))
        self.assertEqual(PUB1_DOI_URL, links[1].target)

        self.item.validate()
        ScientificExtension.ext(self.item).remove_publication(PUBLICATIONS[0])
        links = self.item.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()

    def test_remove_all_publications_with_some(self):
        ScientificExtension.ext(self.item).apply(DOI, publications=PUBLICATIONS)
        ScientificExtension.ext(self.item).remove_publication()
        self.assertFalse(ScientificExtension.ext(self.item).publications)
        links = self.item.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()

    def test_remove_all_publications_with_none(self):
        ScientificExtension.ext(self.item).apply(DOI)
        ScientificExtension.ext(self.item).remove_publication()
        self.assertFalse(ScientificExtension.ext(self.item).publications)
        links = self.item.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()


def make_collection() -> pystac.Collection:
    asset_id = "my/thing"
    start = datetime.datetime(2018, 8, 24)
    end = start + datetime.timedelta(5, 4, 3, 2, 1)
    bboxes = [[-180.0, -90.0, 180.0, 90.0]]
    spatial_extent = pystac.SpatialExtent(bboxes)
    temporal_extent = pystac.TemporalExtent([[start, end]])
    extent = pystac.Extent(spatial_extent, temporal_extent)
    collection = pystac.Collection(asset_id, "desc", extent)
    collection.set_self_href(URL_TEMPLATE % 2019)

    ScientificExtension.add_to(collection)
    return collection


class CollectionScientificExtensionTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.collection = make_collection()

    def test_stac_extensions(self):
        self.assertTrue(ScientificExtension.has_extension(self.collection))

    def test_doi(self):
        ScientificExtension.ext(self.collection).apply(DOI)
        self.assertEqual(DOI, ScientificExtension.ext(self.collection).doi)
        self.assertIn(scientific.DOI, self.collection.extra_fields)
        link = self.collection.get_links(scientific.CITE_AS)[0]
        self.assertEqual(DOI_URL, link.get_href())
        self.collection.validate()

        # Check that setting the doi does not cause extra links.

        # Same doi.
        ScientificExtension.ext(self.collection).doi = DOI
        self.assertEqual(1, len(self.collection.get_links(scientific.CITE_AS)))
        self.collection.validate()

        # Different doi.
        ScientificExtension.ext(self.collection).doi = PUB1_DOI
        self.assertEqual(1, len(self.collection.get_links(scientific.CITE_AS)))
        link = self.collection.get_links(scientific.CITE_AS)[0]
        self.assertEqual(PUB1_DOI_URL, link.get_href())
        self.collection.validate()

    def test_citation(self):
        ScientificExtension.ext(self.collection).apply(citation=CITATION)
        self.assertEqual(CITATION, ScientificExtension.ext(self.collection).citation)
        self.assertIn(scientific.CITATION, self.collection.extra_fields)
        self.assertFalse(self.collection.get_links(scientific.CITE_AS))
        self.collection.validate()

    def test_publications_one(self):
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.collection).apply(publications=publications)
        self.assertEqual(
            publications, ScientificExtension.ext(self.collection).publications
        )
        self.assertIn(scientific.PUBLICATIONS, self.collection.extra_fields)

        links = self.collection.get_links(scientific.CITE_AS)
        doi_urls = [link.get_href() for link in links]
        expected = [PUB1_DOI_URL]
        self.assertCountEqual(expected, doi_urls)

        self.collection.validate()

    def test_publications(self):
        ScientificExtension.ext(self.collection).apply(publications=PUBLICATIONS)
        self.assertEqual(
            PUBLICATIONS, ScientificExtension.ext(self.collection).publications
        )
        self.assertIn(scientific.PUBLICATIONS, self.collection.extra_fields)

        links = self.collection.get_links(scientific.CITE_AS)
        doi_urls = [link.get_href() for link in links]
        expected = [PUB1_DOI_URL, PUB2_DOI_URL]
        self.assertCountEqual(expected, doi_urls)

        self.collection.validate()

    def test_remove_publication_one(self):
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.collection).apply(DOI, publications=publications)
        ScientificExtension.ext(self.collection).remove_publication(publications[0])
        self.assertFalse(ScientificExtension.ext(self.collection).publications)
        links = self.collection.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()

    def test_remove_all_publications_one(self):
        publications = PUBLICATIONS[:1]
        ScientificExtension.ext(self.collection).apply(DOI, publications=publications)
        ScientificExtension.ext(self.collection).remove_publication()
        self.assertFalse(ScientificExtension.ext(self.collection).publications)
        links = self.collection.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()

    def test_remove_publication_forward(self):
        ScientificExtension.ext(self.collection).apply(DOI, publications=PUBLICATIONS)

        ScientificExtension.ext(self.collection).remove_publication(PUBLICATIONS[0])
        self.assertEqual(
            [PUBLICATIONS[1]], ScientificExtension.ext(self.collection).publications
        )
        links = self.collection.get_links(scientific.CITE_AS)
        self.assertEqual(2, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.assertEqual(PUB2_DOI_URL, links[1].target)
        self.collection.validate()

        ScientificExtension.ext(self.collection).remove_publication(PUBLICATIONS[1])
        self.assertFalse(ScientificExtension.ext(self.collection).publications)
        links = self.collection.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()

    def test_remove_publication_reverse(self):
        ScientificExtension.ext(self.collection).apply(DOI, publications=PUBLICATIONS)

        ScientificExtension.ext(self.collection).remove_publication(PUBLICATIONS[1])
        self.assertEqual(
            [PUBLICATIONS[0]], ScientificExtension.ext(self.collection).publications
        )
        links = self.collection.get_links(scientific.CITE_AS)
        self.assertEqual(2, len(links))
        self.assertEqual(PUB1_DOI_URL, links[1].target)

        self.collection.validate()
        ScientificExtension.ext(self.collection).remove_publication(PUBLICATIONS[0])
        links = self.collection.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()

    def test_remove_all_publications_with_some(self):
        ScientificExtension.ext(self.collection).apply(DOI, publications=PUBLICATIONS)
        ScientificExtension.ext(self.collection).remove_publication()
        self.assertFalse(ScientificExtension.ext(self.collection).publications)
        links = self.collection.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()

    def test_remove_all_publications_with_none(self):
        ScientificExtension.ext(self.collection).apply(DOI)
        ScientificExtension.ext(self.collection).remove_publication()
        self.assertFalse(ScientificExtension.ext(self.collection).publications)
        links = self.collection.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()


if __name__ == "__main__":
    unittest.main()
