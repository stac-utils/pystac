import ssl
from urllib.request import urlopen
from urllib.parse import urlparse
from urllib.error import HTTPError

from pystac.stac_io import STAC_IO

# Set the STAC_IO read method to read HTTP.
# Skip SSL Certification because it fails on some machines.


def unsafe_read_https_method(uri):
    parsed = urlparse(uri)
    try:
        if parsed.scheme == 'https':
            context = ssl._create_unverified_context()
            with urlopen(uri, context=context) as f:
                return f.read().decode('utf-8')
        elif parsed.scheme == 'http':
            # Avoid reading cool-sat.com
            if parsed.netloc == 'cool-sat.com':
                raise HTTPError(url=uri,
                                msg='cool-sat.com does not exist',
                                hdrs=None,
                                code=404,
                                fp=None)

            with urlopen(uri) as f:
                return f.read().decode('utf-8')
        else:
            with open(uri) as f:
                return f.read()
    except HTTPError as e:
        raise Exception("Could not read uri {}".format(uri)) from e


STAC_IO.read_text_method = unsafe_read_https_method
