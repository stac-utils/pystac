import unittest
import warnings

from pystac.stac_io import STAC_IO
from tests.utils import TestCases


class StacIOTest(unittest.TestCase):
    def test_stac_io_issues_warnings(self):
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")
            # Trigger a warning.
            STAC_IO.read_text(
                TestCases.get_path("data-files/collections/multi-extent.json")
            )

            # Verify some things
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
