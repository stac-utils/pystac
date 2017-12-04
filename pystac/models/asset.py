from pystac.models.base import STACObject


class Asset(STACObject):
    def __init__(self, href: str, file_format: str, product: str = "", name: str = ""):
        """Asset referenced by feature

        Args:
            href (str): location (full or relative) of asset
            name (str): human readable name of asset
            product (str): location of product definition
            file_format (str): filetype
        """
        self.format = file_format
        self.product = product
        self.name = name
        self.href = href

    @property
    def dict(self) -> dict:
        base_properties = dict(
            href=self.href
        )
        if self.name:
            base_properties['name'] = self.name
        if self.product:
            base_properties['product'] = self.product
        if self.format:
            base_properties['format'] = self.format
        return base_properties
