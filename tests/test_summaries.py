import socket
import unittest
from typing import Any

from pystac.summaries import RangeSummary, Summaries, Summarizer, SummaryStrategy
from tests.utils import TestCases


class SummariesTest(unittest.TestCase):
    def test_summary(self) -> None:
        coll = TestCases.case_5()
        summaries = Summarizer().summarize(coll.get_items(recursive=True))
        summaries_dict = summaries.to_dict()
        self.assertEqual(len(summaries_dict["eo:bands"]), 4)
        self.assertEqual(len(summaries_dict["proj:code"]), 1)

    def test_summary_limit(self) -> None:
        coll = TestCases.case_5()
        summaries = Summarizer().summarize(coll.get_items(recursive=True))
        summaries.maxcount = 2
        summaries_dict = summaries.to_dict()
        self.assertIsNone(summaries_dict.get("eo:bands"))
        self.assertEqual(len(summaries_dict["proj:code"]), 1)

    def test_summary_custom_fields_file(self) -> None:
        coll = TestCases.case_5()
        path = TestCases.get_path("data-files/summaries/fields_no_bands.json")
        summaries = Summarizer(path).summarize(coll.get_items(recursive=True))
        summaries_dict = summaries.to_dict()
        self.assertIsNone(summaries_dict.get("eo:bands"))
        self.assertEqual(len(summaries_dict["proj:code"]), 1)

    def test_summary_custom_fields_dict(self) -> None:
        coll = TestCases.case_5()
        spec = {
            "eo:bands": SummaryStrategy.DONT_SUMMARIZE,
            "proj:code": SummaryStrategy.ARRAY,
        }
        obj = Summarizer(spec)
        self.assertTrue("eo:bands" not in obj.summaryfields)
        self.assertEqual(obj.summaryfields["proj:code"], SummaryStrategy.ARRAY)
        summaries = obj.summarize(coll.get_items(recursive=True))
        summaries_dict = summaries.to_dict()
        self.assertIsNone(summaries_dict.get("eo:bands"))
        self.assertEqual(len(summaries_dict["proj:code"]), 1)

    def test_summary_wrong_custom_fields_file(self) -> None:
        coll = TestCases.case_5()
        with self.assertRaises(FileNotFoundError) as context:
            Summarizer("wrong/path").summarize(coll.get_items(recursive=True))
        self.assertTrue("No such file or directory" in str(context.exception))

    def test_can_open_fields_file_even_with_no_nework(self) -> None:
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

    def test_summary_empty(self) -> None:
        summaries = Summaries.empty()
        self.assertTrue(summaries.is_empty())

    def test_summary_not_empty(self) -> None:
        coll = TestCases.case_5()
        summaries = Summarizer().summarize(coll.get_items(recursive=True))
        self.assertFalse(summaries.is_empty())

    def test_clone_summary(self) -> None:
        coll = TestCases.case_5()
        summaries = Summarizer().summarize(coll.get_items(recursive=True))
        summaries_dict = summaries.to_dict()
        clone = summaries.clone()
        self.assertTrue(isinstance(clone, Summaries))
        clone_dict = clone.to_dict()
        self.assertDictEqual(clone_dict, summaries_dict)


class RangeSummaryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    def test_repr(self) -> None:
        rs = RangeSummary(5, 10)
        self.assertEqual("{'minimum': 5, 'maximum': 10}", rs.__repr__())

    def test_equality(self) -> None:
        rs_1 = RangeSummary(5, 10)
        rs_2 = RangeSummary(5, 10)
        rs_3 = RangeSummary(5, 11)

        self.assertEqual(rs_1, rs_2)
        self.assertNotEqual(rs_1, rs_3)
        self.assertNotEqual(rs_1, (5, 10))
