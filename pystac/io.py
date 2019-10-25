import os
import json


class STAC_IO:
    """Methods used to read and save STAC json.
    Allows users of the library to set their own methods
    (e.g. for reading and writing from cloud storage)
    """
    def default_read_text_method(uri):
        """Default method for reading text. Only handles local file paths."""
        with open(uri) as f:
            return f.read()

    def default_write_text_method(uri, txt):
        """Default method for writing text. Only handles local file paths."""
        with open(uri, 'w') as f:
            f.write(txt)

    read_text_method = default_read_text_method
    """Users of PySTAC can replace the read_text_method in order
    to expand the ability of PySTAC to read different file systems.
    For example, a client of the library might replace this class
    member in it's own __init__.py with a method that can read from
    cloud storage.
    """

    write_text_method = default_write_text_method
    """Users of PySTAC can replace the writte_text_method in order
    to expand the ability of PySTAC to write to different file systems.
    For example, a client of the library might replace this class
    member in it's own __init__.py with a method that can read from
    cloud storage.
    """

    # Replaced in __init__ to account for extension objects.
    stac_object_from_dict = None

    # This is set in __init__.py
    STAC_OBJECT_CLASSES = None

    @classmethod
    def read_text(cls, uri):
        """Read text from the given URI."""
        return cls.read_text_method(uri)

    @classmethod
    def write_text(cls, uri, txt):
        """Write text to the given URI."""
        cls.write_text_method(uri, txt)

    @classmethod
    def read_json(cls, uri):
        """Read a dict from the given URI."""
        return json.loads(STAC_IO.read_text(uri))

    @classmethod
    def read_stac_object(cls, uri):
        """Read a STACObject from the given URI."""
        d = cls.read_json(uri)
        return cls.stac_object_from_dict(d)

    @classmethod
    def save_json(cls, uri, json_dict):
        """Write a dict to the given URI as JSON."""
        dirname = os.path.dirname(uri)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        STAC_IO.write_text(uri, json.dumps(json_dict, indent=4))
