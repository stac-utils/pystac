import json
import unittest

import pystac
from pystac import ExtensionTypeError, Item
from pystac.utils import get_opt
from pystac.extensions.raster import (
    Histogram,
    RasterExtension,
    RasterBand,
    Sampling,
    DataType,
    Statistics,
)
from tests.utils import TestCases, assert_to_from_dict


class RasterTest(unittest.TestCase):
    PLANET_EXAMPLE_URI = TestCases.get_path(
        "data-files/raster/raster-planet-example.json"
    )
    SENTINEL2_EXAMPLE_URI = TestCases.get_path(
        "data-files/raster/raster-sentinel2-example.json"
    )
    GDALINFO_EXAMPLE_URI = TestCases.get_path("data-files/raster/gdalinfo.json")

    def setUp(self) -> None:
        self.maxDiff = None

    def test_to_from_dict(self) -> None:
        with open(self.PLANET_EXAMPLE_URI) as f:
            item_dict = json.load(f)
        assert_to_from_dict(self, Item, item_dict)

    def test_validate_raster(self) -> None:
        item = pystac.Item.from_file(self.PLANET_EXAMPLE_URI)
        item2 = pystac.Item.from_file(self.SENTINEL2_EXAMPLE_URI)

        item.validate()
        item2.validate()

    def test_asset_bands(self) -> None:
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
        assert band0_stats is not None
        self.assertEqual(band0_stats.minimum, 1962)
        self.assertEqual(band0_stats.maximum, 32925)
        self.assertEqual(band0_stats.mean, 8498.9400644319)
        self.assertEqual(band0_stats.stddev, 5056.1292002722)
        self.assertEqual(band0_stats.valid_percent, 61.09)

        band0_hist = asset_bands[0].histogram
        assert band0_hist is not None
        self.assertEqual(band0_hist.count, 256)
        self.assertEqual(band0_hist.min, 1901.288235294118)
        self.assertEqual(band0_hist.max, 32985.71176470588)
        self.assertEqual(len(band0_hist.buckets), band0_hist.count)

        index_asset = item.assets["metadata"]
        asset_bands = RasterExtension.ext(index_asset).bands
        self.assertIs(None, asset_bands)

        # Set
        item2 = pystac.Item.from_file(self.SENTINEL2_EXAMPLE_URI)
        b2_asset = item2.assets["B02"]
        self.assertEqual(
            get_opt(get_opt(RasterExtension.ext(b2_asset).bands)[0].statistics).maximum,
            19264,
        )
        b1_asset = item2.assets["B01"]
        RasterExtension.ext(b2_asset).bands = RasterExtension.ext(b1_asset).bands

        new_b2_asset_bands = RasterExtension.ext(item2.assets["B02"]).bands

        self.assertEqual(
            get_opt(get_opt(new_b2_asset_bands)[0].statistics).maximum, 20567
        )

        item2.validate()

        # Check adding a new asset
        new_stats = [
            Statistics.create(
                minimum=0, maximum=10000, mean=5000, stddev=10, valid_percent=88
            ),
            Statistics.create(
                minimum=-1, maximum=1, mean=0, stddev=1, valid_percent=100
            ),
            Statistics.create(
                minimum=1, maximum=255, mean=200, stddev=3, valid_percent=100
            ),
        ]
        # new_histograms = []
        with open(self.GDALINFO_EXAMPLE_URI) as gdaljson_file:
            gdaljson_data = json.load(gdaljson_file)
            new_histograms = list(
                map(
                    lambda band: Histogram.from_dict(band["histogram"]),
                    gdaljson_data["bands"],
                )
            )
        new_bands = [
            RasterBand.create(
                nodata=1,
                unit="test1",
                statistics=new_stats[0],
                histogram=new_histograms[0],
            ),
            RasterBand.create(
                nodata=2,
                unit="test2",
                statistics=new_stats[1],
                histogram=new_histograms[1],
            ),
            RasterBand.create(
                nodata=3,
                unit="test3",
                statistics=new_stats[2],
                histogram=new_histograms[2],
            ),
        ]
        asset = pystac.Asset(href="some/path.tif", media_type=pystac.MediaType.GEOTIFF)
        RasterExtension.ext(asset).bands = new_bands
        item.add_asset("test", asset)

        self.assertEqual(len(item.assets["test"].extra_fields["raster:bands"]), 3)
        self.assertEqual(
            item.assets["test"].extra_fields["raster:bands"][1]["statistics"][
                "minimum"
            ],
            -1,
        )
        self.assertEqual(
            item.assets["test"].extra_fields["raster:bands"][1]["histogram"]["min"],
            3848.354901960784,
        )

        for s in new_stats:
            s.minimum = None
            s.maximum = None
            s.mean = None
            s.stddev = None
            s.valid_percent = None
            self.assertEqual(len(s.properties), 0)

        for b in new_bands:
            b.bits_per_sample = None
            b.data_type = None
            b.histogram = None
            b.nodata = None
            b.sampling = None
            b.scale = None
            b.spatial_resolution = None
            b.statistics = None
            b.unit = None
            b.offset = None
            self.assertEqual(len(b.properties), 0)

        new_stats[2].apply(
            minimum=0, maximum=10000, mean=5000, stddev=10, valid_percent=88
        )
        new_stats[1].apply(minimum=-1, maximum=1, mean=0, stddev=1, valid_percent=100)
        new_stats[0].apply(
            minimum=1, maximum=255, mean=200, stddev=3, valid_percent=100
        )
        new_bands[2].apply(
            nodata=1,
            unit="test1",
            statistics=new_stats[2],
            histogram=new_histograms[0],
        )
        new_bands[1].apply(
            nodata=2,
            unit="test2",
            statistics=new_stats[1],
            histogram=new_histograms[1],
        )
        new_bands[0].apply(
            nodata=3,
            unit="test3",
            statistics=new_stats[0],
            histogram=new_histograms[2],
        )
        RasterExtension.ext(item.assets["test"]).apply(new_bands)
        self.assertEqual(
            item.assets["test"].extra_fields["raster:bands"][0]["statistics"][
                "minimum"
            ],
            1,
        )

    def test_extension_not_implemented(self) -> None:
        # Should raise exception if Item does not include extension URI
        item = pystac.Item.from_file(self.PLANET_EXAMPLE_URI)
        item.stac_extensions.remove(RasterExtension.get_schema_uri())

        # Should raise exception if owning Item does not include extension URI
        asset = item.assets["data"]

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = RasterExtension.ext(asset)

        # Should succeed if Asset has no owner
        ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
        _ = RasterExtension.ext(ownerless_asset)

    def test_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.PLANET_EXAMPLE_URI)
        item.stac_extensions.remove(RasterExtension.get_schema_uri())
        asset = item.assets["data"]

        _ = RasterExtension.ext(asset, add_if_missing=True)

        self.assertIn(RasterExtension.get_schema_uri(), item.stac_extensions)

    def test_should_raise_exception_when_passing_invalid_extension_object(
        self,
    ) -> None:
        self.assertRaisesRegex(
            ExtensionTypeError,
            r"^Raster extension does not apply to type 'object'$",
            RasterExtension.ext,
            object(),
        )
