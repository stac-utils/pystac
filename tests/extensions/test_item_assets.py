import unittest

from pystac import Collection
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension

from tests.utils import TestCases


class TestItemAssetsExtension(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.collection = Collection.from_file(
            TestCases.get_path("data-files/item-assets/example-landsat8.json")
        )

    def test_example(self) -> None:
        collection = self.collection.clone()
        item_ext = ItemAssetsExtension.ext(collection)

        self.assertEqual(len(item_ext.item_assets), 13)

        self.assertEqual(
            item_ext.item_assets["B1"],
            AssetDefinition(
                {
                    "type": "image/tiff; application=geotiff",
                    "eo:bands": [
                        {
                            "name": "B1",
                            "common_name": "coastal",
                            "center_wavelength": 0.44,
                            "full_width_half_max": 0.02,
                        }
                    ],
                    "title": "Coastal Band (B1)",
                    "description": "Coastal Band Top Of the Atmosphere",
                }
            ),
        )


class TestAssetDefinition(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.collection = Collection.from_file(
            TestCases.get_path("data-files/item-assets/example-landsat8.json")
        )

    def test_title(self) -> None:
        asset_defn = AssetDefinition({})
        title = "Very Important Asset"

        asset_defn.title = title

        self.assertEqual(asset_defn.title, title)
        self.assertEqual(asset_defn.to_dict()["title"], title)

    def test_description(self) -> None:
        asset_defn = AssetDefinition({})
        description = "What an incredibly important asset this is!"

        asset_defn.description = description

        self.assertEqual(asset_defn.description, description)
        self.assertEqual(asset_defn.to_dict()["description"], description)

    def test_media_type(self) -> None:
        asset_defn = AssetDefinition({})
        media_type = "application/json"

        asset_defn.media_type = media_type

        self.assertEqual(asset_defn.media_type, media_type)
        self.assertEqual(asset_defn.to_dict()["type"], media_type)

    def test_roles(self) -> None:
        asset_defn = AssetDefinition({})
        roles = ["thumbnail"]

        asset_defn.roles = roles

        self.assertEqual(asset_defn.roles, roles)
        self.assertEqual(asset_defn.to_dict()["roles"], roles)
