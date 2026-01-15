from typing import Any, final

import pytest

from pystac import Asset
from pystac.common import DataValue


@final
class Common(DataValue):
    def __init__(self, **kwargs: Any):
        self.extra_fields = kwargs


def test_data_type_set_to_invalid_value() -> None:
    common = Common()
    with pytest.raises(ValueError, match="'bad' is not a valid DataType"):
        common.data_type = "bad"


def test_data_type_repr() -> None:
    common = Common()
    common.data_type = "int8"
    assert common.data_type.__repr__() == "int8"


def test_setting_statistics_directly_raises() -> None:
    common = Common()
    with pytest.raises(AttributeError):
        common.statistics = {}  # pyright: ignore [reportAttributeAccessIssue]


def test_get_data_value_common_fields_on_asset() -> None:
    asset = Asset(href="foo", data_type="int8", statistics=dict(minimum=3, maximum=5))
    assert asset.data_type == "int8"
    assert asset.statistics.minimum == 3
    assert asset.statistics.maximum == 5
    assert asset.extra_fields == {
        "data_type": "int8",
        "statistics": {
            "minimum": 3,
            "maximum": 5,
        },
    }


def test_set_data_value_common_fields_on_asset() -> None:
    asset = Asset(href="foo")
    asset.data_type = "int8"
    asset.nodata = None
    asset.statistics.minimum = 3
    asset.statistics.maximum = 5
    asset.statistics.count = None

    asset_dict = asset.to_dict()
    assert asset_dict == {
        "href": "foo",
        "data_type": "int8",
        "statistics": {
            "minimum": 3,
            "maximum": 5,
        },
    }


def test_get_instrument_common_fields_on_asset() -> None:
    asset = Asset(href="foo", gsd=60)
    assert asset.gsd == 60
    assert asset.extra_fields == {"gsd": 60}
