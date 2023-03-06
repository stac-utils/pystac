__all__ = [
    "TestCases",
    "ARBITRARY_GEOM",
    "ARBITRARY_BBOX",
    "ARBITRARY_EXTENT",
    "MockStacIO",
]
import unittest
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, Type

from dateutil.parser import parse

import pystac
from tests.utils.stac_io_mock import MockStacIO
from tests.utils.test_cases import (
    ARBITRARY_BBOX,
    ARBITRARY_EXTENT,
    ARBITRARY_GEOM,
    TestCases,
)


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
