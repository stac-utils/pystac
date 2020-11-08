"""Tests for pystac.tests.extensions.scientific."""

import datetime
import unittest

import pystac
from pystac.extensions import scientific

URL_TEMPLATE = 'http://example.com/catalog/%s.json'

DOI_BASE_URL = 'https://doi.org/'

DOI = '10.5061/dryad.s2v81.2'
DOI_URL = DOI_BASE_URL + DOI
CITATION = 'Some citation string'

PUB1_DOI = '10.1234/first'
PUB1_DOI_URL = DOI_BASE_URL + PUB1_DOI

PUB2_DOI = '10.2345/second'
PUB2_DOI_URL = DOI_BASE_URL + PUB2_DOI

PUBLICATIONS = [
    scientific.Publication(PUB1_DOI, 'First citation.'),
    scientific.Publication(PUB2_DOI, 'Second citation.')
]


def make_item() -> pystac.Item:
    asset_id = 'USGS/GAP/CONUS/2011'
    start = datetime.datetime(2011, 1, 2)
    item = pystac.Item(id=asset_id, geometry=None, bbox=None, datetime=start, properties={})
    item.set_self_href(URL_TEMPLATE % 2011)

    item.ext.enable(pystac.Extensions.SCIENTIFIC)
    return item


class ScientificItemExtTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.item = make_item()
        self.item.ext.enable(pystac.Extensions.SCIENTIFIC)

    def test_stac_extensions(self):
        self.assertEqual([pystac.Extensions.SCIENTIFIC], self.item.stac_extensions)

    def test_doi(self):
        self.item.ext.scientific.apply(DOI)
        self.assertEqual(DOI, self.item.ext.scientific.doi)
        self.assertIn(scientific.DOI, self.item.properties)
        link = self.item.get_links(scientific.CITE_AS)[0]
        self.assertEqual(DOI_URL, link.get_href())
        self.item.validate()

        # Check that setting the doi does not cause extra links.

        # Same doi.
        self.item.ext.scientific.doi = DOI
        self.assertEqual(1, len(self.item.get_links(scientific.CITE_AS)))
        self.item.validate()

        # Different doi.
        self.item.ext.scientific.doi = PUB1_DOI
        self.assertEqual(1, len(self.item.get_links(scientific.CITE_AS)))
        link = self.item.get_links(scientific.CITE_AS)[0]
        self.assertEqual(PUB1_DOI_URL, link.get_href())
        self.item.validate()

    def test_citation(self):
        self.item.ext.scientific.apply(citation=CITATION)
        self.assertEqual(CITATION, self.item.ext.scientific.citation)
        self.assertIn(scientific.CITATION, self.item.properties)
        self.assertFalse(self.item.get_links(scientific.CITE_AS))
        self.item.validate()

    def test_publications_one(self):
        publications = PUBLICATIONS[:1]
        self.item.ext.scientific.apply(publications=publications)
        self.assertEqual([1], [int('1')])
        self.assertEqual(publications, self.item.ext.scientific.publications)
        self.assertIn(scientific.PUBLICATIONS, self.item.properties)

        links = self.item.get_links(scientific.CITE_AS)
        doi_urls = [link.get_href() for link in links]
        expected = [PUB1_DOI_URL]
        self.assertCountEqual(expected, doi_urls)
        self.item.validate()

    def test_publications(self):
        self.item.ext.scientific.apply(publications=PUBLICATIONS)
        self.assertEqual(PUBLICATIONS, self.item.ext.scientific.publications)
        self.assertIn(scientific.PUBLICATIONS, self.item.properties)

        links = self.item.get_links(scientific.CITE_AS)
        doi_urls = [link.get_href() for link in links]
        expected = [PUB1_DOI_URL, PUB2_DOI_URL]
        self.assertCountEqual(expected, doi_urls)
        self.item.validate()

    def test_remove_publication_one(self):
        publications = PUBLICATIONS[:1]
        self.item.ext.scientific.apply(DOI, publications=publications)
        self.item.ext.scientific.remove_publication(publications[0])
        self.assertFalse(self.item.ext.scientific.publications)
        links = self.item.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()

    def test_remove_all_publications_one(self):
        publications = PUBLICATIONS[:1]
        self.item.ext.scientific.apply(DOI, publications=publications)
        self.item.ext.scientific.remove_publication()
        self.assertFalse(self.item.ext.scientific.publications)
        links = self.item.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()

    def test_remove_publication_forward(self):
        self.item.ext.scientific.apply(DOI, publications=PUBLICATIONS)

        self.item.ext.scientific.remove_publication(PUBLICATIONS[0])
        self.assertEqual([PUBLICATIONS[1]], self.item.ext.scientific.publications)
        links = self.item.get_links(scientific.CITE_AS)
        self.assertEqual(2, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.assertEqual(PUB2_DOI_URL, links[1].target)
        self.item.validate()

        self.item.ext.scientific.remove_publication(PUBLICATIONS[1])
        self.assertFalse(self.item.ext.scientific.publications)
        links = self.item.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()

    def test_remove_publication_reverse(self):
        self.item.ext.scientific.apply(DOI, publications=PUBLICATIONS)

        self.item.ext.scientific.remove_publication(PUBLICATIONS[1])
        self.assertEqual([PUBLICATIONS[0]], self.item.ext.scientific.publications)
        links = self.item.get_links(scientific.CITE_AS)
        self.assertEqual(2, len(links))
        self.assertEqual(PUB1_DOI_URL, links[1].target)

        self.item.validate()
        self.item.ext.scientific.remove_publication(PUBLICATIONS[0])
        links = self.item.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()

    def test_remove_all_publications_with_some(self):
        self.item.ext.scientific.apply(DOI, publications=PUBLICATIONS)
        self.item.ext.scientific.remove_publication()
        self.assertFalse(self.item.ext.scientific.publications)
        links = self.item.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()

    def test_remove_all_publications_with_none(self):
        self.item.ext.scientific.apply(DOI)
        self.item.ext.scientific.remove_publication()
        self.assertFalse(self.item.ext.scientific.publications)
        links = self.item.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.item.validate()


def make_collection() -> pystac.Collection:
    asset_id = 'my/thing'
    start = datetime.datetime(2018, 8, 24)
    end = start + datetime.timedelta(5, 4, 3, 2, 1)
    bboxes = [[-180, -90, 180, 90]]
    spatial_extent = pystac.SpatialExtent(bboxes)
    temporal_extent = pystac.TemporalExtent([[start, end]])
    extent = pystac.Extent(spatial_extent, temporal_extent)
    collection = pystac.Collection(asset_id, 'desc', extent)
    collection.set_self_href(URL_TEMPLATE % 2019)

    collection.ext.enable(pystac.Extensions.SCIENTIFIC)
    return collection


class ScientificCollectionExtTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.collection = make_collection()
        self.collection.ext.enable(pystac.Extensions.SCIENTIFIC)

    def test_stac_extensions(self):
        self.assertEqual([pystac.Extensions.SCIENTIFIC], self.collection.stac_extensions)

    def test_doi(self):
        self.collection.ext.scientific.apply(DOI)
        self.assertEqual(DOI, self.collection.ext.scientific.doi)
        self.assertIn(scientific.DOI, self.collection.extra_fields)
        link = self.collection.get_links(scientific.CITE_AS)[0]
        self.assertEqual(DOI_URL, link.get_href())
        self.collection.validate()

        # Check that setting the doi does not cause extra links.

        # Same doi.
        self.collection.ext.scientific.doi = DOI
        self.assertEqual(1, len(self.collection.get_links(scientific.CITE_AS)))
        self.collection.validate()

        # Different doi.
        self.collection.ext.scientific.doi = PUB1_DOI
        self.assertEqual(1, len(self.collection.get_links(scientific.CITE_AS)))
        link = self.collection.get_links(scientific.CITE_AS)[0]
        self.assertEqual(PUB1_DOI_URL, link.get_href())
        self.collection.validate()

    def test_citation(self):
        self.collection.ext.scientific.apply(citation=CITATION)
        self.assertEqual(CITATION, self.collection.ext.scientific.citation)
        self.assertIn(scientific.CITATION, self.collection.extra_fields)
        self.assertFalse(self.collection.get_links(scientific.CITE_AS))
        self.collection.validate()

    def test_publications_one(self):
        publications = PUBLICATIONS[:1]
        self.collection.ext.scientific.apply(publications=publications)
        self.assertEqual(publications, self.collection.ext.scientific.publications)
        self.assertIn(scientific.PUBLICATIONS, self.collection.extra_fields)

        links = self.collection.get_links(scientific.CITE_AS)
        doi_urls = [link.get_href() for link in links]
        expected = [PUB1_DOI_URL]
        self.assertCountEqual(expected, doi_urls)

        self.collection.validate()

    def test_publications(self):
        self.collection.ext.scientific.apply(publications=PUBLICATIONS)
        self.assertEqual(PUBLICATIONS, self.collection.ext.scientific.publications)
        self.assertIn(scientific.PUBLICATIONS, self.collection.extra_fields)

        links = self.collection.get_links(scientific.CITE_AS)
        doi_urls = [link.get_href() for link in links]
        expected = [PUB1_DOI_URL, PUB2_DOI_URL]
        self.assertCountEqual(expected, doi_urls)

        self.collection.validate()

    def test_remove_publication_one(self):
        publications = PUBLICATIONS[:1]
        self.collection.ext.scientific.apply(DOI, publications=publications)
        self.collection.ext.scientific.remove_publication(publications[0])
        self.assertFalse(self.collection.ext.scientific.publications)
        links = self.collection.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()

    def test_remove_all_publications_one(self):
        publications = PUBLICATIONS[:1]
        self.collection.ext.scientific.apply(DOI, publications=publications)
        self.collection.ext.scientific.remove_publication()
        self.assertFalse(self.collection.ext.scientific.publications)
        links = self.collection.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()

    def test_remove_publication_forward(self):
        self.collection.ext.scientific.apply(DOI, publications=PUBLICATIONS)

        self.collection.ext.scientific.remove_publication(PUBLICATIONS[0])
        self.assertEqual([PUBLICATIONS[1]], self.collection.ext.scientific.publications)
        links = self.collection.get_links(scientific.CITE_AS)
        self.assertEqual(2, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.assertEqual(PUB2_DOI_URL, links[1].target)
        self.collection.validate()

        self.collection.ext.scientific.remove_publication(PUBLICATIONS[1])
        self.assertFalse(self.collection.ext.scientific.publications)
        links = self.collection.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()

    def test_remove_publication_reverse(self):
        self.collection.ext.scientific.apply(DOI, publications=PUBLICATIONS)

        self.collection.ext.scientific.remove_publication(PUBLICATIONS[1])
        self.assertEqual([PUBLICATIONS[0]], self.collection.ext.scientific.publications)
        links = self.collection.get_links(scientific.CITE_AS)
        self.assertEqual(2, len(links))
        self.assertEqual(PUB1_DOI_URL, links[1].target)

        self.collection.validate()
        self.collection.ext.scientific.remove_publication(PUBLICATIONS[0])
        links = self.collection.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()

    def test_remove_all_publications_with_some(self):
        self.collection.ext.scientific.apply(DOI, publications=PUBLICATIONS)
        self.collection.ext.scientific.remove_publication()
        self.assertFalse(self.collection.ext.scientific.publications)
        links = self.collection.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()

    def test_remove_all_publications_with_none(self):
        self.collection.ext.scientific.apply(DOI)
        self.collection.ext.scientific.remove_publication()
        self.assertFalse(self.collection.ext.scientific.publications)
        links = self.collection.get_links(scientific.CITE_AS)
        self.assertEqual(1, len(links))
        self.assertEqual(DOI_URL, links[0].target)
        self.collection.validate()


if __name__ == '__main__':
    unittest.main()
