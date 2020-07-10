import unittest

import pystac
from tests.utils import (SchemaValidator, TestCases, STACValidationError)


class CommonsTest(unittest.TestCase):
    def setUp(self):
        self.validator = SchemaValidator()
        self.maxDiff = None

    def test_reads_common_metadata_if_enabled(self):
        # Test reading from collection
        collection = pystac.read_file(
            TestCases.get_path('data-files/commons/example-collection-with-commons.json'))

        self.assertTrue(collection.ext.implements(pystac.Extensions.COMMONS))

        item = collection.get_item("item-with")

        self.assertTrue(item.ext.implements(pystac.Extensions.COMMONS))
        self.assertTrue(item.ext.implements(pystac.Extensions.EO))

        self.validator.validate_object(item)

        # Test reading item directly

        item2 = pystac.read_file(
            TestCases.get_path('data-files/commons/example-item-with-commons.json'))

        self.assertTrue(item2.ext.implements(pystac.Extensions.COMMONS))
        self.assertTrue(item2.ext.implements(pystac.Extensions.EO))

        self.validator.validate_object(item2)

    def test_doesnt_common_metadata_if_not_enabled(self):
        # Test reading from collection
        collection = pystac.read_file(
            TestCases.get_path('data-files/commons/example-collection-without-commons.json'))

        self.assertFalse(collection.ext.implements(pystac.Extensions.COMMONS))

        item = collection.get_item("item-without")

        self.assertFalse(item.ext.implements(pystac.Extensions.COMMONS))
        self.assertTrue(item.ext.implements(pystac.Extensions.EO))

        # Should fail since required EO properties weren't inherited.
        with self.assertRaises(STACValidationError):
            self.validator.validate_object(item)

        # Test reading item directly

        item2 = pystac.read_file(
            TestCases.get_path('data-files/commons/example-item-without-commons.json'))

        self.assertFalse(item2.ext.implements(pystac.Extensions.COMMONS))
        self.assertTrue(item2.ext.implements(pystac.Extensions.EO))

        with self.assertRaises(STACValidationError):
            self.validator.validate_object(item2)
