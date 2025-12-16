from abc import ABC, abstractmethod

from ..stac_object import STACObject


class Validator(ABC):
    """A STAC validator."""

    @abstractmethod
    def validate(self, stac_object: STACObject) -> None:
        """Validates a STAC object."""
