import json
import os
import unittest
from jsonschema import ValidationError
from tempfile import TemporaryDirectory
from copy import deepcopy

from pystac import (Catalog, CatalogType, Item, Asset, STACError)
from pystac.eo import (Band, EOAsset, EOItem)
from tests.utils import (SchemaValidator, TestCases, test_to_from_dict)


class EOItemTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.URI_1 = TestCases.get_path(
            'data-files/eo/eo-landsat-example.json')
        self.URI_2 = TestCases.get_path(
            'data-files/eo/eo-landsat-example-INVALID.json')
        self.eoi = EOItem.from_file(self.URI_1)
        with open(self.URI_1) as f:
            self.eo_dict = json.load(f)

    def test_to_from_dict(self):
        test_to_from_dict(self, EOItem, self.eo_dict)

    def test_from_file(self):
        self.assertEqual(len(self.eoi.bands), 11)
        for b in self.eoi.bands:
            self.assertIsInstance(b, Band)
        self.assertEqual(len(self.eoi.links), 3)

        href = ('https://odu9mlf7d6.execute-api.us-east-1.amazonaws.com/stage/'
                'stac/search?id=LC08_L1TP_107018_20181001_20181001_01_RT')
        self.assertEqual(self.eoi.get_self_href(), href)

        with self.assertRaises(STACError):
            EOItem.from_file(self.URI_2)

    def test_from_item(self):
        i = Item.from_file(self.URI_1)
        with self.assertRaises(AttributeError):
            getattr(i, 'bands')
        self.assertTrue('eo:bands' in i.properties.keys())
        eoi = EOItem.from_item(i)
        self.assertIsNotNone(getattr(eoi, 'bands'))
        with self.assertRaises(KeyError):
            eoi.properties['eo:bands']

    def test_read_eo_item_owns_asset(self):
        item = EOItem.from_file(self.URI_1)
        assert len(item.assets) > 0
        for asset_key in item.assets:
            self.assertEqual(item.assets[asset_key].owner, item)

    def test_clone(self):
        eoi_clone = self.eoi.clone()
        compare_eo_items(self, self.eoi, eoi_clone)

    def test_get_assets(self):
        a = self.eoi.get_assets()
        for _, asset in a.items():
            self.assertIsInstance(asset, Asset)
        eoa = self.eoi.get_eo_assets()
        for _, eo_asset in eoa.items():
            self.assertIsInstance(eo_asset, EOAsset)
        self.assertNotEqual(len(a.items()), len(eoa.items()))
        for k in eoa.keys():
            self.assertIn(k, a.keys())

    def test_add_asset(self):
        eoi_c = deepcopy(self.eoi)
        a = Asset('/asset_dir/asset.json')
        eoa = EOAsset('/asset_dir/eo_asset.json', bands=[0, 1])
        for asset in (a, eoa):
            self.assertIsNone(asset.owner)
        eoi_c.add_asset('new_asset', a)
        eoi_c.add_asset('new_eo_asset', eoa)
        self.assertEqual(len(eoi_c.assets.items()),
                         len(self.eoi.assets.items()) + 2)
        self.assertEqual(a, eoi_c.assets['new_asset'])
        self.assertEqual(eoa, eoi_c.assets['new_eo_asset'])
        for asset in (a, eoa):
            self.assertEqual(asset.owner, eoi_c)

    def test_add_eo_fields_to_dict(self):
        d = {}
        self.eoi._add_eo_fields_to_dict(d)
        comp_d = {
            k: v
            for k, v in deepcopy(self.eo_dict['properties']).items()
            if k.startswith('eo:')
        }
        self.assertDictEqual(d, comp_d)

    def test_validate_eo(self):
        sv = SchemaValidator()
        self.assertIsNone(sv.validate_dict(self.eo_dict, EOItem))

        with open(self.URI_2) as f:
            eo_dict_2 = json.load(f)
        with self.assertRaises(ValidationError):
            print('[Validation error expected] - ', end='')
            sv.validate_dict(eo_dict_2, EOItem)

        with TemporaryDirectory() as tmp_dir:
            cat_dir = os.path.join(tmp_dir, 'catalog')
            catalog = TestCases.test_case_1()
            eo_item = EOItem.from_dict(self.eo_dict)
            catalog.add_item(eo_item)
            catalog.normalize_and_save(
                cat_dir, catalog_type=CatalogType.ABSOLUTE_PUBLISHED)

            cat_read = Catalog.from_file(os.path.join(cat_dir, 'catalog.json'))
            eo_item_read = cat_read.get_item(
                "LC08_L1TP_107018_20181001_20181001_01_RT")
            sv = SchemaValidator()
            sv.validate_object(eo_item_read)
            sv.validate_dict(eo_item_read.to_dict(), EOItem)


class EOAssetTest(unittest.TestCase):
    def setUp(self):
        self.EO_ITEM_URI = TestCases.get_path(
            'data-files/eo/eo-landsat-example.json')
        self.EO_ASSET_URI = TestCases.get_path('data-files/eo/eo-asset.json')
        self.ASSET_URI = TestCases.get_path('data-files/eo/asset.json')
        with open(self.EO_ASSET_URI) as f:
            self.EO_ASSET_DICT = json.load(f)
        with open(self.ASSET_URI) as f:
            self.ASSET_DICT = json.load(f)
        self.EO_ASSET_2_URI = TestCases.get_path(
            'data-files/eo/eo-asset-2.json')
        with open(self.EO_ASSET_2_URI) as f:
            self.EO_ASSET_2_DICT = json.load(f)

    def test_to_from_dict(self):
        test_to_from_dict(self, EOAsset, self.EO_ASSET_DICT)
        test_to_from_dict(self, EOAsset, self.EO_ASSET_2_DICT)

    def test_from_asset(self):
        a1 = Asset.from_dict(self.ASSET_DICT)
        with self.assertRaises(STACError):
            EOAsset.from_asset(a1)

        a2 = Asset.from_dict(self.EO_ASSET_DICT)
        eoa = EOAsset.from_asset(a2)
        self.assertIsNone(eoa.properties)
        self.assertListEqual(eoa.bands, [0])

    def test_clone(self):
        eoa = EOAsset.from_dict(self.EO_ASSET_DICT)
        eoa_clone = eoa.clone()
        compare_eo_assets(self, eoa, eoa_clone)

        eoa2 = EOAsset.from_dict(self.EO_ASSET_2_DICT)
        self.assertDictEqual(eoa2.properties, {"extra property": "extra"})

    def test_get_bands(self):
        eoi = EOItem.from_file(self.EO_ITEM_URI)
        eoa = EOAsset.from_dict(self.EO_ASSET_DICT)
        eoi.add_asset('test-asset', eoa)
        self.assertEqual(eoa.owner, eoi)
        bd = {
            "name": "B1",
            "common_name": "coastal",
            "gsd": 30,
            "center_wavelength": 0.44,
            "full_width_half_max": 0.02
        }
        b1 = Band.from_dict(bd)
        eoa_bands = eoa.get_bands()
        compare_bands(self, b1, eoa_bands[0])


class BandTest(unittest.TestCase):
    def setUp(self):
        self.EO_ITEM_URI = TestCases.get_path(
            'data-files/eo/eo-landsat-example.json')
        with open(self.EO_ITEM_URI) as f:
            self.EO_BANDS_LIST = json.load(f)['properties']['eo:bands']

    def test_constructor(self):
        self.assertIsInstance(Band(), Band)

    def test_to_from_dict(self):
        for b in self.EO_BANDS_LIST:
            test_to_from_dict(self, Band, b)


class EOUtilsTest(unittest.TestCase):
    def test_band_description(self):
        desc = 'Common name: nir, Range: 0.75 to 1.0'
        self.assertEqual(Band.band_description('nir'), desc)
        self.assertIsNone(Band.band_description('uncommon name'))

    def test_band_range(self):
        self.assertEqual(Band.band_range('pan'), (0.50, 0.70))
        self.assertIsNone(Band.band_range('uncommon name'))

    def test_eo_key(self):
        self.assertEqual(EOItem._eo_key(''), 'eo:')
        self.assertEqual(EOItem._eo_key('dsg'), 'eo:dsg')


def compare_eo_items(test_class, eoi_1, eoi_2):
    for eoi in (eoi_1, eoi_2):
        test_class.assertIsInstance(eoi, EOItem)
    test_class.assertEqual(dir(eoi_1), dir(eoi_2))
    test_class.assertEqual(eoi_1.id, eoi_2.id)
    test_class.assertListEqual(eoi_1.bbox, eoi_2.bbox)
    test_class.assertListEqual(eoi_1.stac_extensions, eoi_2.stac_extensions)
    for eoi in (eoi_1, eoi_2):
        eoi.links.sort(key=lambda x: x.target)
    for i in range(len(eoi_1.links)):
        test_class.assertDictEqual(eoi_1.links[i].to_dict(),
                                   eoi_2.links[i].to_dict())

    for d in ('geometry', 'properties'):
        test_class.assertDictEqual(getattr(eoi_1, d), getattr(eoi_2, d))

    test_class.assertEqual(len(eoi_1.assets.keys()), len(eoi_2.assets.keys()))
    for key in eoi_1.assets.keys():
        if isinstance(eoi_1.assets[key], EOAsset):
            compare_eo_assets(test_class, eoi_1.assets[key], eoi_2.assets[key])
        else:
            test_class.assertDictEqual(eoi_1.assets[key].to_dict(),
                                       eoi_2.assets[key].to_dict())

    for eof in EOItem._EO_FIELDS:
        if eof == 'bands':
            test_class.assertEqual(len(eoi_1.bands), len(eoi_2.bands))
            for eoi in (eoi_1, eoi_2):
                eoi.bands.sort(key=lambda x: x.name)
            for i in range(len(eoi_1.bands)):
                compare_bands(test_class, eoi_1.bands[i], eoi_2.bands[i])
        else:
            test_class.assertEqual(getattr(eoi_1, eof), getattr(eoi_2, eof))


def compare_eo_assets(test_class, eoa_1, eoa_2):
    for eoa in (eoa_1, eoa_2):
        test_class.assertIsInstance(eoa, EOAsset)
    test_class.assertEqual(eoa_1.href, eoa_2.href)
    test_class.assertListEqual(eoa_1.bands, eoa_2.bands)
    test_class.assertEqual(eoa_1.title, eoa_2.title)
    test_class.assertEqual(eoa_1.media_type, eoa_2.media_type)
    if eoa_1.properties:
        test_class.assertDictEqual(eoa_1.properties, eoa_2.properties)
    else:
        test_class.assertIsNone(eoa_2.properties)


def compare_bands(test_class, b1, b2):
    test_class.assertDictEqual(b1.to_dict(), b2.to_dict())
