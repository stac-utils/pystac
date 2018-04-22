from marshmallow import (
    Schema,
    fields
)


class STACObject(object):

    def __init__(self, stac):
        self.stac = stac

    @property
    def dict(self):
        return self.stac

    @property
    def json(self):
        return STACObjectSchema().dumps(
            self
        )


class STACObjectSchema(Schema):

    stac = fields.Dict()
