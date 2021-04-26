# flake8: noqa


class ExtensionError(Exception):
    """An error related to the construction of extensions.
    """
    pass

from pystac.extensions.eo import eo_ext  # type:ignore
from pystac.extensions.file import file_ext  # type:ignore
from pystac.extensions.label import label_ext  # type:ignore
