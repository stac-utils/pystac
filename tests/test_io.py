from pathlib import Path

from pystac import Catalog


def test_same_reader(catalog: Catalog) -> None:
    for child in catalog.get_children():
        assert child.reader is catalog.reader


def test_same_writer(catalog: Catalog) -> None:
    for child in catalog.get_children():
        assert child.writer is catalog.writer


def test_walk_deep(tmp_path: Path) -> None:
    catalog = Catalog("root", "coot catalog")
    child = Catalog("child", "child catalog")
    grandchild = Catalog("grandchild", "grandchild catalog")
    catalog.add_child(child)
    child.add_child(grandchild)
    catalog.render(tmp_path / "walking")
    catalog.save()

    catalog = Catalog.from_file(tmp_path / "walking" / "catalog.json")
    for _, _, _ in catalog.walk():
        pass
