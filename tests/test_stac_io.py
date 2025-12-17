import pytest


def test_import_warns() -> None:
    with pytest.warns(FutureWarning):
        from pystac import StacIO  # pyright: ignore[reportUnusedImport] # noqa
