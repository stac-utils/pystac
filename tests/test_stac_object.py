import json
import os
import unittest
import shutil
from tempfile import TemporaryDirectory
from datetime import datetime

from pystac import *
from tests.utils import (TestCases, RANDOM_GEOM, RANDOM_BBOX)

# TODO: Move this to catlog
class FullCopyTest(unittest.TestCase):
    def check_link(self, l, tag):
        if l.is_resolved():
            target_href = l.target.get_self_href()
        else:
            target_href = l.target
        self.assertTrue(tag in target_href)

    def check_item(self, i, tag):
        for l in i.links:
            self.check_link(l, tag)

    def check_catalog(self, c, tag):
        self.assertEqual(len(c.get_links('root')), 1)

        for l in c.links:
            self.check_link(l, tag)

        for child in c.get_children():
            self.check_catalog(child, tag)

        for item in c.get_items():
            self.check_item(item, tag)

    def test_full_copy_1(self):
        with TemporaryDirectory() as tmp_dir:
            cat = Catalog(id='test', description='test catalog')

            item = Item(id='test_item',
                        geometry=RANDOM_GEOM,
                        bbox=RANDOM_BBOX,
                        datetime=datetime.utcnow(),
                        properties={})

            cat.normalize_hrefs(os.path.join(tmp_dir, 'catalog-full-copy-1-source'))
            cat2 = cat.full_copy()
            cat2.normalize_hrefs(os.path.join(tmp_dir, 'catalog-full-copy-1-dest'))

            self.check_catalog(cat, 'source')
            self.check_catalog(cat2, 'dest')

    def test_full_copy_2(self):
        with TemporaryDirectory() as tmp_dir:
            cat = Catalog(id='test', description='test catalog')
            image_item = Item(id='Imagery',
                              geometry=RANDOM_GEOM,
                              bbox=RANDOM_BBOX,
                              datetime=datetime.utcnow(),
                              properties={})
            for key in ['ortho', 'dsm']:
                image_item.add_asset(key,
                                     href='some/{}.tif'.format(key),
                                     media_type=Asset.MEDIA_TYPE.GEOTIFF)

            label_item = LabelItem(id='Labels',
                                   geometry=RANDOM_GEOM,
                                   bbox=RANDOM_BBOX,
                                   datetime=datetime.utcnow(),
                                   properties={},
                                   label_description='labels',
                                   label_type='vector',
                                   label_property='label',
                                   label_classes=[LabelClasses(classes=['one', 'two'],
                                                               name='label')],
                                   label_task='classification')
            label_item.add_source(image_item, assets=['ortho'])

            cat.add_items([image_item, label_item])

            cat.normalize_hrefs(os.path.join(tmp_dir, 'catalog-full-copy-2-source'))
            cat.save()
            cat2 = cat.full_copy()
            cat2.normalize_hrefs(os.path.join(tmp_dir, 'catalog-full-copy-2-dest'))
            cat2.save()

            self.check_catalog(cat, 'source')
            self.check_catalog(cat2, 'dest')


    def test_full_copy_3(self):
        with TemporaryDirectory() as tmp_dir:
            root_cat = TestCases.test_case_1()
            root_cat.normalize_hrefs(os.path.join(tmp_dir, 'catalog-full-copy-3-source'))
            root_cat.save()
            cat2 = root_cat.full_copy()
            cat2.normalize_hrefs(os.path.join(tmp_dir, 'catalog-full-copy-3-dest'))
            cat2.save()

            self.check_catalog(root_cat, 'source')
            self.check_catalog(cat2, 'dest')
