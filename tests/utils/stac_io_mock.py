from unittest.mock import Mock

from pystac.stac_io import STAC_IO


class MockStacIO:
    """Creates a mock that records STAC_IO calls for testing and allows
    clients to replace STAC_IO functionality, all within a context scope.
    """
    def __init__(self, read_text_method=None, write_text_method=None):
        self.read_text_method = read_text_method
        self.write_text_method = write_text_method

    def __enter__(self):
        mock = Mock()
        self.old_read_text_method = STAC_IO.read_text_method
        self.old_write_text_method = STAC_IO.write_text_method

        def read_text_method(uri):
            mock.read_text_method(uri)
            if self.read_text_method:
                return self.read_text_method(uri)
            else:
                return self.old_read_text_method(uri)

        def write_text_method(uri, txt):
            mock.write_text_method(uri, txt)
            if self.write_text_method:
                return self.write_text_method(uri, txt)
            else:
                return self.old_write_text_method(uri, txt)

        STAC_IO.read_text_method = read_text_method
        STAC_IO.write_text_method = write_text_method

        return mock

    def __exit__(self, type, value, traceback):
        STAC_IO.read_text_method = self.old_read_text_method
        STAC_IO.write_text_method = self.old_write_text_method
