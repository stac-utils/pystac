import os
from typing import Any, AnyStr, Optional, Union
from unittest.mock import Mock

import pystac
from pystac.link import HREF
from pystac.stac_io import DefaultStacIO, StacIO


class MockStacIO(pystac.StacIO):
    """Creates a mock that records StacIO calls for testing and allows
    clients to replace StacIO functionality, all within a context scope.

    Args:
        wrapped_stac_io: The StacIO that will be used to perform the calls.
            Defaults to an instance of DefaultStacIO.
    """

    mock: Mock
    wrapped_stac_io: StacIO

    def __init__(self, wrapped_stac_io: Optional[StacIO] = None) -> None:
        self.mock = Mock()
        if wrapped_stac_io is None:
            self.wrapped_stac_io = DefaultStacIO()
        else:
            self.wrapped_stac_io = wrapped_stac_io

    def read_text(self, source: HREF, *args: Any, **kwargs: Any) -> str:
        self.mock.read_text(source)
        return self.wrapped_stac_io.read_text(source)

    def write_text(
        self,
        dest: Union[str, "os.PathLike[AnyStr]"],
        txt: str,
        *args: Any,
        **kwargs: Any
    ) -> None:
        self.mock.write_text(dest, txt)
        self.wrapped_stac_io.write_text(dest, txt)


class MockDefaultStacIO(object):
    """Context manager for mocking StacIO."""

    def __enter__(self) -> MockStacIO:
        mock = MockStacIO()
        pystac.StacIO.set_default(lambda: mock)
        return mock

    def __exit__(self, *args: Any) -> None:
        pystac.StacIO.set_default(DefaultStacIO)
