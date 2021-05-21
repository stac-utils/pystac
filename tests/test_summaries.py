import socket
import unittest

from pystac.summaries import Summarizer, Summaries
from tests.utils import TestCases


class SummariesTest(unittest.TestCase):
    def test_summary(self):
        coll = TestCases.test_case_5()
        summaries = Summarizer().summarize(coll.get_all_items())
        summaries_dict = summaries.to_dict()
        self.assertEqual(len(summaries_dict["eo:bands"]), 4)
        self.assertEqual(len(summaries_dict["proj:epsg"]), 1)

    def test_summary_limit(self):
        coll = TestCases.test_case_5()
        summaries = Summarizer().summarize(coll.get_all_items())
        summaries.maxcount = 2
        summaries_dict = summaries.to_dict()
        self.assertIsNone(summaries_dict.get("eo:bands"))
        self.assertEqual(len(summaries_dict["proj:epsg"]), 1)

    def test_summary_custom_fields_file(self):
        coll = TestCases.test_case_5()
        path = TestCases.get_path("data-files/summaries/fields_no_bands.json")
        summaries = Summarizer(path).summarize(coll.get_all_items())
        summaries_dict = summaries.to_dict()
        self.assertIsNone(summaries_dict.get("eo:bands"))
        self.assertEqual(len(summaries_dict["proj:epsg"]), 1)

    def test_summary_wrong_custom_fields_file(self):
        coll = TestCases.test_case_5()
        with self.assertRaises(FileNotFoundError) as context:
            summaries = Summarizer("wrong/path").summarize(coll.get_all_items())
        self.assertTrue("No such file or directory" in str(context.exception))


    def test_cannot_open_fields_file(self):
        old_socket = socket.socket
        class no_network(socket.socket):
            def __init__(self, *args, **kwargs):
                raise Exception("Network call blocked")
        socket.socket = no_network

        with self.assertRaises(Exception) as context:
            summaries = Summarizer()
        socket.socket = old_socket
        self.assertTrue("Could not read fields definition file" in str(context.exception))

    def test_summary_empty(self):
        summaries = Summaries.empty()
        self.assertTrue(summaries.is_empty())

    def test_summary_not_empty(self):
        coll = TestCases.test_case_5()
        summaries = Summarizer().summarize(coll.get_all_items())
        self.assertFalse(summaries.is_empty())
