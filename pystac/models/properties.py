from datetime import datetime

from pystac.models.base import STACObject


class Properties(STACObject):
    def __init__(self, start: datetime, end: datetime,
                 provider: str, asset_license: str,
                 eo_properties: dict = None):
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
    def dict(self) -> dict:
        base_properties = dict(
            license=self.license,
            provider=self.provider,
            end=self.end.isoformat(),
            start=self.start.isoformat()
        )
        if self.eo_properties:
            base_properties.update(self.eo_properties)
        return base_properties
