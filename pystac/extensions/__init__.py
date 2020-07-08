# flake8: noqa


class Extensions:
    """Enumerates the IDs of common extensions."""
    ASSETS = 'asset'
    CHECKSUM = 'checksum'
    DATACUBE = 'datacube'
    DATETIME_RANGE = 'datetime-range'
    EO = 'eo'
    LABEL = 'label'
    POINTCLOUD = 'pointcloud'
    SAR = 'sar'
    SCIENTIFIC = 'scientific'
    SINGLE_FILE_STAC = 'single-file-stac'
    VIEW = 'view'


from pystac.extensions.base import ExtensionError
