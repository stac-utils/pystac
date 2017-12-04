from pystac.models.base import STACObject


class Link(STACObject):
    def __init__(self, link_type: str, href: str):
        """Link to related objects, must have a type and href

        Args:
            link_type (str): only two types (self and thumbnail)
            href (str): location
        """
        self.link_type = link_type
        self.href = href

    @property
    def dict(self) -> dict:
        return dict(
            type=self.link_type,
            href=self.href
        )
