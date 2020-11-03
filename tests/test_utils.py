import unittest
import os
import json
import ntpath
from datetime import datetime, timezone, timedelta

from pystac import utils

from pystac.utils import (make_relative_href, make_absolute_href, is_absolute_href)


class UtilsTest(unittest.TestCase):
    def test_make_relative_href(self):
        # Test cases of (source_href, start_href, expected)
        test_cases = [
            ('/a/b/c/d/catalog.json', '/a/b/c/catalog.json', './d/catalog.json'),
            ('/a/b/catalog.json', '/a/b/c/catalog.json', '../catalog.json'),
            ('/a/catalog.json', '/a/b/c/catalog.json', '../../catalog.json'),
            ('http://stacspec.org/a/b/c/d/catalog.json', 'http://stacspec.org/a/b/c/catalog.json',
             './d/catalog.json'),
            ('http://stacspec.org/a/b/catalog.json', 'http://stacspec.org/a/b/c/catalog.json',
             '../catalog.json'),
            ('http://stacspec.org/a/catalog.json', 'http://stacspec.org/a/b/c/catalog.json',
             '../../catalog.json'),
            ('http://stacspec.org/a/catalog.json', 'http://cogeo.org/a/b/c/catalog.json',
             'http://stacspec.org/a/catalog.json'),
            ('http://stacspec.org/a/catalog.json', 'https://stacspec.org/a/b/c/catalog.json',
             'http://stacspec.org/a/catalog.json')
        ]

        for source_href, start_href, expected in test_cases:
            actual = make_relative_href(source_href, start_href)
            self.assertEqual(actual, expected)

    def test_make_relative_href_windows(self):
        utils._pathlib = ntpath
        try:
            # Test cases of (source_href, start_href, expected)
            test_cases = [
                ('C:\\a\\b\\c\\d\\catalog.json', 'C:\\a\\b\\c\\catalog.json', '.\\d\\catalog.json'),
                ('C:\\a\\b\\catalog.json', 'C:\\a\\b\\c\\catalog.json', '..\\catalog.json'),
                ('C:\\a\\catalog.json', 'C:\\a\\b\\c\\catalog.json', '..\\..\\catalog.json'),
                ('a\\b\\c\\catalog.json', 'a\\b\\catalog.json', '.\\c\\catalog.json'),
                ('a\\b\\catalog.json', 'a\\b\\c\\catalog.json', '..\\catalog.json'),
                ('http://stacspec.org/a/b/c/d/catalog.json',
                 'http://stacspec.org/a/b/c/catalog.json', './d/catalog.json'),
                ('http://stacspec.org/a/b/catalog.json', 'http://stacspec.org/a/b/c/catalog.json',
                 '../catalog.json'),
                ('http://stacspec.org/a/catalog.json', 'http://stacspec.org/a/b/c/catalog.json',
                 '../../catalog.json'),
                ('http://stacspec.org/a/catalog.json', 'http://cogeo.org/a/b/c/catalog.json',
                 'http://stacspec.org/a/catalog.json'),
                ('http://stacspec.org/a/catalog.json', 'https://stacspec.org/a/b/c/catalog.json',
                 'http://stacspec.org/a/catalog.json')
            ]

            for source_href, start_href, expected in test_cases:
                actual = make_relative_href(source_href, start_href)
                self.assertEqual(actual, expected)
        finally:
            utils._pathlib = os.path

    def test_make_absolute_href(self):
        # Test cases of (source_href, start_href, expected)
        test_cases = [('item.json', '/a/b/c/catalog.json', '/a/b/c/item.json'),
                      ('./item.json', '/a/b/c/catalog.json', '/a/b/c/item.json'),
                      ('./z/item.json', '/a/b/c/catalog.json', '/a/b/c/z/item.json'),
                      ('../item.json', '/a/b/c/catalog.json', '/a/b/item.json'),
                      ('item.json', 'https://stacspec.org/a/b/c/catalog.json',
                       'https://stacspec.org/a/b/c/item.json'),
                      ('./item.json', 'https://stacspec.org/a/b/c/catalog.json',
                       'https://stacspec.org/a/b/c/item.json'),
                      ('./z/item.json', 'https://stacspec.org/a/b/c/catalog.json',
                       'https://stacspec.org/a/b/c/z/item.json'),
                      ('../item.json', 'https://stacspec.org/a/b/c/catalog.json',
                       'https://stacspec.org/a/b/item.json')]

        for source_href, start_href, expected in test_cases:
            actual = make_absolute_href(source_href, start_href)
            self.assertEqual(actual, expected)

    def test_make_absolute_href_on_vsitar(self):
        rel_path = 'some/item.json'
        cat_path = '/vsitar//tmp/catalog.tar/catalog.json'
        expected = '/vsitar//tmp/catalog.tar/some/item.json'

        self.assertEqual(expected, make_absolute_href(rel_path, cat_path))

    def test_make_absolute_href_windows(self):
        utils._pathlib = ntpath
        try:
            # Test cases of (source_href, start_href, expected)
            test_cases = [('item.json', 'C:\\a\\b\\c\\catalog.json', 'c:\\a\\b\\c\\item.json'),
                          ('.\\item.json', 'C:\\a\\b\\c\\catalog.json', 'c:\\a\\b\\c\\item.json'),
                          ('.\\z\\item.json', 'Z:\\a\\b\\c\\catalog.json',
                           'z:\\a\\b\\c\\z\\item.json'),
                          ('..\\item.json', 'a:\\a\\b\\c\\catalog.json', 'a:\\a\\b\\item.json'),
                          ('item.json', 'HTTPS://stacspec.org/a/b/c/catalog.json',
                           'https://stacspec.org/a/b/c/item.json'),
                          ('./item.json', 'https://stacspec.org/a/b/c/catalog.json',
                           'https://stacspec.org/a/b/c/item.json'),
                          ('./z/item.json', 'https://stacspec.org/a/b/c/catalog.json',
                           'https://stacspec.org/a/b/c/z/item.json'),
                          ('../item.json', 'https://stacspec.org/a/b/c/catalog.json',
                           'https://stacspec.org/a/b/item.json')]

            for source_href, start_href, expected in test_cases:
                actual = make_absolute_href(source_href, start_href)
                self.assertEqual(actual, expected)
        finally:
            utils._pathlib = os.path

    def test_is_absolute_href(self):
        # Test cases of (href, expected)
        test_cases = [('item.json', False), ('./item.json', False), ('../item.json', False),
                      ('/item.json', True), ('http://stacspec.org/item.json', True)]

        for href, expected in test_cases:
            actual = is_absolute_href(href)
            self.assertEqual(actual, expected)

    def test_is_absolute_href_windows(self):
        utils._pathlib = ntpath
        try:

            # Test cases of (href, expected)
            test_cases = [('item.json', False), ('.\\item.json', False), ('..\\item.json', False),
                          ('c:\\item.json', True), ('http://stacspec.org/item.json', True)]

            for href, expected in test_cases:
                actual = is_absolute_href(href)
                self.assertEqual(actual, expected)
        finally:
            utils._pathlib = os.path

    def test_datetime_to_str(self):
        cases = (
            ('timezone naive, assume utc', datetime(2000, 1, 1), '2000-01-01T00:00:00Z'),
            ('timezone aware, utc', datetime(2000, 1, 1,
                                             tzinfo=timezone.utc), '2000-01-01T00:00:00Z'),
            ('timezone aware, utc -7', datetime(2000, 1, 1, tzinfo=timezone(timedelta(hours=-7))),
             '2000-01-01T00:00:00-07:00'),
        )

        for title, dt, expected in cases:
            with self.subTest(title=title):
                got = utils.datetime_to_str(dt)
                self.assertEqual(expected, got)

    def test_geojson_bbox(self):
        # Use sample Geojson from https://en.wikipedia.org/wiki/GeoJSON
        with open('tests/data-files/geojson/sample.geojson') as sample_geojson:
            all_features = json.load(sample_geojson)
            geom_dicts = [f['geometry'] for f in all_features['features']]
            for geom in geom_dicts:
                got = utils.geometry_to_bbox(geom)
                self.assertNotEqual(got, None)
