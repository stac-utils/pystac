from pathlib import Path

import pytest

from pystac import Collection
from pystac.asset import ItemAsset


@pytest.fixture
def landsat8_collection(data_files_path: Path) -> Collection:
    return Collection.from_file(
        data_files_path / "collections" / "with-item-assets.json"
    )


def test_example(landsat8_collection: Collection) -> None:
    assert landsat8_collection.item_assets
    assert len(landsat8_collection.item_assets) == 13

    assert landsat8_collection.item_assets["B1"] == ItemAsset.from_dict(
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


class TestItemAsset:
    def test_eq(self, landsat8_collection: Collection) -> None:
        assert landsat8_collection.item_assets
        assert landsat8_collection.item_assets["B1"].to_dict() != {
            "title": "Coastal Band (B1)"
        }

    def test_create(self) -> None:
        title = "Coastal Band (B1)"
        description = "Coastal Band Top Of the Atmosphere"
        media_type = "image/tiff; application=geotiff"
        roles = ["data"]
        asset_defn = ItemAsset(
            title=title, description=description, type=media_type, roles=roles
        )
        assert (
            asset_defn.title,
            asset_defn.description,
            asset_defn.type,
            asset_defn.roles,
        ) == (title, description, media_type, roles)

    def test_title(self) -> None:
        asset_defn = ItemAsset()
        title = "Very Important Asset"

        asset_defn.title = title

        assert asset_defn.title == asset_defn.to_dict()["title"] == title

    def test_description(self) -> None:
        asset_defn = ItemAsset()
        description = "What an incredibly important asset this is!"

        asset_defn.description = description

        assert (
            asset_defn.description == asset_defn.to_dict()["description"] == description
        )

    def test_media_type(self) -> None:
        asset_defn = ItemAsset()
        media_type = "application/json"

        asset_defn.type = media_type

        assert asset_defn.type == asset_defn.to_dict()["type"] == media_type

    def test_roles(self) -> None:
        asset_defn = ItemAsset()
        roles = ["thumbnail"]

        asset_defn.roles = roles

        assert asset_defn.roles == asset_defn.to_dict()["roles"] == roles
