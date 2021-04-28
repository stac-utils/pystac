import json
from typing import Any, Dict
import unittest
from copy import deepcopy

import pystac as ps
from pystac.validation import STACValidationError
from pystac.extensions.projection import ProjectionExtension, projection_ext
from pystac.utils import get_opt
from tests.utils import (TestCases, test_to_from_dict)

WKT2 = """
GEOGCS["WGS 84",
    DATUM["WGS_1984",
        SPHEROID["WGS 84",6378137,298.257223563,
            AUTHORITY["EPSG","7030"]],
        AUTHORITY["EPSG","6326"]],
    PRIMEM["Greenwich",0,
        AUTHORITY["EPSG","8901"]],
    UNIT["degree",0.0174532925199433,
        AUTHORITY["EPSG","9122"]],
    AXIS["Latitude",NORTH],
    AXIS["Longitude",EAST],
    AUTHORITY["EPSG","4326"]]
"""
PROJJSON = json.loads("""
{
    "$schema": "https://proj.org/schemas/v0.1/projjson.schema.json",
    "type": "GeographicCRS",
    "name": "WGS 84",
    "datum": {
        "type": "GeodeticReferenceFrame",
        "name": "World Geodetic System 1984",
        "ellipsoid": {
            "name": "WGS 84",
            "semi_major_axis": 6378137,
            "inverse_flattening": 298.257223563
        }
    },
    "coordinate_system": {
        "subtype": "ellipsoidal",
        "axis": [
        {
            "name": "Geodetic latitude",
            "abbreviation": "Lat",
            "direction": "north",
            "unit": "degree"
        },
        {
            "name": "Geodetic longitude",
            "abbreviation": "Lon",
            "direction": "east",
            "unit": "degree"
        }
        ]
    },
    "area": "World",
    "bbox": {
        "south_latitude": -90,
        "west_longitude": -180,
        "north_latitude": 90,
        "east_longitude": 180
    },
    "id": {
        "authority": "EPSG",
        "code": 4326
    }
}
""")


class ProjectionTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.example_uri = TestCases.get_path('data-files/projection/example-landsat8.json')

    def test_to_from_dict(self):
        with open(self.example_uri) as f:
            d = json.load(f)
        test_to_from_dict(self, ps.Item, d)

    def test_apply(self):
        item = next(iter(TestCases.test_case_2().get_all_items()))
        self.assertFalse(ProjectionExtension.has_extension(item))

        ProjectionExtension.add_to(item)
        projection_ext(item).apply(
            4326,
            wkt2=WKT2,
            projjson=PROJJSON,
            geometry=item.geometry,
            bbox=item.bbox,
            centroid={
                'lat': 0.0,
                'lon': 1.0
            },
            shape=[100, 100],
            transform=[30.0, 0.0, 224985.0, 0.0, -30.0, 6790215.0, 0.0, 0.0, 1.0])

    def test_partial_apply(self):
        proj_item = ps.Item.from_file(self.example_uri)

        projection_ext(proj_item).apply(epsg=1111)

        self.assertEqual(projection_ext(proj_item).epsg, 1111)
        proj_item.validate()

    def test_validate_proj(self):
        item = ps.Item.from_file(self.example_uri)
        item.validate()

    def test_epsg(self):
        proj_item = ps.Item.from_file(self.example_uri)

        # Get
        self.assertIn("proj:epsg", proj_item.properties)
        proj_epsg = projection_ext(proj_item).epsg
        self.assertEqual(proj_epsg, proj_item.properties['proj:epsg'])

        # Set
        projection_ext(proj_item).epsg = proj_epsg + 100
        self.assertEqual(proj_epsg + 100, proj_item.properties['proj:epsg'])

        # Get from Asset
        asset_no_prop = proj_item.assets['B1']
        asset_prop = proj_item.assets['B8']
        self.assertEqual(projection_ext(asset_no_prop).epsg,
                         projection_ext(proj_item).epsg)
        self.assertEqual(projection_ext(asset_prop).epsg, 9999)

        # Set to Asset
        projection_ext(asset_no_prop).epsg = 8888
        self.assertNotEqual(projection_ext(asset_no_prop).epsg,
                            projection_ext(proj_item).epsg)
        self.assertEqual(projection_ext(asset_no_prop).epsg, 8888)

        # Validate
        proj_item.validate

    def test_wkt2(self):
        proj_item = ps.Item.from_file(self.example_uri)

        # Get
        self.assertIn("proj:wkt2", proj_item.properties)
        proj_wkt2 = projection_ext(proj_item).wkt2
        self.assertEqual(proj_wkt2, proj_item.properties['proj:wkt2'])

        # Set
        projection_ext(proj_item).wkt2 = WKT2
        self.assertEqual(WKT2, proj_item.properties['proj:wkt2'])

        # Get from Asset
        asset_no_prop = proj_item.assets['B1']
        asset_prop = proj_item.assets['B8']
        self.assertEqual(projection_ext(asset_no_prop).wkt2,
                         projection_ext(proj_item).wkt2)
        self.assertTrue('TEST_TEXT' in get_opt(projection_ext(asset_prop).wkt2))

        # Set to Asset
        asset_value = "TEST TEXT 2"
        projection_ext(asset_no_prop).wkt2 = asset_value
        self.assertNotEqual(projection_ext(asset_no_prop).wkt2,
                            projection_ext(proj_item).wkt2)
        self.assertEqual(projection_ext(asset_no_prop).wkt2, asset_value)

        # Validate
        proj_item.validate()

    def test_projjson(self):
        proj_item = ps.Item.from_file(self.example_uri)

        # Get
        self.assertIn("proj:projjson", proj_item.properties)
        proj_projjson = projection_ext(proj_item).projjson
        self.assertEqual(proj_projjson, proj_item.properties['proj:projjson'])

        # Set
        projection_ext(proj_item).projjson = PROJJSON
        self.assertEqual(PROJJSON, proj_item.properties['proj:projjson'])

        # Get from Asset
        asset_no_prop = proj_item.assets['B1']
        asset_prop = proj_item.assets['B8']
        self.assertEqual(projection_ext(asset_no_prop).projjson,
                         projection_ext(proj_item).projjson)
        self.assertEqual(projection_ext(asset_prop).projjson['id']['code'], 9999)

        # Set to Asset
        asset_value = deepcopy(PROJJSON)
        asset_value['id']['code'] = 7777
        projection_ext(asset_no_prop).projjson = asset_value
        self.assertNotEqual(projection_ext(asset_no_prop).projjson,
                            projection_ext(proj_item).projjson)
        self.assertEqual(projection_ext(asset_no_prop).projjson['id']['code'], 7777)

        # Validate
        proj_item.validate()

        # Ensure setting bad projjson fails validation
        with self.assertRaises(STACValidationError):
            projection_ext(proj_item).projjson = {"bad": "data"}
            proj_item.validate()

    def test_geometry(self):
        proj_item = ps.Item.from_file(self.example_uri)

        # Get
        self.assertIn("proj:geometry", proj_item.properties)
        proj_geometry = projection_ext(proj_item).geometry
        self.assertEqual(proj_geometry, proj_item.properties['proj:geometry'])

        # Set
        projection_ext(proj_item).geometry = proj_item.geometry
        self.assertEqual(proj_item.geometry, proj_item.properties['proj:geometry'])

        # Get from Asset
        asset_no_prop = proj_item.assets['B1']
        asset_prop = proj_item.assets['B8']
        self.assertEqual(projection_ext(asset_no_prop).geometry,
                         projection_ext(proj_item).geometry)
        self.assertEqual(
            projection_ext(asset_prop).geometry['coordinates'][0][0], [0.0, 0.0])

        # Set to Asset
        asset_value: Dict[str, Any] = {'type': 'Point', 'coordinates': [1.0, 2.0]}
        projection_ext(asset_no_prop).geometry = asset_value
        self.assertNotEqual(projection_ext(asset_no_prop).geometry,
                            projection_ext(proj_item).geometry)
        self.assertEqual(projection_ext(asset_no_prop).geometry, asset_value)

        # Validate
        proj_item.validate()

        # Ensure setting bad geometry fails validation
        with self.assertRaises(STACValidationError):
            projection_ext(proj_item).geometry = {"bad": "data"}
            proj_item.validate()

    def test_bbox(self):
        proj_item = ps.Item.from_file(self.example_uri)

        # Get
        self.assertIn("proj:bbox", proj_item.properties)
        proj_bbox = projection_ext(proj_item).bbox
        self.assertEqual(proj_bbox, proj_item.properties['proj:bbox'])

        # Set
        projection_ext(proj_item).bbox = [1.0, 2.0, 3.0, 4.0]
        self.assertEqual(proj_item.properties['proj:bbox'], [1.0, 2.0, 3.0, 4.0])

        # Get from Asset
        asset_no_prop = proj_item.assets['B1']
        asset_prop = proj_item.assets['B8']
        self.assertEqual(projection_ext(asset_no_prop).bbox,
                         projection_ext(proj_item).bbox)
        self.assertEqual(projection_ext(asset_prop).bbox, [1.0, 2.0, 3.0, 4.0])

        # Set to Asset
        asset_value = [10.0, 20.0, 30.0, 40.0]
        projection_ext(asset_no_prop).bbox = asset_value
        self.assertNotEqual(projection_ext(asset_no_prop).bbox,
                            projection_ext(proj_item).bbox)
        self.assertEqual(projection_ext(asset_no_prop).bbox, asset_value)

        # Validate
        proj_item.validate()

    def test_centroid(self):
        proj_item = ps.Item.from_file(self.example_uri)

        # Get
        self.assertIn("proj:centroid", proj_item.properties)
        proj_centroid = projection_ext(proj_item).centroid
        self.assertEqual(proj_centroid, proj_item.properties['proj:centroid'])

        # Set
        new_val = {'lat': 2.0, 'lon': 3.0}
        projection_ext(proj_item).centroid = new_val
        self.assertEqual(proj_item.properties['proj:centroid'], new_val)

        # Get from Asset
        asset_no_prop = proj_item.assets['B1']
        asset_prop = proj_item.assets['B8']
        self.assertEqual(projection_ext(asset_no_prop).centroid,
                         projection_ext(proj_item).centroid)
        self.assertEqual(projection_ext(asset_prop).centroid, {
            "lat": 0.5,
            "lon": 0.3
        })

        # Set to Asset
        asset_value = {"lat": 1.5, "lon": 1.3}
        projection_ext(asset_no_prop).centroid  = asset_value
        self.assertNotEqual(projection_ext(asset_no_prop).centroid,
                            projection_ext(proj_item).centroid)
        self.assertEqual(projection_ext(asset_no_prop).centroid, asset_value)

        # Validate
        proj_item.validate()

        # Ensure setting bad centroid fails validation
        with self.assertRaises(STACValidationError):
            projection_ext(proj_item).centroid = {'lat': 2.0, 'lng': 3.0}
            proj_item.validate()

    def test_shape(self):
        proj_item = ps.Item.from_file(self.example_uri)

        # Get
        self.assertIn("proj:shape", proj_item.properties)
        proj_shape = projection_ext(proj_item).shape
        self.assertEqual(proj_shape, proj_item.properties['proj:shape'])

        # Set
        new_val = [100, 200]
        projection_ext(proj_item).shape = new_val
        self.assertEqual(proj_item.properties['proj:shape'], new_val)

        # Get from Asset
        asset_no_prop = proj_item.assets['B1']
        asset_prop = proj_item.assets['B8']
        self.assertEqual(projection_ext(asset_no_prop).shape,
                         projection_ext(proj_item).shape)
        self.assertEqual(projection_ext(asset_prop).shape, [16781, 16621])

        # Set to Asset
        asset_value = [1, 2]
        projection_ext(asset_no_prop).shape = asset_value
        self.assertNotEqual(projection_ext(asset_no_prop).shape,
                            projection_ext(proj_item).shape)
        self.assertEqual(projection_ext(asset_no_prop).shape, asset_value)

        # Validate
        proj_item.validate()

    def test_transform(self):
        proj_item = ps.Item.from_file(self.example_uri)

        # Get
        self.assertIn("proj:transform", proj_item.properties)
        proj_transform = projection_ext(proj_item).transform
        self.assertEqual(proj_transform, proj_item.properties['proj:transform'])

        # Set
        new_val = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        projection_ext(proj_item).transform = new_val
        self.assertEqual(proj_item.properties['proj:transform'], new_val)

        # Get from Asset
        asset_no_prop = proj_item.assets['B1']
        asset_prop = proj_item.assets['B8']
        self.assertEqual(projection_ext(asset_no_prop).transform,
                         projection_ext(proj_item).transform)
        self.assertEqual(projection_ext(asset_prop).transform,
                         [15.0, 0.0, 224992.5, 0.0, -15.0, 6790207.5, 0.0, 0.0, 1.0])

        # Set to Asset
        asset_value = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
        projection_ext(asset_no_prop).transform = asset_value
        self.assertNotEqual(projection_ext(asset_no_prop).transform,
                            projection_ext(proj_item).transform)
        self.assertEqual(projection_ext(asset_no_prop).transform, asset_value)

        # Validate
        proj_item.validate()
