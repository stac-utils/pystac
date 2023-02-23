import json
import os
import shutil
import tempfile

from pystac import Item, StacIO

from ._base import Bench
from ._util import get_data_path


class ItemBench(Bench):
    def setup(self) -> None:
        self.temp_dir = tempfile.mkdtemp()

        self.stac_io = StacIO.default()

        # using an item with many assets to better test deserialization timing
        self.item_path = get_data_path("eo/eo-sentinel2-item.json")
        with open(self.item_path) as src:
            self.item_dict = json.load(src)
        self.item = Item.from_file(self.item_path)

    def teardown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def time_item_from_file(self) -> None:
        """Deserialize an Item from file"""
        _ = Item.from_file(self.item_path)

    def time_item_from_dict(self) -> None:
        """Deserialize an Item from dictionary."""
        _ = Item.from_dict(self.item_dict)

    def time_item_to_dict(self) -> None:
        """Serialize an Item to a dictionary."""
        self.item.to_dict(include_self_link=True)

    def time_item_save(self) -> None:
        """Serialize an Item to a JSON file."""
        self.item.save_object(
            include_self_link=True,
            dest_href=os.path.join(self.temp_dir, "time_item_save.json"),
            stac_io=self.stac_io,
        )
