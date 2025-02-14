from typing_extensions import Self

from . import deprecate

deprecate.module("stac_io")


class StacIO:
    @classmethod
    def default(cls: type[Self]) -> Self:
        return cls()
