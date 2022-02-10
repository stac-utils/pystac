import json
import os
import shutil
import tempfile
import pystac

from ._base import Bench
from ._util import get_data_path


class CollectionBench(Bench):

    def setup(self) -> None:
        self.temp_dir = tempfile.mkdtemp()

        self.stac_io = pystac.StacIO.default()

        self.collection_path = get_data_path("examples/1.0.0/collection.json")
        with open(self.collection_path) as src:
            self.collection_dict = json.load(src)
        self.collection = pystac.Collection.from_file(self.collection_path)

    def teardown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def time_collection_from_file(self) -> None:
        """Deserialize an Item from file"""
        _ = pystac.Collection.from_file(self.collection_path)

    def time_collection_from_dict(self) -> None:
        """Deserialize an Item from dictionary."""
        _ = pystac.Collection.from_dict(self.collection_dict)

    def time_collection_to_dict(self) -> None:
        """Serialize an Item to a dictionary."""
        self.collection.to_dict(include_self_link=True)

    def time_collection_save(self) -> None:
        """Serialize an Item to a JSON file."""
        self.collection.save_object(
            include_self_link=True,
            dest_href=os.path.join(self.temp_dir, f"time_collection_save.json"),
            stac_io=self.stac_io,
        )
