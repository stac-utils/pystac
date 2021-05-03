import os
import unittest

import pystac
from tests.utils import TestCases


class VersionTest(unittest.TestCase):
    def setUp(self):
        self._prev_env_version = os.environ.get("PYSTAC_STAC_VERSION_OVERRIDE")
        self._prev_version = pystac.get_stac_version()

    def tearDown(self):
        if self._prev_env_version is None:
            os.environ.pop("PYSTAC_STAC_VERSION_OVERRIDE", None)
        else:
            os.environ["PYSTAC_STAC_VERSION_OVERRIDE"] = self._prev_env_version
        pystac.set_stac_version(None)

    def test_override_stac_version_with_environ(self):

        override_version = "1.0.0-gamma.2"
        os.environ["PYSTAC_STAC_VERSION_OVERRIDE"] = override_version
        cat = TestCases.test_case_1()
        d = cat.to_dict()
        self.assertEqual(d["stac_version"], override_version)

    def test_override_stac_version_with_call(self):
        override_version = "1.0.0-delta.2"
        pystac.set_stac_version(override_version)
        cat = TestCases.test_case_1()
        d = cat.to_dict()
        self.assertEqual(d["stac_version"], override_version)
