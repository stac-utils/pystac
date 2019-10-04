import unittest
from tempfile import TemporaryDirectory

from pystac import STAC_IO, CatalogType

from tests.utils import (TestCases, SchemaValidator)

class STACJsonTest(unittest.TestCase):
    def setUp(self):
        self.schema_validator = SchemaValidator()


    def validate_catalog(self, catalog):
        self.schema_validator.validate_object(catalog)
        validated_count = 1

        for child in catalog.get_children():
            validated_count += self.validate_catalog(child)

        for item in catalog.get_items():
            self.schema_validator.validate_object(item)
            validated_count += 1

        return validated_count

    def validate_file(self, path, object_type):
        d = STAC_IO.read_json(path)
        return self.schema_validator.validate_dict(d, object_type)

    """Tests writing STACs, using JSON Schema validation"""
    def test_testcase1_absolute_published(self):
        catalog = TestCases.test_case_1()

        with TemporaryDirectory() as tmp_dir:
            catalog.normalize_hrefs(tmp_dir)
            self.validate_catalog(catalog)

            catalog.save()

            for parent, children, items in catalog.walk():
                self.validate_file(parent.get_self_href(), type(parent))

                for item in items:
                    self.validate_file(item.get_self_href(), type(item))

    def test_testcase1_relative_published(self):
        catalog = TestCases.test_case_1()

        with TemporaryDirectory() as tmp_dir:
            catalog.normalize_hrefs(tmp_dir)
            self.validate_catalog(catalog)

            catalog.save(catalog_type=CatalogType.RELATIVE_PUBLISHED)

            for parent, children, items in catalog.walk():
                self.validate_file(parent.get_self_href(), type(parent))

                for item in items:
                    self.validate_file(item.get_self_href(), type(item))

    def test_testcase1_self_contained(self):
        catalog = TestCases.test_case_1()

        with TemporaryDirectory() as tmp_dir:
            catalog.normalize_hrefs(tmp_dir)
            self.validate_catalog(catalog)

            catalog.save(catalog_type=CatalogType.SELF_CONTAINED)

            for parent, children, items in catalog.walk():
                self.validate_file(parent.get_self_href(), type(parent))

                for item in items:
                    self.validate_file(item.get_self_href(), type(item))
