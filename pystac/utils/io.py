from contextlib import contextmanager
import os
import logging
import shutil
import tempfile


logger = logging.getLogger(__name__)


@contextmanager
def get_tempdir():
    """Returns a temporary directory that is cleaned up after usage

    Returns:
        str
    """
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


def list_files_prefix(directory: str, prefix: str):
    return [os.path.join(directory, f) for f in os.listdir(directory) if prefix in f]
