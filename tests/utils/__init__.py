# flake8: noqa

import os
from tempfile import TemporaryDirectory
from typing import Any, AnyStr, Dict, TYPE_CHECKING, Type
import unittest
from tests.utils.test_cases import (
    TestCases,
    ARBITRARY_GEOM,
    ARBITRARY_BBOX,
    ARBITRARY_EXTENT,
)

from copy import deepcopy
from datetime import datetime
from dateutil.parser import parse

import pystac
from tests.utils.stac_io_mock import MockStacIO

if TYPE_CHECKING:
    from tempfile import TemporaryDirectory as TemporaryDirectory_Type


def assert_to_from_dict(
    test_class: unittest.TestCase,
    stac_object_class: Type[pystac.STACObject],
    d: Dict[str, Any],
) -> None:
    def _parse_times(a_dict: Dict[str, Any]) -> None:
        for k, v in a_dict.items():
            if isinstance(v, dict):
                _parse_times(v)
            elif isinstance(v, (tuple, list, set)):
                for vv in v:
                    if isinstance(vv, dict):
                        _parse_times(vv)
            else:
                if k == "datetime":
                    if not isinstance(v, datetime):
                        a_dict[k] = parse(v)
                        a_dict[k] = a_dict[k].replace(microsecond=0)

    d1 = deepcopy(d)
    d2 = stac_object_class.from_dict(d).to_dict()
    _parse_times(d1)
    _parse_times(d2)
    test_class.assertDictEqual(d1, d2)


# Use suggestion from https://github.com/python/mypy/issues/5264#issuecomment-399407428
# to solve type errors.
def get_temp_dir() -> "TemporaryDirectory_Type[str]":
    """In the GitHub Actions Windows runner the default TMPDIR directory is on a
    different drive (C:\\) than the code and test data files (D:\\). This was causing
    failures in os.path.relpath on Windows, so we put the temp directories in the
    current working directory instead. There os a "tmp*" line in the .gitignore file
    that ignores these directories."""
    return TemporaryDirectory(dir=os.getcwd())
