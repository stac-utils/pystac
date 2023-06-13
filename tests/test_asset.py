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
