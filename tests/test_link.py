import datetime
import unittest

import pystac

TEST_DATETIME: datetime.datetime = datetime.datetime(2020, 3, 14, 16, 32)


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

    def test_resolve_stac_object_no_root_and_target_is_item(self):
        link = pystac.Link('my rel', target=self.item)
        link.resolve_stac_object()


class StaticLinkTest(unittest.TestCase):
    def test_from_dict_round_trip(self):
        test_cases = [
            {
                'rel': '',
                'href': ''
            },  # Not valid, but works.
            {
                'rel': 'r',
                'href': 't'
            },
            {
                'rel': 'r',
                'href': '/t'
            },
            {
                'rel': 'r',
                'href': 't',
                'type': 'a/b',
                'title': 't',
                'c': 'd',
                1: 2
            },
            # Special case.
            {
                'rel': 'self',
                'href': 't'
            },
        ]
        for d in test_cases:
            d2 = pystac.Link.from_dict(d).to_dict()
            self.assertEqual(d, d2)

    def test_from_dict_link_type(self):
        test_cases = [
            ({
                'rel': '',
                'href': 'https://a'
            }, pystac.LinkType.ABSOLUTE),
            ({
                'rel': '',
                'href': '/a'
            }, pystac.LinkType.ABSOLUTE),
            ({
                'rel': '',
                'href': 'a'
            }, pystac.LinkType.RELATIVE),
            ({
                'rel': '',
                'href': './a'
            }, pystac.LinkType.RELATIVE),
            # 'self' is a special case.
            ({
                'rel': 'self',
                'href': 'does not matter'
            }, pystac.LinkType.ABSOLUTE),
        ]
        for case in test_cases:
            item = pystac.Link.from_dict(case[0])
            self.assertEqual(case[1], item.link_type)

    def test_from_dict_failures(self):
        for d in [{}, {'href': 't'}, {'rel': 'r'}]:
            with self.assertRaises(KeyError):
                pystac.Link.from_dict(d)

        for d in [
            {
                'rel': '',
                'href': 1
            },
            {
                'rel': '',
                'href': None
            },
        ]:
            with self.assertRaises(AttributeError):
                pystac.Link.from_dict(d)

    def test_collection(self):
        c = pystac.Collection('collection id', 'desc', extent=None)
        link = pystac.Link.collection(c)
        expected = {'rel': 'collection', 'href': None, 'type': 'application/json'}
        self.assertEqual(expected, link.to_dict())

    def test_child(self):
        c = pystac.Collection('collection id', 'desc', extent=None)
        link = pystac.Link.child(c)
        expected = {'rel': 'child', 'href': None, 'type': 'application/json'}
        self.assertEqual(expected, link.to_dict())
