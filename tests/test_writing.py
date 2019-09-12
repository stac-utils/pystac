import unittest

from tests.utils import (TestCases, SchemaValidator)

class STACWriteTest(unittest.TestCase):
    def setUp(self):
        self.schema_validator = SchemaValidator()


    def validate_catalog(self, catalog):
        self.schema_validator.validate(catalog)
        validated_count = 1

        for child  in catalog.get_children():
            validated_count += self.validate_catalog(child)

        for item in catalog.get_items():
            self.schema_validator.validate(item)
            validated_count += 1

        return validated_count

    """Tests writing STACs, using JSON Schema validation"""
    def test_testcase1(self):
        catalog = TestCases.test_case_1()
        catalog.set_uris_from_root('/dev/null')
        self.validate_catalog(catalog)
