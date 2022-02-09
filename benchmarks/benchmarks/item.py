import json
import os
import shutil
import tempfile
from timeit import repeat
import uuid

import pystac

from ._util import get_data_path

class ItemBench:
    repeat = 10

    def setup(self) -> None:
        self.temp_dir = tempfile.mkdtemp()

        self.stac_io = pystac.StacIO.default()

        self.item_path = get_data_path("item/sample-item-asset-properties.json")
        with open(self.item_path) as src:
            self.item_dict = json.load(src)
        self.item = pystac.Item.from_file(self.item_path)

    def teardown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def time_from_file(self) -> None:
        """Deserialize an Item from file"""
        _ = pystac.Item.from_file(self.item_path)
    
    def time_from_dict(self) -> None:
        """Deserialize an Item from dictionary."""
        _ = pystac.Item.from_dict(self.item_dict)

    def time_to_dict(self) -> None:
        """Serialize an Item to a dictionary."""
        self.item.to_dict(include_self_link=True)

    def time_save_item(self) -> None:
        """Serialize an Item to a JSON file."""
        self.item.save_object(
            include_self_link=True,
            dest_href=os.path.join(self.temp_dir, f"time_save_item.json"),
            stac_io=self.stac_io
        )