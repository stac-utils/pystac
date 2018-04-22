from pystac.models.base import STACObject
from marshmallow import (
    Schema,
    fields
)


class Properties(STACObject):
    def __init__(self, start, end,
                 provider, asset_license,
                 eo_properties):
        """Container for storing required and optional properties

        Args:
            start (datetime):
            end (datetime):
            provider (str):
            asset_license (str):
            eo_properties (dict):
        """
        self.eo_properties = eo_properties
        self.license = asset_license
        self.provider = provider
        self.end = end
        self.start = start

    @property
    def dict(self):
        base_properties = dict(
            license=self.license,
            provider=self.provider,
            end=self.end,
            start=self.start
        )
        if self.eo_properties:
            base_properties.update(self.eo_properties)
        return base_properties
    
    @property
    def json(self):
        return PropertiesSchema().dumps(
            self
        )


class PropertiesSchema(Schema):

    license = fields.Str()
    provider = fields.Str()
    eo_properties = fields.Dict()
    end = fields.DateTime()
    start = fields.DateTime()
