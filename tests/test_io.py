from pathlib import Path

import pystac


def test_read_file_propagates_reader(examples_path: Path, mock_reader) -> None:
    reader = mock_reader

    catalog: pystac.Catalog = pystac.read_file(
        examples_path / "catalog.json", reader=reader
    )
    items = list(catalog.get_items(recursive=True))

    # At least one linked object should be read via the same reader.
    assert len(reader.calls) > 1
    assert items[0].reader is reader


def test_default_reader_writer_getters(
    examples_path: Path, mock_reader, mock_writer
) -> None:
    assert pystac.get_default_reader() is mock_reader
    assert pystac.get_default_writer() is mock_writer

    catalog_path = examples_path / "catalog.json"
    catalog = pystac.read_file(catalog_path)
    assert isinstance(catalog, pystac.Catalog)
    assert mock_reader.calls == [str(catalog_path)]

    new_catalog = pystac.Catalog("new-catalog", "new description")
    assert new_catalog.reader is mock_reader
    assert new_catalog.writer is mock_writer
