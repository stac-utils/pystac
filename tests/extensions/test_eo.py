import json
import os
import unittest
from tempfile import TemporaryDirectory

import pystac
from pystac import (Catalog, CatalogType, Item, STACObjectType)
from pystac.extensions.eo import Band
from tests.utils import (SchemaValidator, STACValidationError, TestCases, test_to_from_dict)


class EOTest(unittest.TestCase):
    def setUp(self):
        self.validator = SchemaValidator()
        self.maxDiff = None
        self.URI_1 = TestCases.get_path('data-files/eo/eo-landsat-example.json')
        self.URI_2 = TestCases.get_path('data-files/eo/eo-landsat-example-INVALID.json')
        self.eoi = Item.from_file(self.URI_1)
        with open(self.URI_1) as f:
            self.eo_dict = json.load(f)

    def test_to_from_dict(self):
        test_to_from_dict(self, Item, self.eo_dict)

    def test_from_file(self):
        self.assertEqual(len(self.eoi.ext.eo.bands), 11)
        for b in self.eoi.ext.eo.bands:
            self.assertIsInstance(b, Band)
        self.assertEqual(len(self.eoi.links), 3)

        href = ('https://odu9mlf7d6.execute-api.us-east-1.amazonaws.com/stage/'
                'stac/search?id=LC08_L1TP_107018_20181001_20181001_01_RT')
        self.assertEqual(self.eoi.get_self_href(), href)

    def test_from_item(self):
        i = Item.from_file(self.URI_1)
        with self.assertRaises(AttributeError):
            getattr(i, 'bands')
        self.assertTrue('eo:bands' in i.properties.keys())
        eo_ext = i.ext.eo
        self.assertIsNotNone(getattr(eo_ext, 'bands'))

    def test_read_eo_item_owns_asset(self):
        item = Item.from_file(self.URI_1)
        assert len(item.assets) > 0
        for asset_key in item.assets:
            self.assertEqual(item.assets[asset_key].owner, item)

    def test_validate_eo(self):
        self.validator.validate_dict(self.eo_dict, STACObjectType.ITEM)

        with open(self.URI_2) as f:
            eo_dict_2 = json.load(f)

        try:
            self.validator.validate_dict(eo_dict_2, STACObjectType.ITEM)
        except STACValidationError as e:
            self.assertTrue('extension eo' in str(e))

        with TemporaryDirectory() as tmp_dir:
            cat_dir = os.path.join(tmp_dir, 'catalog')
            catalog = TestCases.test_case_1()
            eo_item = Item.from_dict(self.eo_dict)
            catalog.add_item(eo_item)
            catalog.normalize_and_save(cat_dir, catalog_type=CatalogType.ABSOLUTE_PUBLISHED)

            cat_read = Catalog.from_file(os.path.join(cat_dir, 'catalog.json'))
            eo_item_read = cat_read.get_item("LC08_L1TP_107018_20181001_20181001_01_RT")
            self.assertTrue(eo_item_read.ext.implements('eo'))
            self.validator.validate_object(eo_item_read)

    def test_gsd(self):
        eo_item = pystac.read_file(TestCases.get_path('data-files/eo/eo-landsat-example.json'))

        # Get
        self.assertIn("eo:gsd", eo_item.properties)
        eo_gsd = eo_item.ext.eo.gsd
        self.assertEqual(eo_gsd, eo_item.properties['eo:gsd'])

        # Set
        eo_item.ext.eo.gsd = eo_gsd + 100
        self.assertEqual(eo_gsd + 100, eo_item.properties['eo:gsd'])
        self.validator.validate_object(eo_item)

    def test_bands(self):
        eo_item = pystac.read_file(TestCases.get_path('data-files/eo/eo-landsat-example.json'))

        # Get
        self.assertIn("eo:bands", eo_item.properties)
        bands = eo_item.ext.eo.bands
        self.assertEqual(list(map(lambda x: x.name, bands)),
                         ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11'])
        for band in bands:
            self.assertIsInstance(band.common_name, str)
            self.assertIn(type(band.center_wavelength), [float, int])
            self.assertIn(type(band.full_width_half_max), [float, int])
            self.assertIs(None, band.description)

        # Ensure modifying the bands make changes on the item.
        bands_dict = {band.name: band for band in bands}
        bands_dict['B1'].description = "Band 1"

        self.assertTrue([x for x in eo_item.properties['eo:bands']
                         if x['name'] == 'B1'][0]['description'] == "Band 1")

        # Set
        new_bands = [
            Band.create(name="red", description=Band.band_description("red")),
            Band.create(name="green", description=Band.band_description("green")),
            Band.create(name="blue", description=Band.band_description("blue")),
        ]

        eo_item.ext.eo.bands = new_bands
        self.assertEqual('Common name: red, Range: 0.6 to 0.7',
                         eo_item.properties['eo:bands'][0]['description'])
        self.validator.validate_object(eo_item)

    def test_get_asset_bands(self):
        eo_item = pystac.read_file(TestCases.get_path('data-files/eo/eo-landsat-example.json'))

        b1_asset = eo_item.assets['B1']
        asset_bands = eo_item.ext.eo.get_asset_bands(b1_asset)
        self.assertIsNot(None, asset_bands)
        self.assertEqual(len(asset_bands), 1)
        self.assertEqual(asset_bands[0].name, 'B1')

        index_asset = eo_item.assets['index']
        asset_bands = eo_item.ext.eo.get_asset_bands(index_asset)
        self.assertIs(None, asset_bands)

    def test_set_asset_bands(self):
        eo_item = pystac.read_file(TestCases.get_path('data-files/eo/eo-landsat-example.json'))

        b1_asset = eo_item.assets['B1']
        eo_item.ext.eo.set_asset_bands(b1_asset, ['B2'])

        eo_item_mod = Item.from_dict(eo_item.to_dict())
        b1_asset_mod = eo_item_mod.assets['B1']
        asset_bands = eo_item_mod.ext.eo.get_asset_bands(b1_asset_mod)
        self.assertIsNot(None, asset_bands)
        self.assertEqual(len(asset_bands), 1)
        self.assertEqual(asset_bands[0].name, 'B2')

        self.validator.validate_object(eo_item)

        # Check setting with invalid keys

        with self.assertRaises(KeyError):
            eo_item.ext.eo.set_asset_bands(b1_asset, ['BAD_KEY', 'BAD_KEY_2'])

        # Check adding a new asset
        asset = pystac.Asset(href="some/path.tif", media_type=pystac.MediaType.GEOTIFF)
        eo_item.ext.eo.set_asset_bands(asset, [b.name for b in eo_item.ext.eo.bands])
        eo_item.add_asset("test", asset)

        self.assertEqual(eo_item.assets["test"].properties["eo:bands"],
                         list(range(0, len(eo_item.ext.eo.bands))))

    def test_read_pre_09_fields_into_common_metadata(self):
        eo_item = pystac.read_file(
            TestCases.get_path('data-files/examples/0.8.1/item-spec/examples/'
                               'landsat8-sample.json'))

        self.assertEqual(eo_item.common_metadata.platform, "landsat-8")
        self.assertEqual(eo_item.common_metadata.instruments, ["oli_tirs"])
