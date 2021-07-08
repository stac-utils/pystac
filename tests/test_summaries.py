import socket
from typing import Any
import unittest

from pystac.summaries import RangeSummary, Summarizer, Summaries
from tests.utils import TestCases


class SummariesTest(unittest.TestCase):
    def test_summary(self) -> None:
        coll = TestCases.test_case_5()
        summaries = Summarizer().summarize(coll.get_all_items())
        summaries_dict = summaries.to_dict()
        self.assertEqual(len(summaries_dict["eo:bands"]), 4)
        self.assertEqual(len(summaries_dict["proj:epsg"]), 1)

    def test_summary_limit(self) -> None:
        coll = TestCases.test_case_5()
        summaries = Summarizer().summarize(coll.get_all_items())
        summaries.maxcount = 2
        summaries_dict = summaries.to_dict()
        self.assertIsNone(summaries_dict.get("eo:bands"))
        self.assertEqual(len(summaries_dict["proj:epsg"]), 1)

    def test_summary_custom_fields_file(self) -> None:
        coll = TestCases.test_case_5()
        path = TestCases.get_path("data-files/summaries/fields_no_bands.json")
        summaries = Summarizer(path).summarize(coll.get_all_items())
        summaries_dict = summaries.to_dict()
        self.assertIsNone(summaries_dict.get("eo:bands"))
        self.assertEqual(len(summaries_dict["proj:epsg"]), 1)

    def test_summary_wrong_custom_fields_file(self) -> None:
        coll = TestCases.test_case_5()
        with self.assertRaises(FileNotFoundError) as context:
            Summarizer("wrong/path").summarize(coll.get_all_items())
        self.assertTrue("No such file or directory" in str(context.exception))

    def test_cannot_open_fields_file(self) -> None:
        old_socket = socket.socket

        class no_network(socket.socket):
            def __init__(self, *args: Any, **kwargs: Any):
                raise Exception("Network call blocked")

        socket.socket = no_network  # type:ignore

        with self.assertRaises(Exception) as context:
            Summarizer()
        socket.socket = old_socket  # type:ignore
        self.assertTrue("Could not read fields definition" in str(context.exception))

    def test_summary_empty(self) -> None:
        summaries = Summaries.empty()
        self.assertTrue(summaries.is_empty())

    def test_summary_not_empty(self) -> None:
        coll = TestCases.test_case_5()
        summaries = Summarizer().summarize(coll.get_all_items())
        self.assertFalse(summaries.is_empty())


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
