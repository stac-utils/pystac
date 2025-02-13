import warnings

from typing_extensions import Self

warnings.warn(
    "The stac_io module, and all StacIO classes, are deprecated as of pystac v2.0 "
    "and will be removed in a future version. Use pystac.Reader and pystac.Writer "
    "instead.",
    FutureWarning,
)


class StacIO:
    @classmethod
    def default(cls: type[Self]) -> Self:
        return cls()
