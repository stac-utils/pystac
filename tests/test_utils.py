import json
import ntpath
import os
import sys
import time
import unittest
from datetime import datetime, timedelta, timezone
from typing import Optional

import pytest
from dateutil import tz

from pystac import utils
from pystac.utils import (
    is_absolute_href,
    make_absolute_href,
    make_relative_href,
    now_in_utc,
    now_to_rfc3339_str,
    str_to_datetime,
)
from tests.utils import TestCases


class UtilsTest(unittest.TestCase):
    @unittest.skipIf(
        sys.platform in ("win32", "cygwin"), reason="Paths are specific to posix"
    )
    def test_make_relative_href(self) -> None:
        # Test cases of (source_href, start_href, expected)
        test_cases = [
            ("/a/b/c/d/catalog.json", "/a/b/c/catalog.json", "./d/catalog.json"),
            ("/a/b/catalog.json", "/a/b/c/catalog.json", "../catalog.json"),
            ("/a/catalog.json", "/a/b/c/catalog.json", "../../catalog.json"),
            ("/a/b/c/d/", "/a/b/c/catalog.json", "./d/"),
            ("/a/b/c/d/.dotfile", "/a/b/c/d/catalog.json", "./.dotfile"),
        ]

        for source_href, start_href, expected in test_cases:
            actual = make_relative_href(source_href, start_href)
            self.assertEqual(actual, expected)

    def test_make_relative_href_url(self) -> None:
        test_cases = [
            (
                "http://stacspec.org/a/b/c/d/catalog.json",
                "http://stacspec.org/a/b/c/catalog.json",
                "./d/catalog.json",
            ),
            (
                "http://stacspec.org/a/b/catalog.json",
                "http://stacspec.org/a/b/c/catalog.json",
                "../catalog.json",
            ),
            (
                "http://stacspec.org/a/catalog.json",
                "http://stacspec.org/a/b/c/catalog.json",
                "../../catalog.json",
            ),
            (
                "http://stacspec.org/a/catalog.json",
                "http://cogeo.org/a/b/c/catalog.json",
                "http://stacspec.org/a/catalog.json",
            ),
            (
                "http://stacspec.org/a/catalog.json",
                "https://stacspec.org/a/b/c/catalog.json",
                "http://stacspec.org/a/catalog.json",
            ),
            (
                "http://stacspec.org/a/",
                "https://stacspec.org/a/b/c/catalog.json",
                "http://stacspec.org/a/",
            ),
            (
                "http://stacspec.org/a/b/.dotfile",
                "http://stacspec.org/a/b/catalog.json",
                "./.dotfile",
            ),
        ]

        for source_href, start_href, expected in test_cases:
            actual = make_relative_href(source_href, start_href)
            self.assertEqual(actual, expected)

    def test_make_relative_href_windows(self) -> None:
        utils._pathlib = ntpath
        try:
            # Test cases of (source_href, start_href, expected)
            test_cases = [
                (
                    "C:\\a\\b\\c\\d\\catalog.json",
                    "C:\\a\\b\\c\\catalog.json",
                    ".\\d\\catalog.json",
                ),
                (
                    "C:\\a\\b\\catalog.json",
                    "C:\\a\\b\\c\\catalog.json",
                    "..\\catalog.json",
                ),
                (
                    "C:\\a\\catalog.json",
                    "C:\\a\\b\\c\\catalog.json",
                    "..\\..\\catalog.json",
                ),
                ("a\\b\\c\\catalog.json", "a\\b\\catalog.json", ".\\c\\catalog.json"),
                ("a\\b\\catalog.json", "a\\b\\c\\catalog.json", "..\\catalog.json"),
                (
                    "http://stacspec.org/a/b/c/d/catalog.json",
                    "http://stacspec.org/a/b/c/catalog.json",
                    "./d/catalog.json",
                ),
                (
                    "http://stacspec.org/a/b/catalog.json",
                    "http://stacspec.org/a/b/c/catalog.json",
                    "../catalog.json",
                ),
                (
                    "http://stacspec.org/a/catalog.json",
                    "http://stacspec.org/a/b/c/catalog.json",
                    "../../catalog.json",
                ),
                (
                    "http://stacspec.org/a/catalog.json",
                    "http://cogeo.org/a/b/c/catalog.json",
                    "http://stacspec.org/a/catalog.json",
                ),
                (
                    "http://stacspec.org/a/catalog.json",
                    "https://stacspec.org/a/b/c/catalog.json",
                    "http://stacspec.org/a/catalog.json",
                ),
            ]

            for source_href, start_href, expected in test_cases:
                actual = make_relative_href(source_href, start_href)
                self.assertEqual(actual, expected)
        finally:
            utils._pathlib = os.path

    @unittest.skipIf(
        sys.platform in ("win32", "cygwin"), reason="Paths are specific to posix"
    )
    def test_make_absolute_href(self) -> None:
        # Test cases of (source_href, start_href, expected)
        test_cases = [
            ("item.json", "/a/b/c/catalog.json", "/a/b/c/item.json"),
            ("./item.json", "/a/b/c/catalog.json", "/a/b/c/item.json"),
            ("./z/item.json", "/a/b/c/catalog.json", "/a/b/c/z/item.json"),
            ("../item.json", "/a/b/c/catalog.json", "/a/b/item.json"),
            (
                "item.json",
                "https://stacspec.org/a/b/c/catalog.json",
                "https://stacspec.org/a/b/c/item.json",
            ),
            (
                "./item.json",
                "https://stacspec.org/a/b/c/catalog.json",
                "https://stacspec.org/a/b/c/item.json",
            ),
            (
                "./z/item.json",
                "https://stacspec.org/a/b/c/catalog.json",
                "https://stacspec.org/a/b/c/z/item.json",
            ),
            (
                "../item.json",
                "https://stacspec.org/a/b/c/catalog.json",
                "https://stacspec.org/a/b/item.json",
            ),
            ("http://localhost:8000", None, "http://localhost:8000"),
        ]

        for source_href, start_href, expected in test_cases:
            actual = make_absolute_href(source_href, start_href)
            self.assertEqual(actual, expected)

    @unittest.skipIf(
        sys.platform in ("win32", "cygwin"), reason="Paths are specific to posix"
    )
    def test_make_absolute_href_on_vsitar(self) -> None:
        rel_path = "some/item.json"
        cat_path = "/vsitar//tmp/catalog.tar/catalog.json"
        expected = "/vsitar//tmp/catalog.tar/some/item.json"

        self.assertEqual(expected, make_absolute_href(rel_path, cat_path))

    def test_make_absolute_href_windows(self) -> None:
        utils._pathlib = ntpath
        try:
            # Test cases of (source_href, start_href, expected)
            test_cases = [
                ("item.json", "C:\\a\\b\\c\\catalog.json", "C:\\a\\b\\c\\item.json"),
                (".\\item.json", "C:\\a\\b\\c\\catalog.json", "C:\\a\\b\\c\\item.json"),
                (
                    ".\\z\\item.json",
                    "Z:\\a\\b\\c\\catalog.json",
                    "Z:\\a\\b\\c\\z\\item.json",
                ),
                ("..\\item.json", "a:\\a\\b\\c\\catalog.json", "a:\\a\\b\\item.json"),
                (
                    "item.json",
                    "HTTPS://stacspec.org/a/b/c/catalog.json",
                    "https://stacspec.org/a/b/c/item.json",
                ),
                (
                    "./item.json",
                    "https://stacspec.org/a/b/c/catalog.json",
                    "https://stacspec.org/a/b/c/item.json",
                ),
                (
                    "./z/item.json",
                    "https://stacspec.org/a/b/c/catalog.json",
                    "https://stacspec.org/a/b/c/z/item.json",
                ),
                (
                    "../item.json",
                    "https://stacspec.org/a/b/c/catalog.json",
                    "https://stacspec.org/a/b/item.json",
                ),
            ]

            for source_href, start_href, expected in test_cases:
                actual = make_absolute_href(source_href, start_href)
                self.assertEqual(actual, expected)
        finally:
            utils._pathlib = os.path

    def test_is_absolute_href(self) -> None:
        # Test cases of (href, expected)
        test_cases = [
            ("item.json", False),
            ("./item.json", False),
            ("../item.json", False),
            ("/item.json", True),
            ("http://stacspec.org/item.json", True),
        ]

        for href, expected in test_cases:
            actual = is_absolute_href(href)
            self.assertEqual(actual, expected)

    def test_is_absolute_href_windows(self) -> None:
        utils._pathlib = ntpath
        try:
            # Test cases of (href, expected)
            test_cases = [
                ("item.json", False),
                (".\\item.json", False),
                ("..\\item.json", False),
                ("c:\\item.json", True),
                ("http://stacspec.org/item.json", True),
            ]

            for href, expected in test_cases:
                actual = is_absolute_href(href)
                self.assertEqual(actual, expected)
        finally:
            utils._pathlib = os.path

    def test_datetime_to_str(self) -> None:
        cases = (
            (
                "timezone naive, assume utc",
                datetime(2000, 1, 1),
                "2000-01-01T00:00:00Z",
            ),
            (
                "timezone aware, utc",
                datetime(2000, 1, 1, tzinfo=timezone.utc),
                "2000-01-01T00:00:00Z",
            ),
            (
                "timezone aware, utc -7",
                datetime(2000, 1, 1, tzinfo=timezone(timedelta(hours=-7))),
                "2000-01-01T00:00:00-07:00",
            ),
        )

        for title, dt, expected in cases:
            with self.subTest(title=title):
                got = utils.datetime_to_str(dt)
                self.assertEqual(expected, got)

    def test_datetime_to_str_with_microseconds_timespec(self) -> None:
        cases = (
            (
                "timezone naive, assume utc",
                datetime(2000, 1, 1, 0, 0, 0, 0),
                "2000-01-01T00:00:00.000000Z",
            ),
            (
                "timezone aware, utc",
                datetime(2000, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc),
                "2000-01-01T00:00:00.000000Z",
            ),
            (
                "timezone aware, utc -7",
                datetime(2000, 1, 1, 0, 0, 0, 0, tzinfo=timezone(timedelta(hours=-7))),
                "2000-01-01T00:00:00.000000-07:00",
            ),
        )

        for title, dt, expected in cases:
            with self.subTest(title=title):
                got = utils.datetime_to_str(dt, timespec="microseconds")
                self.assertEqual(expected, got)

    def test_str_to_datetime(self) -> None:
        def _set_tzinfo(tz_str: Optional[str]) -> None:
            if tz_str is None:
                if "TZ" in os.environ:
                    del os.environ["TZ"]
            else:
                os.environ["TZ"] = tz_str
            # time.tzset() only available for Unix/Linux
            if hasattr(time, "tzset"):
                time.tzset()

        utc_timestamp = "2015-06-27T10:25:31Z"

        prev_tz = os.environ.get("TZ")

        with self.subTest(tz=None):
            _set_tzinfo(None)
            utc_datetime = str_to_datetime(utc_timestamp)
            self.assertIs(utc_datetime.tzinfo, tz.tzutc())
            self.assertIsNot(utc_datetime.tzinfo, tz.tzlocal())

        with self.subTest(tz="UTC"):
            _set_tzinfo("UTC")
            utc_datetime = str_to_datetime(utc_timestamp)
            self.assertIs(utc_datetime.tzinfo, tz.tzutc())
            self.assertIsNot(utc_datetime.tzinfo, tz.tzlocal())

        with self.subTest(tz="US/Central"):
            _set_tzinfo("US/Central")
            utc_datetime = str_to_datetime(utc_timestamp)
            self.assertIs(utc_datetime.tzinfo, tz.tzutc())
            self.assertIsNot(utc_datetime.tzinfo, tz.tzlocal())

        if prev_tz is not None:
            _set_tzinfo(prev_tz)

    def test_geojson_bbox(self) -> None:
        # Use sample Geojson from https://en.wikipedia.org/wiki/GeoJSON
        with open(
            TestCases.get_path("data-files/geojson/sample.geojson")
        ) as sample_geojson:
            all_features = json.load(sample_geojson)
            geom_dicts = [f["geometry"] for f in all_features["features"]]
            for geom in geom_dicts:
                got = utils.geometry_to_bbox(geom)
                self.assertNotEqual(got, None)


@pytest.mark.parametrize(
    "datetime",
    [
        "37-01-01T12:00:27.87Z",  # invalid year, must be 4 digits
        "21985-12-12T23:20:50.52Z",  # year must be 4 digits
        "1985-13-12T23:20:50.52Z",  # month > 12
        "1985-12-32T23:20:50.52Z",  # day > 31
        "1985-12-01T25:20:50.52Z",  # hour > 24
        "1985-12-01T00:60:50.52Z",  # minute > 59
        "1985-12-01T00:06:61.52Z",  # second > 60
        "1985-04-12T23:20:50.Z",  # fractional sec . but no frac secs
        "1985-04-12T23:20:50,Z",  # fractional sec , but no frac secs
        "1990-12-31T23:59:61Z",  # second > 60 w/o fractional seconds
    ],
)
def test_parse_invalid_rfc3339_str_to_datetime(datetime: str) -> None:
    with pytest.raises(ValueError):
        str_to_datetime(datetime)


@pytest.mark.parametrize(
    "datetime",
    [
        "1985-04-12",  # date only
        "1937-01-01T12:00:27.87+0100",  # invalid TZ format, no sep :
        "1985-12-12T23:20:50.52",  # no TZ
        "1985-04-12T23:20:50,52Z",  # comma as frac sec sep disallowed in RFC3339
    ],
)
def test_parse_invalid_rfc3339_but_valid_iso8601_str_to_datetime(datetime: str) -> None:
    assert str_to_datetime(datetime)


@pytest.mark.parametrize(
    "datetime",
    [
        "1985-04-12T23:20:50.52Z",
        "1996-12-19T16:39:57-00:00",
        "1996-12-19T16:39:57+00:00",
        "1996-12-19T16:39:57-08:00",
        "1996-12-19T16:39:57+08:00",
        "1937-01-01T12:00:27.87+01:00",
        "1985-04-12T23:20:50.52Z",
        "1937-01-01T12:00:27.8710+01:00",
        "1937-01-01T12:00:27.8+01:00",
        "1937-01-01T12:00:27.8Z",
        "2020-07-23T00:00:00.000+03:00",
        "2020-07-23T00:00:00+03:00",
        "1985-04-12t23:20:50.000z",
        "2020-07-23T00:00:00Z",
        "2020-07-23T00:00:00.0Z",
        "2020-07-23T00:00:00.01Z",
        "2020-07-23T00:00:00.012Z",
        "2020-07-23T00:00:00.0123Z",
        "2020-07-23T00:00:00.01234Z",
        "2020-07-23T00:00:00.012345Z",
        "2020-07-23T00:00:00.0123456Z",
        "2020-07-23T00:00:00.01234567Z",
        "2020-07-23T00:00:00.012345678Z",
    ],
)
def test_parse_valid_iso8601_str_to_datetime(datetime: str) -> None:
    assert str_to_datetime(datetime)


def test_now_functions() -> None:
    now1 = now_in_utc()
    time.sleep(1)
    now2 = now_in_utc()

    assert now1 < now2
    assert now1.tzinfo == timezone.utc

    assert str_to_datetime(now_to_rfc3339_str())
