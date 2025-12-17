from typing import Any

from . import deprecate
from .constants import DEFAULT_STAC_VERSION
from .stac_object import STACObject


@deprecate.function("Use DEFAULT_STAC_VERSION instead.")
def get_stac_version() -> str:
    """**DEPRECATED** Returns the default STAC version.

    Warning:
        This function is deprecated as of PySTAC v2.0 and will be removed in a
        future version. Just look at
        [DEFAULT_STAC_VERSION][pystac.DEFAULT_STAC_VERSION].

    Returns:
        The default STAC version.

    Examples:
        >>> pystac.get_stac_version()
        "1.1.0"
    """
    return DEFAULT_STAC_VERSION


@deprecate.function(
    "This function is a no-op. Use `Container.set_stac_version()` to modify the STAC "
    "version of an entire catalog."
)
def set_stac_version(version: str) -> None:  # pyright: ignore[reportUnusedParameter]
    """**DEPRECATED** This function is a no-op and will be removed in a future version

    Warning:
        In pre-v2.0 PySTAC, this function was used to set the global STAC version.
        In PySTAC v2.0 this global capability has been removed — the user should
        use `Container.set_stac_version()` to mutate an entire catalog.
    """


@deprecate.function("Use STACObject.from_dict instead")
def read_dict(d: dict[str, Any]) -> STACObject:
    """**DEPRECATED** Reads a STAC object from a dictionary.

    Warning:
        This function is deprecated as of PySTAC v2.0 and will be removed in a
        future version. Use [STACObject.from_dict][pystac.STACObject.from_dict] instead.
    """
    return STACObject.from_dict(d)
