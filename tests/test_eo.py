import os
import unittest
import json

from pystac import *
from pystac.eo import EOAsset, EOItem, Band, band_desc, band_range, eo_key


class EOAssetTest(unittest.TestCase):
    def test_eo_asseet(self):
        pass

class EOItemTest(unittest.TestCase):
    def test_eo_item(self):
        pass

class BandTest(unittest.TestCase):
    def test_band(self):
        pass

class EOUtilsTest(unittest.TestCase):
    def test_band_desc(self):
        desc = 'Common name: nir, Range: 0.75 to 1.0'
        self.assertEqual(band_desc('nir'), desc)
        self.assertEqual(band_desc('uncommon name'), 'Common name: uncommon name')

    def test_band_range(self):
        self.assertEqual(band_range('pan'), (0.50, 0.70))
        self.assertEqual(band_range('uncommon name'), 'uncommon name')

    def test_eo_key(self):
        self.assertEqual(eo_key(''), 'eo:')
        self.assertEqual(eo_key('dsg'), 'eo:dsg')       

