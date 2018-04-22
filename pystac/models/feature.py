import geojson
from geojson import Polygon

from pystac.models.asset import AssetSchema
from pystac.models.base import STACObject
from pystac.models.link import LinkSchema
from pystac.models.properties import PropertiesSchema
from marshmallow import (
    Schema,
    fields
)


class Feature(STACObject):
    def __init__(self, item_id,
                 geometry, properties,
                 links, assets):
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
    def dict(self):
        return dict(
            type='Feature',
            id=self.id,
            properties=self.properties.dict,
            geometry=self.geometry,
            bbox=self.bbox,
            links=[link.dict for link in self.links],
            assets=[asset.dict for asset in self.assets]
        )
    
    @property
    def json(self):
        return FeatureSchema().dumps(
            self
        )


class FeatureSchema(Schema):

    links = fields.Nested(LinkSchema, many=True)
    properties = fields.Nested(PropertiesSchema)
    geometry = fields.Dict()
    id = fields.Str()
    assets = fields.Nested(AssetSchema, many=True)