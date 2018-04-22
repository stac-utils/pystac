from pystac.models.band import BandSchema
from pystac.models.base import STACObject
from marshmallow import (
    Schema,
    fields
)


class Product(STACObject):
    def __init__(self, product_id, bands, filetype, origin, **kwargs):
        """Product specification for items/assets in STAC

        Args:
            product_id (str): ID of product, should be unique across products
            bands (List[band]): list of bands for product
            filetype (str): type of product
            origin (str): origin of product
        """
        self.product_id = product_id
        self.bands = bands
        self.filetype = filetype
        self.origin = origin
        self.other_properties = kwargs

    @property
    def dict(self):
        product = dict(
            id=self.product_id,
            bands=[b.dict for b in self.bands],
            filetype=self.filetype,
            origin=self.origin,
        )
        product.update(self.other_properties)
        return product

    @property
    def json(self):
        return ProductSchema().dumps(
            self
        )


class ProductSchema(Schema):

    product_id = fields.Str()
    bands = fields.Nested(BandSchema, many=True)
    filetype = fields.Str()
    origin = fields.Str()
    other_properties = fields.Dict()