import ssl
from urllib.request import urlopen
from urllib.parse import urlparse

from pystac.stac_io import STAC_IO

# Set the STAC_IO read method to read HTTP.
# Skip SSL Certification because it fails on some machines.


def unsafe_read_https_method(uri):
    parsed = urlparse(uri)
    if parsed.scheme == 'https':
        context = ssl._create_unverified_context()
        with urlopen(uri, context=context) as f:
            return f.read().decode('utf-8')
    elif parsed.scheme == 'http':
        with urlopen(uri) as f:
            return f.read().decode('utf-8')
    else:
        with open(uri) as f:
            return f.read()


STAC_IO.read_text_method = unsafe_read_https_method
