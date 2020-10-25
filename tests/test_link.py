import datetime
import unittest

import pystac

TEST_DATETIME = datetime.datetime(2020, 3, 14, 16, 32)


class LinkTest(unittest.TestCase):
    item: pystac.Item

    def setUp(self):
        self.item = pystac.Item(id='test-item',
                                geometry=None,
                                bbox=None,
                                datetime=TEST_DATETIME,
                                properties={})

    def test_minimal(self):
        rel = 'my rel'
        target = 'https://example.com/a/b'
        link = pystac.Link(rel, target)
        self.assertEqual(target, link.get_href())
        self.assertEqual(target, link.get_absolute_href())

        expected_repr = f'<Link rel={rel} target={target}>'
        self.assertEqual(expected_repr, link.__repr__())

        self.assertFalse(link.is_resolved())

        expected_dict = {'rel': rel, 'href': target}
        self.assertEqual(expected_dict, link.to_dict())

        # Run the same tests on the clone.
        clone = link.clone()
        # TODO(schwehr): Does link need an __eq__?
        self.assertNotEqual(link, clone)

        self.assertEqual(target, clone.get_href())
        self.assertEqual(target, clone.get_absolute_href())

        self.assertEqual(expected_repr, clone.__repr__())

        self.assertEqual(expected_dict, clone.to_dict())

        # Try the modification methods.
        self.assertIsNone(link.owner)
        link.set_owner(1)  # A junk value.
        self.assertEqual(1, link.owner)
        link.set_owner(None)
        self.assertIsNone(link.owner)

        self.assertEqual(pystac.LinkType.ABSOLUTE, link.link_type)

        link.make_absolute()
        self.assertEqual(pystac.LinkType.ABSOLUTE, link.link_type)
        self.assertEqual(target, link.get_href())
        self.assertEqual(target, link.get_absolute_href())

        link.make_relative()
        self.assertEqual(pystac.LinkType.RELATIVE, link.link_type)
        self.assertEqual(target, link.get_href())
        self.assertEqual(target, link.get_absolute_href())

        link.set_owner(self.item)
        self.assertEqual(self.item, link.owner)
        # TODO(schwehr): Cannot call link.get_href() after set_owner.

        # TODO(schwehr): Test link.resolve_stac_object()

    def test_relative(self):
        rel = 'my rel'
        target = '../elsewhere'
        mime_type = 'example/stac_thing'
        link = pystac.Link(rel,
                           target,
                           mime_type,
                           'a title',
                           properties={'a': 'b'},
                           link_type=pystac.LinkType.RELATIVE)
        expected_dict = {
            'rel': rel,
            'href': target,
            'type': 'example/stac_thing',
            'title': 'a title',
            'a': 'b'
        }
        self.assertEqual(expected_dict, link.to_dict())

        self.assertEqual(pystac.LinkType.RELATIVE, link.link_type)

    def test_link_does_not_fail_if_href_is_none(self):
        """Test to ensure get_href does not fail when the href is None."""
        catalog = pystac.Catalog(id='test', description='test desc')
        catalog.add_item(self.item)
        catalog.set_self_href('/some/href')
        catalog.make_all_links_relative()

        link = catalog.get_single_link('item')
        self.assertIsNone(link.get_href())
