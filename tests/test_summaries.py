import socket
from typing import Any

import pytest

from pystac.summaries import RangeSummary, Summaries, Summarizer, SummaryStrategy
from tests.utils import TestCases


def test_summary() -> None:
    coll = TestCases.case_5()
    summaries = Summarizer().summarize(coll.get_items(recursive=True))
    summaries_dict = summaries.to_dict()
    assert len(summaries_dict["eo:bands"]) == 4
    assert len(summaries_dict["proj:code"]) == 1


def test_summary_limit() -> None:
    coll = TestCases.case_5()
    summaries = Summarizer().summarize(coll.get_items(recursive=True))
    summaries.maxcount = 2
    summaries_dict = summaries.to_dict()
    assert summaries_dict.get("eo:bands") is None
    assert len(summaries_dict["proj:code"]) == 1


def test_summary_custom_fields_file() -> None:
    coll = TestCases.case_5()
    path = TestCases.get_path("data-files/summaries/fields_no_bands.json")
    summaries = Summarizer(path).summarize(coll.get_items(recursive=True))
    summaries_dict = summaries.to_dict()
    assert summaries_dict.get("eo:bands") is None
    assert len(summaries_dict["proj:code"]) == 1


def test_summary_custom_fields_dict() -> None:
    coll = TestCases.case_5()
    spec = {
        "eo:bands": SummaryStrategy.DONT_SUMMARIZE,
        "proj:code": SummaryStrategy.ARRAY,
    }
    obj = Summarizer(spec)
    assert "eo:bands" not in obj.summaryfields
    assert obj.summaryfields["proj:code"] == SummaryStrategy.ARRAY
    summaries = obj.summarize(coll.get_items(recursive=True))
    summaries_dict = summaries.to_dict()
    assert summaries_dict.get("eo:bands") is None
    assert len(summaries_dict["proj:code"]) == 1


def test_summary_wrong_custom_fields_file() -> None:
    coll = TestCases.case_5()
    with pytest.raises(FileNotFoundError) as context:
        Summarizer("wrong/path").summarize(coll.get_items(recursive=True))
    assert "No such file or directory" in str(context.value)


def test_can_open_fields_file_even_with_no_nework() -> None:
    old_socket = socket.socket
    try:

        class no_network(socket.socket):
            def __init__(self, *args: Any, **kwargs: Any):
                raise Exception("Network call blocked")

        socket.socket = no_network  # type:ignore
        Summarizer()
    finally:
        # even if this test fails, it should not break the whole test suite
        socket.socket = old_socket  # type:ignore


def test_summary_empty() -> None:
    summaries = Summaries.empty()
    assert summaries.is_empty()


def test_summary_not_empty() -> None:
    coll = TestCases.case_5()
    summaries = Summarizer().summarize(coll.get_items(recursive=True))
    assert not summaries.is_empty()


def test_clone_summary() -> None:
    coll = TestCases.case_5()
    summaries = Summarizer().summarize(coll.get_items(recursive=True))
    summaries_dict = summaries.to_dict()
    clone = summaries.clone()
    assert isinstance(clone, Summaries)
    clone_dict = clone.to_dict()
    assert clone_dict == summaries_dict


def test_RangeSummary_repr() -> None:
    rs = RangeSummary(5, 10)
    assert "{'minimum': 5, 'maximum': 10}" == rs.__repr__()


def test_RangeSummary_equality() -> None:
    rs_1 = RangeSummary(5, 10)
    rs_2 = RangeSummary(5, 10)
    rs_3 = RangeSummary(5, 11)

    assert rs_1 == rs_2
    assert rs_1 != rs_3
    assert rs_1 != (5, 10)
