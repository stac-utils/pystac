import unittest
from tempfile import TemporaryDirectory

import pystac
from pystac import Collection, CatalogType, HIERARCHICAL_LINKS
from pystac.utils import is_absolute_href, make_absolute_href, make_relative_href
from pystac.validation import validate_dict

from tests.utils import TestCases


class STACWritingTest(unittest.TestCase):
    """Tests writing STACs, using JSON Schema validation,
    and ensure that links are correctly set to relative or absolute.
    """

    def validate_catalog(self, catalog: pystac.Catalog):
        catalog.validate()
        validated_count = 1

        for child in catalog.get_children():
            validated_count += self.validate_catalog(child)

        for item in catalog.get_items():
            item.validate()
            validated_count += 1

        return validated_count

    def validate_file(self, path: str, object_type: str):
        d = pystac.StacIO.default().read_json(path)
        return validate_dict(d, pystac.STACObjectType(object_type))

    def validate_link_types(self, root_href: str, catalog_type: pystac.CatalogType):
        def validate_asset_href_type(item: pystac.Item, item_href: str):
            for asset in item.assets.values():
                if not is_absolute_href(asset.href):
                    is_valid = not is_absolute_href(asset.href)
                    if not is_valid:
                        # If the item href and asset href don't share
                        # the same root, the asset href must be absolute
                        rel_href = make_relative_href(asset.href, item_href)
                        self.assertEqual(asset.href, rel_href)
                    else:
                        self.assertTrue(is_valid)

        def validate_item_link_type(
            href: str, link_type: str, should_include_self: bool
        ):
            item_dict = pystac.StacIO.default().read_json(href)
            item = pystac.Item.from_file(href)
            rel_links = (
                HIERARCHICAL_LINKS
                + pystac.EXTENSION_HOOKS.get_extended_object_links(item)
            )
            for link in item.get_links():
                if not link.rel == "self":
                    if link_type == "RELATIVE" and link.rel in rel_links:
                        self.assertFalse(is_absolute_href(link.href))
                    else:
                        self.assertTrue(is_absolute_href(link.href))

            validate_asset_href_type(item, href)

            rels = set([link["rel"] for link in item_dict["links"]])
            self.assertEqual("self" in rels, should_include_self)

        def validate_catalog_link_type(
            href: str, link_type: str, should_include_self: bool
        ):
            cat_dict = pystac.StacIO.default().read_json(href)
            cat = pystac.Catalog.from_file(href)

            rels = set([link["rel"] for link in cat_dict["links"]])
            self.assertEqual("self" in rels, should_include_self)

            for child_link in cat.get_child_links():
                child_href = make_absolute_href(child_link.href, href)
                validate_catalog_link_type(
                    child_href,
                    link_type,
                    catalog_type == CatalogType.ABSOLUTE_PUBLISHED,
                )

            for item_link in cat.get_item_links():
                item_href = make_absolute_href(item_link.href, href)
                validate_item_link_type(
                    item_href, link_type, catalog_type == CatalogType.ABSOLUTE_PUBLISHED
                )

        link_type = "RELATIVE"
        if catalog_type == CatalogType.ABSOLUTE_PUBLISHED:
            link_type = "ABSOLUTE"

        root_should_include_href = catalog_type in [
            CatalogType.ABSOLUTE_PUBLISHED,
            CatalogType.RELATIVE_PUBLISHED,
        ]

        validate_catalog_link_type(root_href, link_type, root_should_include_href)

    def do_test(self, catalog: pystac.Catalog, catalog_type: pystac.CatalogType):
        with TemporaryDirectory() as tmp_dir:
            catalog.normalize_hrefs(tmp_dir)
            self.validate_catalog(catalog)

            catalog.save(catalog_type=catalog_type)

            root_href = catalog.self_href
            self.validate_link_types(root_href, catalog_type)

            for parent, _, items in catalog.walk():
                if issubclass(type(parent), Collection):
                    stac_object_type = pystac.STACObjectType.COLLECTION
                else:
                    stac_object_type = pystac.STACObjectType.CATALOG
                self.validate_file(parent.self_href, stac_object_type)

                for item in items:
                    self.validate_file(item.self_href, pystac.STACObjectType.ITEM)

    def test_testcases(self):
        for catalog in TestCases.all_test_catalogs():
            catalog = catalog.full_copy()
            ctypes = [
                CatalogType.ABSOLUTE_PUBLISHED,
                CatalogType.RELATIVE_PUBLISHED,
                CatalogType.SELF_CONTAINED,
            ]
            for catalog_type in ctypes:
                with self.subTest(
                    title="Catalog {} [{}]".format(catalog.id, catalog_type)
                ):
                    self.do_test(catalog, catalog_type)
