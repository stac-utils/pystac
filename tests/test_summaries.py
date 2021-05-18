import unittest

from pystac.summaries import Summarizer, Summaries
from tests.utils import TestCases


class SummariesTest(unittest.TestCase):
    def test_summary(self):
        coll = TestCases.test_case_5()
        summaries = Summarizer().summarize(coll)
        summaries_dict = summaries.to_dict()
        self.assertEquals(len(summaries_dict["eo:bands"]), 4)
        self.assertEquals(len(summaries_dict["proj:epsg"]), 1)

    def test_summary_limit(self):
        coll = TestCases.test_case_5()
        summaries = Summarizer().summarize(coll)
        summaries.maxcount = 2
        summaries_dict = summaries.to_dict()
        self.assertIsNone(summaries_dict.get("eo:bands"))
        self.assertEquals(len(summaries_dict["proj:epsg"]), 1)

    def test_summary_custom_fields_file(self):
        coll = TestCases.test_case_5()
        path = TestCases.get_path("data-files/summaries/fields_no_bands.json")
        summaries = Summarizer(path).summarize(coll)
        summaries_dict = summaries.to_dict()
        self.assertIsNone(summaries_dict.get("eo:bands"))
        self.assertEquals(len(summaries_dict["proj:epsg"]), 1)

    def test_summary_wrong_custom_fields_file(self):
        coll = TestCases.test_case_5()
        summaries = Summarizer("wrong/path").summarize(coll)
        summaries_dict = summaries.to_dict()
        self.assertEquals(len(summaries_dict["eo:bands"]), 4)
        self.assertEquals(len(summaries_dict["proj:epsg"]), 1)

    def test_summary_empty(self):
        summaries = Summaries.empty()
        self.assertTrue(summaries.is_empty())

    def test_summary_not_empty(self):
        coll = TestCases.test_case_5()
        summaries = Summarizer().summarize(coll)
        self.assertFalse(summaries.is_empty())
