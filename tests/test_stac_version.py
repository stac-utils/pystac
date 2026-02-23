import os
from collections.abc import Generator
from unittest.mock import patch

import pystac
import pytest

from tests.utils import TestCases


def test_override_stac_version_with_environ() -> None:
    override_version = "1.0.0-gamma.2"
    with patch.dict(os.environ, {"PYSTAC_STAC_VERSION_OVERRIDE": override_version}):
        cat = TestCases.case_1()
        d = cat.to_dict()
    assert d["stac_version"] == override_version


@pytest.fixture
def override_pystac_version() -> Generator[str]:
    stac_version = pystac.get_stac_version()
    override_version = "1.0.0-delta.2"
    pystac.set_stac_version(override_version)
    yield override_version
    pystac.set_stac_version(stac_version)


def test_override_stac_version_with_call(override_pystac_version: str) -> None:
    cat = TestCases.case_1()
    d = cat.to_dict()
    assert d["stac_version"] == override_pystac_version
