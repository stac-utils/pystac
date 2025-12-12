import os
from pathlib import Path

import pytest

import pystac


@pytest.mark.parametrize("action", ["copy", "move"])
def test_alter_asset_absolute_path(
    action: str, tmp_asset: pystac.Asset, tmp_path: Path
) -> None:
    asset = tmp_asset
    old_href = asset.get_absolute_href()
    assert old_href is not None

    new_href = str(tmp_path / "data.geojson")
    getattr(asset, action)(new_href)

    assert asset.href == new_href
    assert asset.get_absolute_href() == new_href
    assert os.path.exists(new_href)
    if action == "move":
        assert not os.path.exists(old_href)
    elif action == "copy":
        assert os.path.exists(old_href)


@pytest.mark.parametrize("action", ["copy", "move"])
def test_alter_asset_relative_path(action: str, tmp_asset: pystac.Asset) -> None:
    asset = tmp_asset
    old_href = asset.get_absolute_href()
    assert old_href is not None

    new_href = "./different.geojson"
    getattr(asset, action)(new_href)

    assert asset.href == new_href
    href = asset.get_absolute_href()
    assert href is not None
    assert os.path.exists(href)
    if action == "move":
        assert not os.path.exists(old_href)
    elif action == "copy":
        assert os.path.exists(old_href)


@pytest.mark.parametrize("action", ["copy", "move"])
def test_alter_asset_relative_src_no_owner_fails(
    action: str, tmp_asset: pystac.Asset
) -> None:
    asset = tmp_asset
    asset.owner = None
    new_href = "./different.geojson"
    with pytest.raises(ValueError, match=f"Cannot {action} file") as e:
        getattr(asset, action)(new_href)

    assert new_href not in str(e.value)
    assert asset.href != new_href


@pytest.mark.parametrize("action", ["copy", "move"])
def test_alter_asset_relative_dst_no_owner_fails(
    action: str, tmp_asset: pystac.Asset
) -> None:
    asset = tmp_asset
    item = asset.owner

    assert isinstance(item, pystac.Item)
    item.make_asset_hrefs_absolute()

    asset.owner = None
    new_href = "./different.geojson"
    with pytest.raises(ValueError, match=f"Cannot {action} file") as e:
        getattr(asset, action)(new_href)

    assert new_href in str(e.value)
    assert asset.href != new_href


def test_delete_asset(tmp_asset: pystac.Asset) -> None:
    asset = tmp_asset
    href = asset.get_absolute_href()
    assert href is not None
    assert os.path.exists(href)

    asset.delete()

    assert not os.path.exists(href)


def test_delete_asset_relative_no_owner_fails(tmp_asset: pystac.Asset) -> None:
    asset = tmp_asset
    href = asset.get_absolute_href()
    assert href is not None
    assert os.path.exists(href)

    asset.owner = None

    with pytest.raises(ValueError, match="Cannot delete file") as e:
        asset.delete()

    assert asset.href in str(e.value)
    assert os.path.exists(href)


@pytest.mark.parametrize(
    "self_href, asset_href, expected_href_nix, expected_href_win",
    (
        ("/local/myitem.json", "asset.data", "/local/asset.data", "/local/asset.data"),
        (
            "/local/myitem.json",
            "/absolute/asset.data",
            "/absolute/asset.data",
            "/absolute/asset.data",
        ),
        (
            "c:\\local\\myitem.json",
            "asset.data",
            os.path.join(os.getcwd(), "c:/local/asset.data"),
            "c:/local/asset.data",
        ),
        (
            "c:\\local\\myitem.json",
            "d:\\asset.data",
            os.path.join(os.getcwd(), "c:/local/d:/asset.data"),
            "d:\\asset.data",
        ),
        (
            "http://test.com/stac/catalog/myitem.json",
            "asset.data",
            "http://test.com/stac/catalog/asset.data",
            "http://test.com/stac/catalog/asset.data",
        ),
        (
            "http://test.com/stac/catalog/myitem.json",
            "/asset.data",
            "http://test.com/asset.data",
            "http://test.com/asset.data",
        ),
    ),
)
def test_asset_get_absolute_href(
    tmp_asset: pystac.Asset,
    self_href: str,
    asset_href: str,
    expected_href_nix: str,
    expected_href_win: str,
) -> None:
    asset = tmp_asset
    item = asset.owner

    if not isinstance(item, pystac.Item):
        raise TypeError("Asset must belong to an Item")

    item.set_self_href(self_href)

    asset.href = asset_href
    if os.name == "nt":
        assert asset.get_absolute_href() == expected_href_win
    else:
        assert asset.get_absolute_href() == expected_href_nix
