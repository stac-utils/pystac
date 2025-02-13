from .projection import ProjectionExtension
from .protocols import Extendable


class Extensions:
    """Manage extensions on a STAC object."""

    def __init__(self, extendable: Extendable) -> None:
        self.extendable = extendable

    @property
    def proj(self) -> ProjectionExtension:
        return ProjectionExtension(self.extendable)
