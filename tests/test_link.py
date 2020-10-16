from datetime import datetime
import unittest

import pystac
from tests.utils import (RANDOM_BBOX, RANDOM_GEOM)


class LinkTest(unittest.TestCase):
    def test_link_doest_fail_if_href_is_none(self):
        """Tests to cover a bug that was uncovered where a non-None HREF
        was supposed"""
        catalog = pystac.Catalog(id='test', description='test')
        item = pystac.Item(id='test-item',
                           geometry=RANDOM_GEOM,
                           bbox=RANDOM_BBOX,
                           datetime=datetime.utcnow(),
                           properties={'key': 'one'})
        catalog.add_item(item)
        catalog.set_self_href('/some/href')
        catalog.make_all_links_relative()

        for link in catalog.links:
            if link.rel == 'item':
                self.assertIsNone(link.get_href())
