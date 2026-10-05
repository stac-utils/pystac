import os
from copy import deepcopy
from pathlib import Path

import pytest

import pystac


def test_copied_asset_is_independent_of_its_owner(item: pystac.Item) -> None:
    """Modifying an asset from ``get_assets`` does not touch the owning item."""
    item.add_asset(
        "data",
        pystac.Asset("data.tif", roles=["data"], extra_fields={"nested": {"k": [1]}}),
    )

    copied = item.get_assets()["data"]
    assert copied.roles is not None
    copied.href = "other.tif"
    copied.roles.append("overview")
    copied.extra_fields["nested"]["k"].append(2)

    assert item.assets["data"].href == "data.tif"
    assert item.assets["data"].roles == ["data"]
    assert item.assets["data"].extra_fields["nested"]["k"] == [1]
    assert copied.owner is item


def test_deepcopy_of_an_item_reattaches_its_assets(item: pystac.Item) -> None:
    """The assets of a copied item belong to the copy, not to the original."""
    item.add_asset("data", pystac.Asset("data.tif"))

    copied = deepcopy(item)
    copied.assets["data"].href = "other.tif"

    assert copied.assets["data"].owner is copied
    assert item.assets["data"].href == "data.tif"


def test_deepcopy_of_an_asset_keeps_its_owner(asset: pystac.Asset) -> None:
    """An asset copied on its own still points at the object it came from."""
    assert deepcopy(asset).owner is asset.owner


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
    "self_href, asset_href, expected_href",
    (
        (
            "http://test.com/stac/catalog/myitem.json",
            "asset.data",
            "http://test.com/stac/catalog/asset.data",
        ),
        (
            "http://test.com/stac/catalog/myitem.json",
            "/asset.data",
            "http://test.com/asset.data",
        ),
    ),
)
def test_asset_get_absolute_href(
    tmp_asset: pystac.Asset,
    self_href: str,
    asset_href: str,
    expected_href: str,
) -> None:
    asset = tmp_asset
    item = asset.owner

    if not isinstance(item, pystac.Item):
        raise TypeError("Asset must belong to an Item")

    # Set the item HREF as per test
    item.set_self_href(self_href)
    assert item.get_self_href() == self_href

    # Set the asset HREF as per test and check expected output
    asset.href = asset_href
    assert asset.get_absolute_href() == expected_href


@pytest.mark.skipif(os.name == "nt", reason="Unix only test")
@pytest.mark.parametrize(
    "self_href, asset_href, expected_href",
    (
        (
            "/local/myitem.json",
            "asset.data",
            "/local/asset.data",
        ),
        (
            "/local/myitem.json",
            "subdir/asset.data",
            "/local/subdir/asset.data",
        ),
        (
            "/local/myitem.json",
            "/absolute/asset.data",
            "/absolute/asset.data",
        ),
    ),
)
def test_asset_get_absolute_href_unix(
    tmp_asset: pystac.Asset,
    self_href: str,
    asset_href: str,
    expected_href: str,
) -> None:
    test_asset_get_absolute_href(tmp_asset, self_href, asset_href, expected_href)


@pytest.mark.skipif(os.name != "nt", reason="Windows only test")
@pytest.mark.parametrize(
    "self_href, asset_href, expected_href",
    (
        (
            "{tmpdir}/myitem.json",
            "asset.data",
            "{tmpdir}/asset.data",
        ),
        (
            "{tmpdir}/myitem.json",
            "subdir/asset.data",
            "{tmpdir}/subdir/asset.data",
        ),
        (
            "{tmpdir}/myitem.json",
            "c:/absolute/asset.data",
            "c:/absolute/asset.data",
        ),
        (
            "{tmpdir}/myitem.json",
            "d:\\absolute\\asset.data",
            "d:\\absolute\\asset.data",
        ),
    ),
)
def test_asset_get_absolute_href_windows(
    tmp_path: Path,
    tmp_asset: pystac.Asset,
    self_href: str,
    asset_href: str,
    expected_href: str,
) -> None:
    # For windows, we need an actual existing temporary directory
    tmpdir = tmp_path.as_posix()
    test_asset_get_absolute_href(
        tmp_asset,
        self_href.format(tmpdir=tmpdir),
        asset_href.format(tmpdir=tmpdir),
        expected_href.format(tmpdir=tmpdir),
    )
