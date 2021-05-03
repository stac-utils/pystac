from typing import Any, Union
from unittest.mock import Mock

import pystac


class MockStacIO(pystac.StacIO):
    """Creates a mock that records STAC_IO calls for testing and allows
    clients to replace STAC_IO functionality, all within a context scope.
    """

    def __init__(self):
        self.mock = Mock()

    def read_text(
        self, source: Union[str, pystac.Link], *args: Any, **kwargs: Any
    ) -> str:
        self.mock.read_text(source)
        return pystac.StacIO.default().read_text(source)

    def write_text(
        self, dest: Union[str, pystac.Link], txt: str, *args: Any, **kwargs: Any
    ) -> None:
        self.mock.write_text(dest, txt)
        pystac.StacIO.default().write_text(dest, txt)
