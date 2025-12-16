import datetime
import json

import pytest

from pystac import SpatialExtent, STACWarning, TemporalExtent


def test_temporal_with_datetimes() -> None:
    extent = TemporalExtent([[datetime.datetime(2023, 1, 1), None]])
    json.dumps(extent.to_dict())


def test_temporal_with_unnested_list() -> None:
    extent = TemporalExtent(["2025-02-11T00:00:00Z", None])
    d = extent.to_dict()
    assert d == {"interval": [["2025-02-11T00:00:00Z", None]]}


def test_temporal_with_mixed_list() -> None:
    # This is awkward, and the right thing to do is questionable
    # We've chosen "truncate", aka discard any invalid stuff after we've started
    # down a "correct-ish" path
    with pytest.warns(STACWarning):
        extent = TemporalExtent(["2025-02-11T00:00:00Z", [None, None]])
    d = extent.to_dict()
    assert d == {"interval": [["2025-02-11T00:00:00Z", None]]}


def test_temporal_with_long_list() -> None:
    with pytest.warns(STACWarning):
        extent = TemporalExtent([["2025-02-11T00:00:00Z", None, None]])
    d = extent.to_dict()
    assert d == {"interval": [["2025-02-11T00:00:00Z", None]]}


def test_temporal_with_bad_tail() -> None:
    with pytest.warns(STACWarning):
        extent = TemporalExtent(
            [
                ["2025-02-11T00:00:00Z", None],
                "2025-02-11T01:00:00Z",
                "2025-02-11T02:00:00Z",
            ]
        )
    d = extent.to_dict()
    assert d == {"interval": [["2025-02-11T00:00:00Z", None]]}


def test_temporal_from_now() -> None:
    extent = TemporalExtent.from_now()
    assert isinstance(extent.interval[0][0], str)
    assert extent.interval[0][1] is None


def test_spatial_from_coordinates() -> None:
    with pytest.warns(FutureWarning):
        SpatialExtent.from_coordinates([-180, -90, 180, 90])
