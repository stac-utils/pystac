# flake8: noqa


class ExtensionError(Exception):
    """An error related to the construction of extensions.
    """
    pass


class Extensions:
    """Enumerates the IDs of common extensions."""
    CHECKSUM = 'checksum'
    COLLECTION_ASSETS = 'collection-assets'
    DATACUBE = 'datacube'
    EO = 'eo'
    ITEM_ASSETS = 'item-assets'
    LABEL = 'label'
    POINTCLOUD = 'pointcloud'
    PROJECTION = 'projection'
    SAR = 'sar'
    SAT = 'sat'
    SCIENTIFIC = 'scientific'
    SINGLE_FILE_STAC = 'single-file-stac'
    TILED_ASSETS = 'tiled-assets'
    TIMESTAMPS = 'timestamps'
    VERSION = 'version'
    VIEW = 'view'
