import pytest

import pystac
from pystac import DEFAULT_STAC_VERSION


def test_get_stac_version() -> None:
    with pytest.warns(FutureWarning):
        assert pystac.get_stac_version() == DEFAULT_STAC_VERSION


def test_set_stac_version() -> None:
    with pytest.warns(FutureWarning):
        pystac.set_stac_version("1.0.0")
