from typing import Any


class BenchImportPySTAC:
    repeat = 10

    def setup(self, *args: Any, **kwargs: Any) -> None:
        def import_pystac() -> None:
            import pystac  # noqa: F401

        self._import_pystac = import_pystac

    def time_import_pystac(self) -> None:
        self._import_pystac()
