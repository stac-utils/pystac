import os
import unittest
from unittest.mock import patch

from pystac.version import STACVersion, set_stac_version
from tests.utils.test_cases import TestCases


class VersionTest(unittest.TestCase):
    def setUp(self) -> None:
        STACVersion._override_version = None

    def test_override_stac_version_with_environ(self) -> None:
        override_version = "1.0.0-gamma.2"
        with patch.dict(os.environ, {"PYSTAC_STAC_VERSION_OVERRIDE": override_version}):
            cat = TestCases.test_case_1()
            d = cat.to_dict()
        self.assertEqual(d["stac_version"], override_version)

    def test_override_stac_version_with_call(self) -> None:
        override_version = "1.0.0-delta.2"
        set_stac_version(override_version)
        cat = TestCases.test_case_1()
        d = cat.to_dict()
        self.assertEqual(d["stac_version"], override_version)
