from pathlib import Path

from pystac import Item


def test_default_schema_url() -> None:
    item = Item("an-id")
    item.ext.proj.add()
    assert item.stac_extensions
    assert (
        "https://stac-extensions.github.io/projection/v2.0.0/schema.json"
        in item.stac_extensions
    )


def test_code() -> None:
    item = Item("an-id")
    item.ext.proj.add()
    item.ext.proj.code = "EPSG:4326"
    d = item.to_dict()
    assert d["properties"]["proj:code"] == "EPSG:4326"


def test_has(examples_path: Path) -> None:
    item = Item.from_file(examples_path / "extended-item.json")
    assert item.ext.proj.exists()


def test_remove(examples_path: Path) -> None:
    item = Item.from_file(examples_path / "extended-item.json")
    item.ext.proj.remove()
    assert not item.ext.proj.exists()


def test_v1(data_files_path: Path) -> None:
    item = Item.from_file(data_files_path / "examples" / "1.0.0" / "extended-item.json")
    assert item.ext.proj.version == "1.0.0"
    assert item.ext.proj.epsg == 32659


def test_remove_fields() -> None:
    item = Item("an-id")
    item.ext.proj.add()
    item.ext.proj.code = "EPSG:4326"
    item.ext.proj.remove()
    d = item.to_dict()
    assert "proj:code" not in d["properties"]
