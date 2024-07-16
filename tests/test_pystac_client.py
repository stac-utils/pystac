import pytest

pytest.importorskip("pystac_client")


def test_import_pystac_client() -> None:
    from pystac.client import Client

    assert Client.__doc__
