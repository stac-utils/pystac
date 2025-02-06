import pytest

from pystac import Collection
from pystac.errors import DeprecatedWarning
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.item_assets import ItemAssetDefinition
from tests.utils import TestCases

CLASSIFICATION_COLLECTION_RASTER_URI = TestCases.get_path(
    "data-files/classification/collection-item-assets-raster-bands.json"
)


@pytest.fixture
def landsat8_collection() -> Collection:
    return Collection.from_file(
        TestCases.get_path("data-files/item-assets/example-landsat8.json")
    )


def test_example(landsat8_collection: Collection) -> None:
    assert len(landsat8_collection.item_assets) == 13

    assert landsat8_collection.item_assets["B1"] == ItemAssetDefinition(
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
    )


def test_set_using_dict(landsat8_collection: Collection) -> None:
    assert len(landsat8_collection.item_assets) == 13

    landsat8_collection.item_assets["Bx"] = {
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

    assert (
        landsat8_collection.item_assets["B1"] == landsat8_collection.item_assets["Bx"]
    )


class TestAssetDefinition:
    def test_eq(self, landsat8_collection: Collection) -> None:
        assert landsat8_collection.item_assets["B1"] != {"title": "Coastal Band (B1)"}

    def test_create(self) -> None:
        title = "Coastal Band (B1)"
        description = "Coastal Band Top Of the Atmosphere"
        media_type = "image/tiff; application=geotiff"
        roles = ["data"]
        asset_defn = ItemAssetDefinition.create(
            title=title, description=description, media_type=media_type, roles=roles
        )
        assert (
            asset_defn.title,
            asset_defn.description,
            asset_defn.media_type,
            asset_defn.roles,
        ) == (title, description, media_type, roles)

    def test_title(self) -> None:
        asset_defn = ItemAssetDefinition({})
        title = "Very Important Asset"

        asset_defn.title = title

        assert asset_defn.title == asset_defn.to_dict()["title"] == title

    def test_description(self) -> None:
        asset_defn = ItemAssetDefinition({})
        description = "What an incredibly important asset this is!"

        asset_defn.description = description

        assert (
            asset_defn.description == asset_defn.to_dict()["description"] == description
        )

    def test_media_type(self) -> None:
        asset_defn = ItemAssetDefinition({})
        media_type = "application/json"

        asset_defn.media_type = media_type

        assert asset_defn.media_type == asset_defn.to_dict()["type"] == media_type

    def test_roles(self) -> None:
        asset_defn = ItemAssetDefinition({})
        roles = ["thumbnail"]

        asset_defn.roles = roles

        assert asset_defn.roles == asset_defn.to_dict()["roles"] == roles

    def test_set_owner(self, landsat8_collection: Collection) -> None:
        asset_definition = ItemAssetDefinition(
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
        )
        asset_definition.set_owner(landsat8_collection)
        assert asset_definition.owner == landsat8_collection


def test_extra_fields(collection: Collection) -> None:
    asset_definition = ItemAssetDefinition.create(
        title=None,
        description=None,
        media_type=None,
        roles=None,
        extra_fields={"raster:bands": [{"nodata": 42}]},
    )

    collection.item_assets = {"data": asset_definition}
    assert collection.item_assets["data"].owner == collection

    collection_as_dict = collection.to_dict()
    assert collection_as_dict["item_assets"]["data"]["raster:bands"] == [{"nodata": 42}]
    asset = asset_definition.create_asset("asset.tif")
    assert asset.extra_fields["raster:bands"] == [{"nodata": 42}]

    collection.item_assets["data"].ext.add("raster")
    assert (bands := collection.item_assets["data"].ext.raster.bands)
    assert bands[0].nodata == 42

    assert collection.item_assets["data"].ext.has("raster")
    assert collection.ext.has("raster")


def test_set_item_asset(collection: Collection) -> None:
    asset_definition = ItemAssetDefinition.create(
        title=None,
        description=None,
        media_type=None,
        roles=None,
        extra_fields={"raster:bands": [{"nodata": 42}]},
    )

    collection.item_assets["data"] = asset_definition
    assert collection.item_assets["data"].owner == collection


def test_item_assets_extension_is_deprecated() -> None:
    collection = Collection.from_file(CLASSIFICATION_COLLECTION_RASTER_URI)

    assert ItemAssetsExtension.get_schema_uri() not in collection.stac_extensions

    with pytest.warns(DeprecatedWarning, match="top-level property of"):
        item_asset_ext = ItemAssetsExtension.ext(collection, add_if_missing=True)
        item_asset = item_asset_ext.item_assets["cloud-mask-raster"]

    assert collection.id in repr(item_asset_ext)

    assert item_asset.ext.has("eo")

    with pytest.warns(DeprecatedWarning, match="top-level property of"):
        assert collection.ext.item_assets["cloud-mask-raster"].ext.has("eo")

    assert ItemAssetsExtension.get_schema_uri() in collection.stac_extensions

    with pytest.warns(DeprecationWarning):
        asset_definition = AssetDefinition(
            {"title": "Thumbnail image", "type": "image/jpeg"}
        )
    item_asset_ext.item_assets["thumbnail"] = asset_definition


def test_item_assets_extension_asset_definition_is_deprecated() -> None:
    with pytest.warns(
        DeprecationWarning, match="Please use ``pystac.ItemAssetDefinition``"
    ):
        asset_definition = AssetDefinition(
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
        )

    assert asset_definition.title == "Coastal Band (B1)"
    assert asset_definition.ext.eo.bands
    assert asset_definition.ext.eo.bands[0].name == "B1"
    assert asset_definition.owner is None
