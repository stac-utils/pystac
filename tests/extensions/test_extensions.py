import unittest

import pystac
from pystac import (Catalog, Collection, Item)
from pystac.extensions.base import (CatalogExtension, CollectionExtension, ItemExtension,
                                    ExtensionDefinition, ExtendedObject, ExtensionError)
from pystac.stac_object import ExtensionIndex

from tests.utils import TestCases


class TestCatalogExt(CatalogExtension):
    def __init__(self, cat):
        self.cat = cat

    @property
    def test_id(self):
        return self.cat.id

    @classmethod
    def from_catalog(cls, cat):
        return TestCatalogExt(cat)

    @classmethod
    def _object_links(cls):
        return []


class TestCollectionExt(CollectionExtension):
    def __init__(self, col):
        self.col = col

    @property
    def xmin(self):
        return self.col.extent.spatial.bboxes[0][0]

    @classmethod
    def from_collection(cls, col):
        return TestCollectionExt(col)

    @classmethod
    def _object_links(cls):
        return []


class TestItemExt(ItemExtension):
    def __init__(self, item):
        self.item = item

    @property
    def asset_keys(self):
        return set(self.item.assets)

    @classmethod
    def from_item(cls, item):
        return TestItemExt(item)

    @classmethod
    def _object_links(cls):
        return []


class ExtensionsTest(unittest.TestCase):
    def test_can_add_custom_extension(self):
        prev_extensions = pystac.STAC_EXTENSIONS.get_registered_extensions()

        pystac.STAC_EXTENSIONS.add_extension(
            ExtensionDefinition("test", [
                ExtendedObject(Catalog, TestCatalogExt),
                ExtendedObject(Collection, TestCollectionExt),
                ExtendedObject(Item, TestItemExt)
            ]))

        try:
            cat = TestCases.test_case_2()
            col = cat.get_child('1a8c1632-fa91-4a62-b33e-3a87c2ebdf16')
            item = next(cat.get_all_items())

            cat.ext.enable("test")
            col.ext.enable("test")
            item.ext.enable("test")

            self.assertEqual(cat.ext.test.test_id, cat.id)
            self.assertEqual(col.ext.test.xmin, col.extent.spatial.bboxes[0][0])
            self.assertEqual(item.ext.test.asset_keys, set(item.assets))

        finally:
            pystac.STAC_EXTENSIONS.remove_extension("test")

        self.assertFalse(pystac.STAC_EXTENSIONS.is_registered_extension("test"))
        self.assertEqual(pystac.STAC_EXTENSIONS.get_registered_extensions(), prev_extensions)

    def test_getattribute_overload(self):
        catalog = Catalog(id='test', description='test')
        self.assertEqual(ExtensionIndex.__name__, 'ExtensionIndex')
        self.assertRaises(ExtensionError, catalog.ext.__getattr__, 'foo')
        self.assertRaises(ExtensionError, catalog.ext.__getattr__, 'eo')
        catalog.ext.enable('single-file-stac')
        self.assertTrue(catalog.ext.__getattr__('single-file-stac'),
                        pystac.extensions.single_file_stac.SingleFileSTACCatalogExt)
