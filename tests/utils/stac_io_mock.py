from typing import Any, Union
from unittest.mock import Mock

import pystac as ps


class MockStacIO(ps.StacIO):
    """Creates a mock that records STAC_IO calls for testing and allows
    clients to replace STAC_IO functionality, all within a context scope.
    """

    def __init__(self):
        self.mock = Mock()

    def read_text(self, source: Union[str, ps.Link], *args: Any, **kwargs: Any) -> str:
        self.mock.read_text(source)
        return ps.StacIO.default().read_text(source)

    def write_text(
        self, dest: Union[str, ps.Link], txt: str, *args: Any, **kwargs: Any
    ) -> None:
        self.mock.write_text(dest, txt)
        ps.StacIO.default().write_text(dest, txt)
