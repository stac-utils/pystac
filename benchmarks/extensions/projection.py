from datetime import datetime

from pystac import Item
from pystac.extensions.projection import ProjectionExtension

from .._base import Bench


class ProjectionBench(Bench):
    def setup(self) -> None:
        self.item = Item("an-id", None, None, datetime.now(), {})

    def time_add_projection_extension(self) -> None:
        _ = ProjectionExtension.ext(self.item, add_if_missing=True)
