from datetime import datetime
import unittest

import pystac
from tests.utils import (RANDOM_BBOX, RANDOM_GEOM)

TEST_DATETIME = datetime(2020, 3, 14, 16, 32)


class LinkTest(unittest.TestCase):
    def test_link_does_not_fail_if_href_is_none(self):
        """Test to ensure get_href does not fail when the href is None"""
        catalog = pystac.Catalog(id='test', description='test desc')
        item = pystac.Item(id='test-item',
                           geometry=RANDOM_GEOM,
                           bbox=RANDOM_BBOX,
                           datetime=datetime.utcnow(),
                           properties={})
        catalog.add_item(item)
        catalog.set_self_href('/some/href')
        catalog.make_all_links_relative()

        link = catalog.get_single_link('item')
        self.assertIsNone(link.get_href())
