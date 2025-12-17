from __future__ import annotations

from . import deprecate

deprecate.module("stac_io")


class StacIO:
    @staticmethod
    def default() -> DefaultStacIO:
        return DefaultStacIO()


class DefaultStacIO(StacIO):
    pass
