import json
from copy import deepcopy
from typing import Any

import pytest

import pystac
from pystac import ExtensionTypeError, Item
from pystac.errors import ExtensionNotImplemented
from pystac.extensions.projection import ProjectionExtension
from pystac.utils import get_opt
from tests.utils import TestCases, assert_to_from_dict

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
PROJJSON = json.loads(
    """
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
"""
)


@pytest.fixture
def example_uri() -> str:
    return TestCases.get_path("data-files/projection/example-landsat8.json")


@pytest.fixture
def example_summaries_uri() -> str:
    return TestCases.get_path("data-files/projection/collection-with-summaries.json")


def test_to_from_dict(example_uri: str) -> None:
    with open(example_uri) as f:
        d = json.load(f)
    assert_to_from_dict(pystac.Item, d)


def test_apply() -> None:
    item = next(TestCases.case_2().get_items(recursive=True))
    assert not ProjectionExtension.has_extension(item)

    ProjectionExtension.add_to(item)
    ProjectionExtension.ext(item).apply(
        epsg=4326,
        wkt2=WKT2,
        projjson=PROJJSON,
        geometry=item.geometry,
        bbox=item.bbox,
        centroid={"lat": 0.0, "lon": 1.0},
        shape=[100, 100],
        transform=[30.0, 0.0, 224985.0, 0.0, -30.0, 6790215.0, 0.0, 0.0, 1.0],
    )


@pytest.mark.vcr()
def test_partial_apply(example_uri: str) -> None:
    proj_item = pystac.Item.from_file(example_uri)

    ProjectionExtension.ext(proj_item).apply(epsg=1111)

    assert ProjectionExtension.ext(proj_item).epsg == 1111
    proj_item.validate()


@pytest.mark.vcr()
def test_validate_proj(example_uri: str) -> None:
    item = pystac.Item.from_file(example_uri)
    item.validate()


@pytest.mark.vcr()
def test_epsg(example_uri: str) -> None:
    proj_item = pystac.Item.from_file(example_uri)

    # Get
    assert "proj:epsg" not in proj_item.properties
    assert "proj:code" in proj_item.properties
    proj_epsg = ProjectionExtension.ext(proj_item).epsg
    assert f"EPSG:{proj_epsg}" == proj_item.properties["proj:code"]

    # Set
    assert proj_epsg is not None
    ProjectionExtension.ext(proj_item).epsg = proj_epsg + 100
    assert f"EPSG:{proj_epsg + 100}" == proj_item.properties["proj:code"]

    # Get from Asset
    asset_no_prop = proj_item.assets["B1"]
    asset_prop = proj_item.assets["B8"]
    assert (
        ProjectionExtension.ext(asset_no_prop).epsg
        == ProjectionExtension.ext(proj_item).epsg
    )
    assert ProjectionExtension.ext(asset_prop).epsg == 9999

    # Set to Asset
    ProjectionExtension.ext(asset_no_prop).epsg = 8888
    assert (
        ProjectionExtension.ext(asset_no_prop).epsg
        != ProjectionExtension.ext(proj_item).epsg
    )
    assert ProjectionExtension.ext(asset_no_prop).epsg == 8888

    # Validate
    proj_item.validate()


def test_optional_epsg() -> None:
    example_uri = TestCases.get_path("data-files/projection/optional-epsg.json")
    proj_item = pystac.Item.from_file(example_uri)

    # No proj info on item
    assert "proj:epsg" not in proj_item.properties
    assert "proj:code" not in proj_item.properties

    # Some proj info on assets
    asset_no_prop = proj_item.assets["metadata"]
    assert ProjectionExtension.ext(asset_no_prop).epsg is None

    asset_prop = proj_item.assets["visual"]
    assert ProjectionExtension.ext(asset_prop).epsg == 32618


@pytest.mark.vcr()
def test_wkt2(example_uri: str) -> None:
    proj_item = pystac.Item.from_file(example_uri)

    # Get
    assert "proj:wkt2" in proj_item.properties
    proj_wkt2 = ProjectionExtension.ext(proj_item).wkt2
    assert proj_wkt2 == proj_item.properties["proj:wkt2"]

    # Set
    ProjectionExtension.ext(proj_item).wkt2 = WKT2
    assert WKT2 == proj_item.properties["proj:wkt2"]

    # Get from Asset
    asset_no_prop = proj_item.assets["B1"]
    asset_prop = proj_item.assets["B8"]
    assert (
        ProjectionExtension.ext(asset_no_prop).wkt2
        == ProjectionExtension.ext(proj_item).wkt2
    )
    assert "TEST_TEXT" in get_opt(ProjectionExtension.ext(asset_prop).wkt2)

    # Set to Asset
    asset_value = "TEST TEXT 2"
    ProjectionExtension.ext(asset_no_prop).wkt2 = asset_value
    assert (
        ProjectionExtension.ext(asset_no_prop).wkt2
        != ProjectionExtension.ext(proj_item).wkt2
    )
    assert ProjectionExtension.ext(asset_no_prop).wkt2 == asset_value

    # Validate
    proj_item.validate()


@pytest.mark.vcr()
def test_projjson(example_uri: str) -> None:
    proj_item = pystac.Item.from_file(example_uri)

    # Get
    assert "proj:projjson" in proj_item.properties
    proj_projjson = ProjectionExtension.ext(proj_item).projjson
    assert proj_projjson == proj_item.properties["proj:projjson"]

    # Set
    ProjectionExtension.ext(proj_item).projjson = PROJJSON
    assert PROJJSON == proj_item.properties["proj:projjson"]

    # Get from Asset
    asset_no_prop = proj_item.assets["B1"]
    asset_prop = proj_item.assets["B8"]
    assert (
        ProjectionExtension.ext(asset_no_prop).projjson
        == ProjectionExtension.ext(proj_item).projjson
    )
    asset_prop_json = ProjectionExtension.ext(asset_prop).projjson
    assert asset_prop_json is not None
    assert asset_prop_json["id"]["code"] == 9999

    # Set to Asset
    asset_value = deepcopy(PROJJSON)
    asset_value["id"]["code"] = 7777
    ProjectionExtension.ext(asset_no_prop).projjson = asset_value
    assert (
        ProjectionExtension.ext(asset_no_prop).projjson
        != ProjectionExtension.ext(proj_item).projjson
    )
    asset_no_prop_json = ProjectionExtension.ext(asset_no_prop).projjson
    assert asset_no_prop_json is not None
    assert asset_no_prop_json["id"]["code"] == 7777

    # Validate
    proj_item.validate()

    # Ensure setting bad projjson fails validation
    with pytest.raises(pystac.STACValidationError):
        ProjectionExtension.ext(proj_item).projjson = {"bad": "data"}
        proj_item.validate()


def test_crs_string(example_uri: str) -> None:
    item = pystac.Item.from_file(example_uri)
    ProjectionExtension.remove_from(item)
    for key in list(item.properties.keys()):
        if key.startswith("proj:"):
            item.properties.pop(key)
    assert item.properties.get("proj:code") is None
    assert item.properties.get("proj:epsg") is None
    assert item.properties.get("proj:wkt2") is None
    assert item.properties.get("proj:projjson") is None

    projection = ProjectionExtension.ext(item, add_if_missing=True)
    assert projection.crs_string is None

    projection.projjson = PROJJSON
    assert projection.crs_string == json.dumps(PROJJSON)

    projection.wkt2 = WKT2
    assert projection.crs_string == WKT2

    projection.epsg = 4326
    assert projection.crs_string == "EPSG:4326"

    projection.code = "IAU_2015:49900"
    assert projection.crs_string == "IAU_2015:49900"


@pytest.mark.vcr()
def test_geometry(example_uri: str) -> None:
    proj_item = pystac.Item.from_file(example_uri)

    # Get
    assert "proj:geometry" in proj_item.properties
    proj_geometry = ProjectionExtension.ext(proj_item).geometry
    assert proj_geometry == proj_item.properties["proj:geometry"]

    # Set
    ProjectionExtension.ext(proj_item).geometry = proj_item.geometry
    assert proj_item.geometry == proj_item.properties["proj:geometry"]

    # Get from Asset
    asset_no_prop = proj_item.assets["B1"]
    asset_prop = proj_item.assets["B8"]
    assert (
        ProjectionExtension.ext(asset_no_prop).geometry
        == ProjectionExtension.ext(proj_item).geometry
    )
    asset_prop_geometry = ProjectionExtension.ext(asset_prop).geometry
    assert asset_prop_geometry is not None
    assert asset_prop_geometry["coordinates"][0][0], [0.0 == 0.0]

    # Set to Asset
    asset_value: dict[str, Any] = {"type": "Point", "coordinates": [1.0, 2.0]}
    ProjectionExtension.ext(asset_no_prop).geometry = asset_value
    assert (
        ProjectionExtension.ext(asset_no_prop).geometry
        != ProjectionExtension.ext(proj_item).geometry
    )
    assert ProjectionExtension.ext(asset_no_prop).geometry == asset_value

    # Validate
    proj_item.validate()

    # Ensure setting bad geometry fails validation
    with pytest.raises(pystac.STACValidationError):
        ProjectionExtension.ext(proj_item).geometry = {"bad": "data"}
        proj_item.validate()


@pytest.mark.vcr()
def test_bbox(example_uri: str) -> None:
    proj_item = pystac.Item.from_file(example_uri)

    # Get
    assert "proj:bbox" in proj_item.properties
    proj_bbox = ProjectionExtension.ext(proj_item).bbox
    assert proj_bbox == proj_item.properties["proj:bbox"]

    # Set
    ProjectionExtension.ext(proj_item).bbox = [1.0, 2.0, 3.0, 4.0]
    assert proj_item.properties["proj:bbox"] == [1.0, 2.0, 3.0, 4.0]

    # Get from Asset
    asset_no_prop = proj_item.assets["B1"]
    asset_prop = proj_item.assets["B8"]
    assert (
        ProjectionExtension.ext(asset_no_prop).bbox
        == ProjectionExtension.ext(proj_item).bbox
    )
    assert ProjectionExtension.ext(asset_prop).bbox == [1.0, 2.0, 3.0, 4.0]

    # Set to Asset
    asset_value = [10.0, 20.0, 30.0, 40.0]
    ProjectionExtension.ext(asset_no_prop).bbox = asset_value
    assert (
        ProjectionExtension.ext(asset_no_prop).bbox
        != ProjectionExtension.ext(proj_item).bbox
    )
    assert ProjectionExtension.ext(asset_no_prop).bbox == asset_value

    # Validate
    proj_item.validate()


@pytest.mark.vcr()
def test_centroid(example_uri: str) -> None:
    proj_item = pystac.Item.from_file(example_uri)

    # Get
    assert "proj:centroid" in proj_item.properties
    proj_centroid = ProjectionExtension.ext(proj_item).centroid
    assert proj_centroid == proj_item.properties["proj:centroid"]

    # Set
    new_val = {"lat": 2.0, "lon": 3.0}
    ProjectionExtension.ext(proj_item).centroid = new_val
    assert proj_item.properties["proj:centroid"] == new_val

    # Get from Asset
    asset_no_prop = proj_item.assets["B1"]
    asset_prop = proj_item.assets["B8"]
    assert (
        ProjectionExtension.ext(asset_no_prop).centroid
        == ProjectionExtension.ext(proj_item).centroid
    )
    assert ProjectionExtension.ext(asset_prop).centroid == {"lat": 0.5, "lon": 0.3}

    # Set to Asset
    asset_value = {"lat": 1.5, "lon": 1.3}
    ProjectionExtension.ext(asset_no_prop).centroid = asset_value
    assert (
        ProjectionExtension.ext(asset_no_prop).centroid
        != ProjectionExtension.ext(proj_item).centroid
    )
    assert ProjectionExtension.ext(asset_no_prop).centroid == asset_value

    # Validate
    proj_item.validate()

    # Ensure setting bad centroid fails validation
    with pytest.raises(pystac.STACValidationError):
        ProjectionExtension.ext(proj_item).centroid = {"lat": 2.0, "lng": 3.0}
        proj_item.validate()


@pytest.mark.vcr()
def test_shape(example_uri: str) -> None:
    proj_item = pystac.Item.from_file(example_uri)

    # Get
    assert "proj:shape" in proj_item.properties
    proj_shape = ProjectionExtension.ext(proj_item).shape
    assert proj_shape == proj_item.properties["proj:shape"]

    # Set
    new_val = [100, 200]
    ProjectionExtension.ext(proj_item).shape = new_val
    assert proj_item.properties["proj:shape"] == new_val

    # Get from Asset
    asset_no_prop = proj_item.assets["B1"]
    asset_prop = proj_item.assets["B8"]
    assert (
        ProjectionExtension.ext(asset_no_prop).shape
        == ProjectionExtension.ext(proj_item).shape
    )
    assert ProjectionExtension.ext(asset_prop).shape == [16781, 16621]

    # Set to Asset
    asset_value = [1, 2]
    ProjectionExtension.ext(asset_no_prop).shape = asset_value
    assert (
        ProjectionExtension.ext(asset_no_prop).shape
        != ProjectionExtension.ext(proj_item).shape
    )
    assert ProjectionExtension.ext(asset_no_prop).shape == asset_value

    # Validate
    proj_item.validate()


@pytest.mark.vcr()
def test_transform(example_uri: str) -> None:
    proj_item = pystac.Item.from_file(example_uri)

    # Get
    assert "proj:transform" in proj_item.properties
    proj_transform = ProjectionExtension.ext(proj_item).transform
    assert proj_transform == proj_item.properties["proj:transform"]

    # Set
    new_val = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    ProjectionExtension.ext(proj_item).transform = new_val
    assert proj_item.properties["proj:transform"] == new_val

    # Get from Asset
    asset_no_prop = proj_item.assets["B1"]
    asset_prop = proj_item.assets["B8"]
    assert (
        ProjectionExtension.ext(asset_no_prop).transform
        == ProjectionExtension.ext(proj_item).transform
    )
    assert ProjectionExtension.ext(asset_prop).transform == [
        15.0,
        0.0,
        224992.5,
        0.0,
        -15.0,
        6790207.5,
        0.0,
        0.0,
        1.0,
    ]

    # Set to Asset
    asset_value = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
    ProjectionExtension.ext(asset_no_prop).transform = asset_value
    assert (
        ProjectionExtension.ext(asset_no_prop).transform
        != ProjectionExtension.ext(proj_item).transform
    )
    assert ProjectionExtension.ext(asset_no_prop).transform == asset_value

    # Validate
    proj_item.validate()


def test_extension_not_implemented(example_uri: str) -> None:
    # Should raise exception if Item does not include extension URI
    item = pystac.Item.from_file(example_uri)
    item.stac_extensions.remove(ProjectionExtension.get_schema_uri())

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = ProjectionExtension.ext(item)

    # Should raise exception if owning Item does not include extension URI
    asset = item.assets["B8"]

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = ProjectionExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = ProjectionExtension.ext(ownerless_asset)


def test_item_ext_add_to(example_uri: str) -> None:
    item = pystac.Item.from_file(example_uri)
    item.stac_extensions.remove(ProjectionExtension.get_schema_uri())
    assert ProjectionExtension.get_schema_uri() not in item.stac_extensions

    _ = ProjectionExtension.ext(item, add_if_missing=True)

    assert ProjectionExtension.get_schema_uri() in item.stac_extensions


def test_asset_ext_add_to(example_uri: str) -> None:
    item = pystac.Item.from_file(example_uri)
    item.stac_extensions.remove(ProjectionExtension.get_schema_uri())
    assert ProjectionExtension.get_schema_uri() not in item.stac_extensions
    asset = item.assets["B8"]

    _ = ProjectionExtension.ext(asset, add_if_missing=True)

    assert ProjectionExtension.get_schema_uri() in item.stac_extensions


def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError,
        match=r"^ProjectionExtension does not apply to type 'object'$",
    ):
        # intentionally calling this wrong so ---vvv
        ProjectionExtension.ext(object())  # type: ignore


def test_get_summaries(example_summaries_uri: str) -> None:
    col = pystac.Collection.from_file(example_summaries_uri)
    proj_summaries = ProjectionExtension.summaries(col)

    # Get

    epsg_summaries = proj_summaries.epsg
    assert epsg_summaries is not None
    assert epsg_summaries == [32614]


def test_set_summaries(example_summaries_uri: str) -> None:
    col = pystac.Collection.from_file(example_summaries_uri)
    proj_summaries = ProjectionExtension.summaries(col)

    # Set

    proj_summaries.epsg = [4326]

    col_dict = col.to_dict()
    assert col_dict["summaries"]["proj:code"] == ["EPSG:4326"]


def test_summaries_adds_uri(example_summaries_uri: str) -> None:
    col = pystac.Collection.from_file(example_summaries_uri)
    col.stac_extensions = []
    with pytest.raises(
        pystac.ExtensionNotImplemented, match="Extension 'proj' is not implemented"
    ):
        ProjectionExtension.summaries(col, add_if_missing=False)

    ProjectionExtension.summaries(col, True)

    assert ProjectionExtension.get_schema_uri() in col.stac_extensions

    ProjectionExtension.remove_from(col)
    assert ProjectionExtension.get_schema_uri() not in col.stac_extensions


def test_no_args_for_extension_class(item: Item) -> None:
    item.ext.add("proj")
    with pytest.raises(TypeError, match="takes 1 positional argument but 2 were given"):
        item.ext.proj.apply(32614)  # type:ignore


def test_set_both_code_and_epsg(item: Item) -> None:
    item.ext.add("proj")
    with pytest.raises(KeyError, match="Only one of the options"):
        item.ext.proj.apply(epsg=32614, code="EPSG:32614")


@pytest.mark.vcr()
def test_get_set_code(projection_landsat8_item: Item) -> None:
    proj_item = projection_landsat8_item
    assert proj_item.ext.proj.code == proj_item.properties["proj:code"]
    assert proj_item.ext.proj.epsg == 32614

    proj_item.ext.proj.code = "IAU_2015:30100"
    assert proj_item.ext.proj.epsg is None
    assert proj_item.properties["proj:code"] == "IAU_2015:30100"


def test_migrate() -> None:
    old = "https://stac-extensions.github.io/projection/v1.1.0/schema.json"
    current = "https://stac-extensions.github.io/projection/v2.0.0/schema.json"

    path = TestCases.get_path("data-files/projection/example-with-version-1.1.json")
    item = Item.from_file(path)

    assert old not in item.stac_extensions
    assert current in item.stac_extensions

    assert item.ext.proj.epsg == 32614
    assert item.ext.proj.code == "EPSG:32614"


def test_older_extension_version(projection_landsat8_item: Item) -> None:
    old = "https://stac-extensions.github.io/projection/v1.0.0/schema.json"
    current = "https://stac-extensions.github.io/projection/v2.0.0/schema.json"

    stac_extensions = set(projection_landsat8_item.stac_extensions)
    stac_extensions.remove(current)
    stac_extensions.add(old)
    item_as_dict = projection_landsat8_item.to_dict(
        include_self_link=False, transform_hrefs=False
    )
    item_as_dict["stac_extensions"] = list(stac_extensions)
    item = Item.from_dict(item_as_dict, migrate=False)
    assert ProjectionExtension.has_extension(item)
    assert old in item.stac_extensions

    migrated_item = pystac.Item.from_dict(item_as_dict, migrate=True)
    assert ProjectionExtension.has_extension(migrated_item)
    assert current in migrated_item.stac_extensions


def test_newer_extension_version(projection_landsat8_item: Item) -> None:
    new = "https://stac-extensions.github.io/projection/v2.1.0/schema.json"
    current = "https://stac-extensions.github.io/projection/v2.0.0/schema.json"

    stac_extensions = set(projection_landsat8_item.stac_extensions)
    stac_extensions.remove(current)
    stac_extensions.add(new)
    item_as_dict = projection_landsat8_item.to_dict(
        include_self_link=False, transform_hrefs=False
    )
    item_as_dict["stac_extensions"] = list(stac_extensions)
    item = Item.from_dict(item_as_dict)
    assert ProjectionExtension.has_extension(item)
    assert new in item.stac_extensions

    migrated_item = pystac.Item.from_dict(item_as_dict, migrate=True)
    assert ProjectionExtension.has_extension(migrated_item)
    assert new in migrated_item.stac_extensions


def test_ext_syntax(projection_landsat8_item: pystac.Item) -> None:
    ext_item = projection_landsat8_item
    assert ext_item.ext.proj.epsg == 32614
    assert ext_item.assets["B1"].ext.proj.epsg == 32614


def test_ext_syntax_remove(projection_landsat8_item: pystac.Item) -> None:
    ext_item = projection_landsat8_item
    ext_item.ext.remove("proj")
    with pytest.raises(ExtensionNotImplemented):
        ext_item.ext.proj


def test_ext_syntax_add(item: pystac.Item) -> None:
    item.ext.add("proj")
    assert isinstance(item.ext.proj, ProjectionExtension)


def test_v1_from_dict() -> None:
    with open(
        TestCases.get_path("data-files/projection/example-with-version-1.1.json")
    ) as f:
        data = json.load(f)
    item = pystac.Item.from_dict(data, migrate=False)
    assert item.ext.proj.epsg is not None
    assert item.ext.proj.crs_string is not None


def test_v1_crs_string() -> None:
    with open(TestCases.get_path("data-files/projection/another-1.1.json")) as f:
        data = json.load(f)
    item = pystac.Item.from_dict(data, migrate=False)
    assert item.ext.proj.epsg is not None
    assert item.ext.proj.crs_string == "EPSG:32617"
