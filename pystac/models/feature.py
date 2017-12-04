from typing import List

import geojson
from geojson import Polygon

from pystac.models.asset import Asset
from pystac.models.base import STACObject
from pystac.models.link import Link
from pystac.models.properties import Properties


class Feature(STACObject):
    def __init__(self, item_id: str,
                 geometry: Polygon, properties: Properties,
                 links: List[Link], assets: List[Asset]):
        """STAC Catalog item

        Args:
            item_id (str):
            geometry (Polygon):
            properties (Properties):
            links (List[Link]):
            assets (List[Asset]):
        """
        self.links = links
        self.properties = properties
        self.geometry = geometry
        self.id = item_id
        self.assets = assets

    @property
    def bbox(self):
        lats, lngs = zip(*geojson.utils.coords(self.geometry))
        return [min(lats), min(lngs), max(lats), max(lngs)]

    @property
    def dict(self) -> dict:
        return dict(
            type='Feature',
            id=self.id,
            properties=self.properties.dict,
            geometry=self.geometry,
            bbox=self.bbox,
            links=[link.dict for link in self.links],
            assets=[asset.dict for asset in self.assets]
        )


