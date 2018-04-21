from pystac.models.base import STACObject
from marshmallow import (
    Schema,
    fields
)


class Link(STACObject):
    def __init__(self, link_type, href):
        """Link to related objects, must have a type and href

        Args:
            link_type (str): only two types (self and thumbnail)
            href (str): location
        """
        self.link_type = link_type
        self.href = href

    @property
    def dict(self):
        return dict(
            type=self.link_type,
            href=self.href
        )

    @property
    def json(self):
        return LinkSchema().dumps(
            self
        )


class LinkSchema(Schema):

    link_type = fields.Str()
    href = fields.Str() #  TBD with fields.URL()