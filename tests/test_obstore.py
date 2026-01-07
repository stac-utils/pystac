from pathlib import Path

import pytest
from pytest import Subtests

import pystac

obstore = pytest.importorskip("obstore")


def test_examples_read_file(examples_path: Path, subtests: Subtests) -> None:
    from pystac.obstore import ObstoreReader

    store = obstore.store.LocalStore()
    reader = ObstoreReader(store)

    for path in examples_path.glob("**/*.json"):
        with subtests.test(path=path):
            stac_object = pystac.read_file(path, reader=reader)
            stac_object.validate()
