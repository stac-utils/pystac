import json
import unittest

import pystac
from pystac import Item
from pystac.utils import get_opt
from pystac.extensions.raster import RasterExtension, RasterBand, Sampling, DataType
from tests.utils import TestCases, test_to_from_dict


class RasterTest(unittest.TestCase):
    PLANET_EXAMPLE_URI = TestCases.get_path(
        "data-files/raster/raster-planet-example.json"
    )
    SENTINEL2_EXAMPLE_URI = TestCases.get_path(
        "data-files/raster/raster-sentinel2-example.json"
    )

    def setUp(self):
        self.maxDiff = None

    def test_to_from_dict(self):
        with open(self.PLANET_EXAMPLE_URI) as f:
            item_dict = json.load(f)
        test_to_from_dict(self, Item, item_dict)

    def test_validate_raster(self):
        item = pystac.read_file(self.PLANET_EXAMPLE_URI)
        item2 = pystac.read_file(self.SENTINEL2_EXAMPLE_URI)
        item.validate()
        item2.validate()

    def test_asset_bands(self):
        item = pystac.Item.from_file(self.PLANET_EXAMPLE_URI)

        # Get
        data_asset = item.assets["data"]
        asset_bands = RasterExtension.ext(data_asset).bands
        assert asset_bands is not None
        self.assertEqual(len(asset_bands), 4)
        self.assertEqual(asset_bands[0].nodata, 0)
        self.assertEqual(asset_bands[0].sampling, Sampling.AREA)
        self.assertEqual(asset_bands[0].unit, "W⋅sr−1⋅m−2⋅nm−1")
        self.assertEqual(asset_bands[0].data_type, DataType.UINT16)
        self.assertEqual(asset_bands[0].scale, 0.01)
        self.assertEqual(asset_bands[0].offset, 0)
        self.assertEqual(asset_bands[0].spatial_resolution, 3)

        band0_stats = asset_bands[0].statistics

        self.assertEqual(band0_stats.maximum, 32925)
        self.assertEqual(band0_stats.mean, 8498.9400644319)
        self.assertEqual(band0_stats.minimum, 1962)
        self.assertEqual(band0_stats.stddev, 5056.1292002722)
        self.assertEqual(band0_stats.valid_percent, 61.09)

        index_asset = item.assets["metadata"]
        asset_bands = RasterExtension.ext(index_asset).bands
        self.assertIs(None, asset_bands)

        # Set
        item2 = pystac.Item.from_file(self.SENTINEL2_EXAMPLE_URI)
        b2_asset = item2.assets["B02"]
        self.assertEqual(
            get_opt(RasterExtension.ext(b2_asset).bands)[0].statistics.maximum, 19264
        )
        b1_asset = item2.assets["B01"]
        RasterExtension.ext(b2_asset).bands = RasterExtension.ext(b1_asset).bands

        new_b2_asset_bands = RasterExtension.ext(item2.assets["B02"]).bands

        self.assertEqual(get_opt(new_b2_asset_bands)[0].statistics.maximum, 20567)

        item2.validate()

        # Check adding a new asset
        new_bands = [
            RasterBand.create(nodata=1, unit="test1"),
            RasterBand.create(nodata=2, unit="test3"),
            RasterBand.create(nodata=3, unit="test3"),
        ]
        asset = pystac.Asset(href="some/path.tif", media_type=pystac.MediaType.GEOTIFF)
        RasterExtension.ext(asset).bands = new_bands
        item.add_asset("test", asset)

        self.assertEqual(len(item.assets["test"].properties["eo:bands"]), 3)
