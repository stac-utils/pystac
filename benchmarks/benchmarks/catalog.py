import json
import os
import shutil
import tempfile
import pystac

from ._base import Bench
from ._util import get_data_path


class CatalogBench(Bench):

    def setup(self) -> None:
        self.temp_dir = tempfile.mkdtemp()

        self.stac_io = pystac.StacIO.default()

        self.catalog_path = get_data_path("examples/1.0.0/catalog.json")
        with open(self.catalog_path) as src:
            self.catalog_dict = json.load(src)
        self.catalog = pystac.Catalog.from_file(self.catalog_path)

    def teardown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def time_catalog_from_file(self) -> None:
        """Deserialize an Item from file"""
        _ = pystac.Catalog.from_file(self.catalog_path)

    def time_catalog_from_dict(self) -> None:
        """Deserialize an Item from dictionary."""
        _ = pystac.Catalog.from_dict(self.catalog_dict)

    def time_catalog_to_dict(self) -> None:
        """Serialize an Item to a dictionary."""
        self.catalog.to_dict(include_self_link=True)

    def time_catalog_save(self) -> None:
        """Serialize an Item to a JSON file."""
        self.catalog.save_object(
            include_self_link=True,
            dest_href=os.path.join(self.temp_dir, f"time_catalog_save.json"),
            stac_io=self.stac_io,
        )
