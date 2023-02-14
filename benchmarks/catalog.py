import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from pystac import (
    Catalog,
    Collection,
    Extent,
    Item,
    SpatialExtent,
    StacIO,
    TemporalExtent,
)

from ._base import Bench
from ._util import get_data_path


class CatalogBench(Bench):
    def setup(self) -> None:
        self.temp_dir = tempfile.mkdtemp()

        self.stac_io = StacIO.default()

        self.catalog_path = get_data_path("examples/1.0.0/catalog.json")
        with open(self.catalog_path) as src:
            self.catalog_dict = json.load(src)
        self.catalog = Catalog.from_file(self.catalog_path)

    def teardown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def time_catalog_from_file(self) -> None:
        """Deserialize an Item from file"""
        _ = Catalog.from_file(self.catalog_path)

    def time_catalog_from_dict(self) -> None:
        """Deserialize an Item from dictionary."""
        _ = Catalog.from_dict(self.catalog_dict)

    def time_catalog_to_dict(self) -> None:
        """Serialize an Item to a dictionary."""
        self.catalog.to_dict(include_self_link=True)

    def time_catalog_save(self) -> None:
        """Serialize an Item to a JSON file."""
        self.catalog.save_object(
            include_self_link=True,
            dest_href=os.path.join(self.temp_dir, "time_catalog_save.json"),
            stac_io=self.stac_io,
        )


class WalkCatalogBench(Bench):
    def setup_cache(self) -> Catalog:
        return make_large_catalog()

    def time_walk(self, catalog: Catalog) -> None:
        for (
            _,
            _,
            _,
        ) in catalog.walk():
            pass

    def peakmem_walk(self, catalog: Catalog) -> None:
        for (
            _,
            _,
            _,
        ) in catalog.walk():
            pass


class ReadCatalogBench(Bench):
    def setup(self) -> None:
        catalog = make_large_catalog()
        self.temporary_directory = TemporaryDirectory()
        self.path = str(Path(self.temporary_directory.name) / "catalog.json")
        catalog.normalize_and_save(self.temporary_directory.name)

    def teardown(self) -> None:
        shutil.rmtree(self.temporary_directory.name)

    def time_read_and_walk(self) -> None:
        catalog = Catalog.from_file(self.path)
        for _, _, _ in catalog.walk():
            pass


class WriteCatalogBench(Bench):
    def setup(self) -> None:
        self.catalog = make_large_catalog()
        self.temporary_directory = TemporaryDirectory()

    def teardown(self) -> None:
        shutil.rmtree(self.temporary_directory.name)

    def time_normalize_and_save(self) -> None:
        self.catalog.normalize_and_save(self.temporary_directory.name)


def make_large_catalog() -> Catalog:
    catalog = Catalog("an-id", "a description")
    extent = Extent(
        SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
        TemporalExtent([[datetime(2023, 1, 1), None]]),
    )
    for i in range(0, 10):
        collection = Collection(f"collection-{i}", f"Collection {i}", extent)
        for j in range(0, 100):
            item = Item(f"item-{i}-{j}", None, None, datetime.now(), {})
            collection.add_item(item)
        catalog.add_child(collection)
    return catalog
