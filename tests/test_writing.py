import unittest
from tempfile import TemporaryDirectory

from pystac import (STAC_IO, STACObject, CatalogType, LinkType)
from pystac.utils import make_absolute_href

from tests.utils import (TestCases, SchemaValidator)


class STACWritingTest(unittest.TestCase):
    """Tests writing STACs, using JSON Schema validation,
    and ensure that links are correctly set to relative or absolute.
    """
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

    def validate_link_types(self, root_href, catalog_type):
        def validate_item_link_type(href, link_type, should_include_self):
            item_dict = STAC_IO.read_json(href)
            item = STACObject.from_file(href)
            for link in item.get_links():
                if not link.rel == 'self':
                    self.assertEqual(link.link_type, link_type)

            rels = set([l['rel'] for l in item_dict['links']])
            self.assertEqual('self' in rels, should_include_self)

        def validate_catalog_link_type(href, link_type, should_include_self):
            cat_dict = STAC_IO.read_json(href)
            cat = STACObject.from_file(href)
            for link in cat.get_links():
                if not link.rel == 'self':
                    self.assertEqual(link.link_type, link_type)

            rels = set([l['rel'] for l in cat_dict['links']])
            self.assertEqual('self' in rels, should_include_self)

            for child_link in cat.get_child_links():
                child_href = make_absolute_href(child_link.target, href)
                validate_catalog_link_type(
                    child_href, link_type,
                    catalog_type == CatalogType.ABSOLUTE_PUBLISHED)

            for item_link in cat.get_item_links():
                item_href = make_absolute_href(item_link.target, href)
                validate_item_link_type(
                    item_href, link_type,
                    catalog_type == CatalogType.ABSOLUTE_PUBLISHED)

        link_type = LinkType.RELATIVE
        if catalog_type == CatalogType.ABSOLUTE_PUBLISHED:
            link_type = LinkType.ABSOLUTE

        root_should_include_href = catalog_type in [
            CatalogType.ABSOLUTE_PUBLISHED, CatalogType.RELATIVE_PUBLISHED
        ]

        validate_catalog_link_type(root_href, link_type,
                                   root_should_include_href)

    def do_test(self, catalog, catalog_type):
        with TemporaryDirectory() as tmp_dir:
            catalog.normalize_hrefs(tmp_dir)
            self.validate_catalog(catalog)

            catalog.save(catalog_type=catalog_type)

            root_href = catalog.get_self_href()
            self.validate_link_types(root_href, catalog_type)

            for parent, children, items in catalog.walk():
                self.validate_file(parent.get_self_href(), type(parent))

                for item in items:
                    self.validate_file(item.get_self_href(), type(item))

    def test_testcase1_absolute_published(self):
        catalog = TestCases.test_case_1()
        self.do_test(catalog, CatalogType.ABSOLUTE_PUBLISHED)

    def test_testcase1_relative_published(self):
        catalog = TestCases.test_case_1()
        self.do_test(catalog, CatalogType.RELATIVE_PUBLISHED)

    def test_testcase1_self_contained(self):
        catalog = TestCases.test_case_1()
        self.do_test(catalog, CatalogType.SELF_CONTAINED)

    def test_testcase2_absolute_published(self):
        catalog = TestCases.test_case_2()

        catalog = catalog.full_copy()
        self.do_test(catalog, CatalogType.ABSOLUTE_PUBLISHED)

    def test_testcase2_relative_published(self):
        catalog = TestCases.test_case_2()
        self.do_test(catalog, CatalogType.RELATIVE_PUBLISHED)

    def test_testcase2_self_contained(self):
        catalog = TestCases.test_case_2()
        self.do_test(catalog, CatalogType.SELF_CONTAINED)

    def test_testcase3_absolute_published(self):
        catalog = TestCases.test_case_3()

        catalog = catalog.full_copy()
        self.do_test(catalog, CatalogType.ABSOLUTE_PUBLISHED)

    def test_testcase3_relative_published(self):
        catalog = TestCases.test_case_3()
        self.do_test(catalog, CatalogType.RELATIVE_PUBLISHED)

    def test_testcase3_self_contained(self):
        catalog = TestCases.test_case_3()
        self.do_test(catalog, CatalogType.SELF_CONTAINED)
