import unittest

import pytest

from pystac import Collection
from pystac.errors import DeprecatedWarning
from pystac.extensions.item_assets import ItemAssetsExtension
from pystac.item_assets import ItemAssetDefinition
from tests.utils import TestCases

CLASSIFICATION_COLLECTION_RASTER_URI = TestCases.get_path(
    "data-files/classification/collection-item-assets-raster-bands.json"
)


class TestItemAssets(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.collection = Collection.from_file(
            TestCases.get_path("data-files/item-assets/example-landsat8.json")
        )

    def test_example(self) -> None:
        collection = self.collection.clone()

        assert collection.item_assets
        self.assertEqual(len(collection.item_assets), 13)

        self.assertEqual(
            collection.item_assets["B1"],
            ItemAssetDefinition(
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

    def test_set_using_dict(self) -> None:
        collection = self.collection.clone()

        assert collection.item_assets
        self.assertEqual(len(collection.item_assets), 13)

        collection.item_assets["Bx"] = {
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
        }  # type:ignore

        self.assertEqual(collection.item_assets["B1"], collection.item_assets["Bx"])


class TestAssetDefinition(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.collection = Collection.from_file(
            TestCases.get_path("data-files/item-assets/example-landsat8.json")
        )

    def test_create(self) -> None:
        title = "Coastal Band (B1)"
        description = "Coastal Band Top Of the Atmosphere"
        media_type = "image/tiff; application=geotiff"
        roles = ["data"]
        asset_defn = ItemAssetDefinition.create(
            title=title, description=description, media_type=media_type, roles=roles
        )
        self.assertEqual(asset_defn.title, title)
        self.assertEqual(asset_defn.description, description)
        self.assertEqual(asset_defn.media_type, media_type)
        self.assertEqual(asset_defn.roles, roles)

    def test_title(self) -> None:
        asset_defn = ItemAssetDefinition({})
        title = "Very Important Asset"

        asset_defn.title = title

        self.assertEqual(asset_defn.title, title)
        self.assertEqual(asset_defn.to_dict()["title"], title)

    def test_description(self) -> None:
        asset_defn = ItemAssetDefinition({})
        description = "What an incredibly important asset this is!"

        asset_defn.description = description

        self.assertEqual(asset_defn.description, description)
        self.assertEqual(asset_defn.to_dict()["description"], description)

    def test_media_type(self) -> None:
        asset_defn = ItemAssetDefinition({})
        media_type = "application/json"

        asset_defn.media_type = media_type

        self.assertEqual(asset_defn.media_type, media_type)
        self.assertEqual(asset_defn.to_dict()["type"], media_type)

    def test_roles(self) -> None:
        asset_defn = ItemAssetDefinition({})
        roles = ["thumbnail"]

        asset_defn.roles = roles

        self.assertEqual(asset_defn.roles, roles)
        self.assertEqual(asset_defn.to_dict()["roles"], roles)


def test_extra_fields(collection: Collection) -> None:
    asset_definition = ItemAssetDefinition.create(
        title=None,
        description=None,
        media_type=None,
        roles=None,
        extra_fields={"raster:bands": [{"nodata": 42}]},
    )
    collection.item_assets = {"data": asset_definition}
    collection_as_dict = collection.to_dict()
    assert collection_as_dict["item_assets"]["data"]["raster:bands"] == [{"nodata": 42}]
    asset = asset_definition.create_asset("asset.tif")
    assert asset.extra_fields["raster:bands"] == [{"nodata": 42}]

    collection.item_assets["data"].ext.add("raster")
    assert (bands := collection.item_assets["data"].ext.raster.bands)
    assert bands[0].nodata == 42

    assert collection.item_assets["data"].ext.has("raster")
    assert collection.ext.has("raster")


def test_item_assets_extension_is_deprecated() -> None:
    collection = Collection.from_file(CLASSIFICATION_COLLECTION_RASTER_URI)

    assert ItemAssetsExtension.get_schema_uri() not in collection.stac_extensions

    with pytest.warns(DeprecatedWarning, match="top-level property of"):
        item_asset = ItemAssetsExtension.ext(
            collection, add_if_missing=True
        ).item_assets["cloud-mask-raster"]

    assert item_asset.ext.has("eo")

    with pytest.warns(DeprecatedWarning, match="top-level property of"):
        assert collection.ext.item_assets["cloud-mask-raster"].ext.has("eo")

    assert ItemAssetsExtension.get_schema_uri() in collection.stac_extensions
