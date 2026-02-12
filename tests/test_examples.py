import json
from pathlib import Path

import pytest

import pystac
from pystac.reader import StandardLibraryReader

EXAMPLE_FILES = sorted(
    list(
        (Path(__file__).parent / "data-files" / "examples").glob("**/*.json"),
    )
)


@pytest.mark.vcr
@pytest.mark.parametrize("path", EXAMPLE_FILES)
def test_example_from_dict(path: Path):
    with open(path) as f:
        data = json.load(f)
    stac_object = pystac.from_dict(data)
    stac_object.validate()


@pytest.mark.vcr
@pytest.mark.parametrize("path", EXAMPLE_FILES)
def test_example_read_file(path: Path):
    stac_object = pystac.read_file(path, reader=StandardLibraryReader())
    stac_object.validate()
