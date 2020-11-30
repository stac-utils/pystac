import json
import unittest

import pystac
from pystac import Item
from pystac.extensions.eo import Band
from tests.utils import (TestCases, test_to_from_dict)


class EOTest(unittest.TestCase):
    LANDSAT_EXAMPLE_URI = TestCases.get_path('data-files/eo/eo-landsat-example.json')
    BANDS_IN_ITEM_URI = TestCases.get_path('data-files/eo/sample-bands-in-item-properties.json')

    def setUp(self):
        self.maxDiff = None

    def test_to_from_dict(self):
        with open(self.LANDSAT_EXAMPLE_URI) as f:
            item_dict = json.load(f)
        test_to_from_dict(self, Item, item_dict)

    def test_validate_eo(self):
        item = pystac.read_file(self.LANDSAT_EXAMPLE_URI)
        item2 = pystac.read_file(self.BANDS_IN_ITEM_URI)
        item.validate()
        item2.validate()

    def test_bands(self):
        eo_item = pystac.read_file(self.BANDS_IN_ITEM_URI)

        # Get
        self.assertIn("eo:bands", eo_item.properties)
        bands = eo_item.ext.eo.bands
        self.assertEqual(list(map(lambda x: x.name, bands)), ['band1', 'band2', 'band3', 'band4'])

        # Set
        new_bands = [
            Band.create(name="red", description=Band.band_description("red")),
            Band.create(name="green", description=Band.band_description("green")),
            Band.create(name="blue", description=Band.band_description("blue")),
        ]

        eo_item.ext.eo.bands = new_bands
        self.assertEqual('Common name: red, Range: 0.6 to 0.7',
                         eo_item.properties['eo:bands'][0]['description'])
        self.assertEqual(len(eo_item.ext.eo.bands), 3)
        eo_item.validate()

    def test_asset_bands(self):
        eo_item = pystac.read_file(self.LANDSAT_EXAMPLE_URI)

        # Get

        b1_asset = eo_item.assets['B1']
        asset_bands = eo_item.ext.eo.get_bands(b1_asset)
        self.assertIsNot(None, asset_bands)
        self.assertEqual(len(asset_bands), 1)
        self.assertEqual(asset_bands[0].name, 'B1')

        index_asset = eo_item.assets['index']
        asset_bands = eo_item.ext.eo.get_bands(index_asset)
        self.assertIs(None, asset_bands)

        # No asset specified
        asset_bands = eo_item.ext.eo.get_bands()
        self.assertIsNot(None, asset_bands)

        # Set
        b2_asset = eo_item.assets['B2']
        self.assertEqual(eo_item.ext.eo.get_bands(b2_asset)[0].name, "B2")
        eo_item.ext.eo.set_bands(eo_item.ext.eo.get_bands(b1_asset), b2_asset)

        new_b2_asset_bands = eo_item.ext.eo.get_bands(eo_item.assets['B2'])

        self.assertEqual(new_b2_asset_bands[0].name, 'B1')

        eo_item.validate()

        # Check adding a new asset
        new_bands = [
            Band.create(name="red", description=Band.band_description("red")),
            Band.create(name="green", description=Band.band_description("green")),
            Band.create(name="blue", description=Band.band_description("blue")),
        ]
        asset = pystac.Asset(href="some/path.tif", media_type=pystac.MediaType.GEOTIFF)
        eo_item.ext.eo.set_bands(new_bands, asset)
        eo_item.add_asset("test", asset)

        self.assertEqual(len(eo_item.assets["test"].properties["eo:bands"]), 3)

    def test_cloud_cover(self):
        item = pystac.read_file(self.LANDSAT_EXAMPLE_URI)

        # Get
        self.assertIn("eo:cloud_cover", item.properties)
        cloud_cover = item.ext.eo.cloud_cover
        self.assertEqual(cloud_cover, 78)

        # Set
        item.ext.eo.cloud_cover = 50
        self.assertEqual(item.properties['eo:cloud_cover'], 50)

        # Get from Asset
        b2_asset = item.assets['B2']
        self.assertEqual(item.ext.eo.get_cloud_cover(b2_asset), item.ext.eo.get_cloud_cover())

        b3_asset = item.assets['B3']
        self.assertEqual(item.ext.eo.get_cloud_cover(b3_asset), 20)

        # Set on Asset
        item.ext.eo.set_cloud_cover(10, b2_asset)
        self.assertEqual(item.ext.eo.get_cloud_cover(b2_asset), 10)

        item.validate()

    def test_read_pre_09_fields_into_common_metadata(self):
        eo_item = pystac.read_file(
            TestCases.get_path('data-files/examples/0.8.1/item-spec/examples/'
                               'landsat8-sample.json'))

        self.assertEqual(eo_item.common_metadata.platform, "landsat-8")
        self.assertEqual(eo_item.common_metadata.instruments, ["oli_tirs"])

    def test_reads_asset_bands_in_pre_1_0_version(self):
        eo_item = pystac.read_file(
            TestCases.get_path('data-files/examples/0.9.0/item-spec/examples/'
                               'landsat8-sample.json'))

        bands = eo_item.ext.eo.get_bands(eo_item.assets['B9'])

        self.assertEqual(len(bands), 1)
        self.assertEqual(bands[0].common_name, 'cirrus')

    def test_reads_gsd_in_pre_1_0_version(self):
        eo_item = pystac.read_file(
            TestCases.get_path('data-files/examples/0.9.0/item-spec/examples/'
                               'landsat8-sample.json'))

        self.assertEqual(eo_item.common_metadata.gsd, 30.0)
