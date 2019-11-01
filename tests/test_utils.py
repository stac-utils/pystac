import unittest

from pystac.utils import (make_relative_href, make_absolute_href,
                          is_absolute_href)


class UtilsTest(unittest.TestCase):
    def test_make_relative_href(self):
        # Test cases of (source_href, start_href, expected)
        test_cases = [
            ('/a/b/c/d/catalog.json', '/a/b/c/catalog.json',
             './d/catalog.json'),
            ('/a/b/catalog.json', '/a/b/c/catalog.json', '../catalog.json'),
            ('/a/catalog.json', '/a/b/c/catalog.json', '../../catalog.json'),
            ('http://stacspec.org/a/b/c/d/catalog.json',
             'http://stacspec.org/a/b/c/catalog.json', './d/catalog.json'),
            ('http://stacspec.org/a/b/catalog.json',
             'http://stacspec.org/a/b/c/catalog.json', '../catalog.json'),
            ('http://stacspec.org/a/catalog.json',
             'http://stacspec.org/a/b/c/catalog.json', '../../catalog.json'),
            ('http://stacspec.org/a/catalog.json',
             'http://cogeo.org/a/b/c/catalog.json',
             'http://stacspec.org/a/catalog.json'),
            ('http://stacspec.org/a/catalog.json',
             'https://stacspec.org/a/b/c/catalog.json',
             'http://stacspec.org/a/catalog.json')
        ]

        for source_href, start_href, expected in test_cases:
            actual = make_relative_href(source_href, start_href)
            self.assertEqual(actual, expected)

    def test_make_absolute_href(self):
        # Test cases of (source_href, start_href, expected)
        test_cases = [
            ('item.json', '/a/b/c/catalog.json', '/a/b/c/item.json'),
            ('./item.json', '/a/b/c/catalog.json', '/a/b/c/item.json'),
            ('./z/item.json', '/a/b/c/catalog.json', '/a/b/c/z/item.json'),
            ('../item.json', '/a/b/c/catalog.json', '/a/b/item.json'),
            ('item.json', 'https://stacgeo.org/a/b/c/catalog.json',
             'https://stacgeo.org/a/b/c/item.json'),
            ('./item.json', 'https://stacgeo.org/a/b/c/catalog.json',
             'https://stacgeo.org/a/b/c/item.json'),
            ('./z/item.json', 'https://stacgeo.org/a/b/c/catalog.json',
             'https://stacgeo.org/a/b/c/z/item.json'),
            ('../item.json', 'https://stacgeo.org/a/b/c/catalog.json',
             'https://stacgeo.org/a/b/item.json')
        ]

        for source_href, start_href, expected in test_cases:
            actual = make_absolute_href(source_href, start_href)
            self.assertEqual(actual, expected)

    def test_is_absolute_href(self):
        # Test cases of (href, expected)
        test_cases = [('item.json', False), ('./item.json', False),
                      ('../item.json', False), ('/item.json', True),
                      ('http://stacgeo.org/item.json', True)]

        for href, expected in test_cases:
            actual = is_absolute_href(href)
            self.assertEqual(actual, expected)
