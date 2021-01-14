import unittest
from tempfile import TemporaryDirectory

from pystac import (STAC_IO, STACObject, Collection, CatalogType, LinkType)
from pystac.serialization import (STACObjectType)
from pystac.utils import is_absolute_href, make_absolute_href, make_relative_href
from pystac.validation import validate_dict

from tests.utils import TestCases


class STACWritingTest(unittest.TestCase):
    """Tests writing STACs, using JSON Schema validation,
    and ensure that links are correctly set to relative or absolute.
    """
    def validate_catalog(self, catalog):
        catalog.validate()
        validated_count = 1

        for child in catalog.get_children():
            validated_count += self.validate_catalog(child)

        for item in catalog.get_items():
            item.validate()
            validated_count += 1

        return validated_count

    def validate_file(self, path, object_type):
        d = STAC_IO.read_json(path)
        return validate_dict(d, object_type)

    def validate_link_types(self, root_href, catalog_type):
        def validate_asset_href_type(item, item_href, link_type):
            for asset in item.assets.values():
                if link_type == LinkType.ABSOLUTE:
                    self.assertTrue(is_absolute_href(asset.href))
                else:
                    is_valid = not is_absolute_href(asset.href)
                    if not is_valid:
                        # If the item href and asset href don't share
                        # the same root, the asset href must be absolute
                        rel_href = make_relative_href(asset.href, item_href)
                        self.assertEqual(asset.href, rel_href)
                    else:
                        self.assertTrue(is_valid)

        def validate_item_link_type(href, link_type, should_include_self):
            item_dict = STAC_IO.read_json(href)
            item = STACObject.from_file(href)
            for link in item.get_links():
                if not link.rel == 'self':
                    self.assertEqual(link.link_type, link_type)

            validate_asset_href_type(item, href, link_type)

            rels = set([link['rel'] for link in item_dict['links']])
            self.assertEqual('self' in rels, should_include_self)

        def validate_catalog_link_type(href, link_type, should_include_self):
            cat_dict = STAC_IO.read_json(href)
            cat = STACObject.from_file(href)
            for link in cat.get_links():
                if not link.rel == 'self':
                    self.assertEqual(link.link_type, link_type)

            rels = set([link['rel'] for link in cat_dict['links']])
            self.assertEqual('self' in rels, should_include_self)

            for child_link in cat.get_child_links():
                child_href = make_absolute_href(child_link.target, href)
                validate_catalog_link_type(child_href, link_type,
                                           catalog_type == CatalogType.ABSOLUTE_PUBLISHED)

            for item_link in cat.get_item_links():
                item_href = make_absolute_href(item_link.target, href)
                validate_item_link_type(item_href, link_type,
                                        catalog_type == CatalogType.ABSOLUTE_PUBLISHED)

        link_type = LinkType.RELATIVE
        if catalog_type == CatalogType.ABSOLUTE_PUBLISHED:
            link_type = LinkType.ABSOLUTE

        root_should_include_href = catalog_type in [
            CatalogType.ABSOLUTE_PUBLISHED, CatalogType.RELATIVE_PUBLISHED
        ]

        validate_catalog_link_type(root_href, link_type, root_should_include_href)

    def do_test(self, catalog, catalog_type):
        with TemporaryDirectory() as tmp_dir:
            catalog.normalize_hrefs(tmp_dir)
            self.validate_catalog(catalog)

            catalog.save(catalog_type=catalog_type)

            root_href = catalog.get_self_href()
            self.validate_link_types(root_href, catalog_type)

            for parent, children, items in catalog.walk():
                if issubclass(type(parent), Collection):
                    stac_object_type = STACObjectType.COLLECTION
                else:
                    stac_object_type = STACObjectType.CATALOG
                self.validate_file(parent.get_self_href(), stac_object_type)

                for item in items:
                    self.validate_file(item.get_self_href(), STACObjectType.ITEM)

    def test_testcases(self):
        for catalog in TestCases.all_test_catalogs():
            catalog = catalog.full_copy()
            for catalog_type in [
                    CatalogType.ABSOLUTE_PUBLISHED, CatalogType.RELATIVE_PUBLISHED,
                    CatalogType.SELF_CONTAINED
            ]:
                with self.subTest(title='Catalog {} [{}]'.format(catalog.id, catalog_type)):
                    self.do_test(catalog, catalog_type)
