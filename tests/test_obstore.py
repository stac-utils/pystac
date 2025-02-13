from pathlib import Path

import pytest

import pystac

pytest.importorskip("obstore")

from pystac.obstore import ObstoreReader


def test_read_local(examples_path: Path) -> None:
    reader = ObstoreReader()
    _ = pystac.read_file(examples_path / "simple-item.json", reader=reader)
    _ = pystac.read_file(str(examples_path / "simple-item.json"), reader=reader)
    _ = pystac.read_file(
        "file://" + str(examples_path / "simple-item.json"), reader=reader
    )
