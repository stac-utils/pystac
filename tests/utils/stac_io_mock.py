from typing import Any, Union
from unittest.mock import Mock

from pystac.link import Link
from pystac.stac_io import StacIO


class MockStacIO(StacIO):
    """Creates a mock that records StacIO calls for testing and allows
    clients to replace StacIO functionality, all within a context scope.
    """

    def __init__(self) -> None:
        self.mock = Mock()

    def read_text(self, source: Union[str, Link], *args: Any, **kwargs: Any) -> str:
        self.mock.read_text(source)
        return StacIO.default().read_text(source)

    def write_text(
        self, dest: Union[str, Link], txt: str, *args: Any, **kwargs: Any
    ) -> None:
        self.mock.write_text(dest, txt)
        StacIO.default().write_text(dest, txt)
