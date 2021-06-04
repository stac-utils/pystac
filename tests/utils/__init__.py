# flake8: noqa

import os
import tempfile
from typing import Any, Dict, Type, Optional
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


# Mypy raises an error for this class:
#  error: Missing type parameters for generic type "TemporaryDirectory"  [type-arg]
# Trying to add a concrete type (e.g. TemporaryDirectory[str]) satisfies mypy, but
# raises a runtime exception:
#  TypeError: 'type' object is not subscriptable
class TemporaryDirectory(tempfile.TemporaryDirectory):  # type: ignore [type-arg]
    def __init__(self, suffix: Optional[str] = None, prefix: Optional[str] = None):
        """In the GitHub Actions Windows runner the default TMPDIR directory is on a
        different drive (C:\\) than the code and test data files (D:\\). This was causing
        failures in os.path.relpath on Windows, so we put the temp directories in the
        current working directory instead. There os a "tmp*" line in the .gitignore file
        that ignores these directories."""
        super().__init__(suffix=suffix, prefix=prefix, dir=os.getcwd())
