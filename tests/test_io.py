from pathlib import Path

from utils.mock_io import MockReader

import pystac


def test_read_file_propagates_reader(examples_path: Path) -> None:
    reader = MockReader()

    catalog = pystac.read_file(examples_path / "catalog.json", reader=reader)
    _ = list(catalog.get_items(recursive=True))

    # At least one linked object should be read via the same reader.
    assert len(reader.calls) > 1
