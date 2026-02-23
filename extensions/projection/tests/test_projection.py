import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

import pystac
import pytest
from pystac import ExtensionTypeError, Item
from pystac.errors import ExtensionNotImplemented
from pystac.extensions.projection import ProjectionExtension
from pystac.utils import get_opt

DATA_FILES = Path(__file__).resolve().parent / "data-files"

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

ARBITRARY_GEOM: dict[str, Any] = {
    "type": "Polygon",
    "coordinates": [
        [
            [-2.5048828125, 3.8916575492899987],
            [-1.9610595703125, 3.8916575492899987],
            [-1.9610595703125, 4.275202171119132],
            [-2.5048828125, 4.275202171119132],
            [-2.5048828125, 3.8916575492899987],
        ]
    ],
}

ARBITRARY_BBOX: list[float] = [
    ARBITRARY_GEOM["coordinates"][0][0][0],
    ARBITRARY_GEOM["coordinates"][0][0][1],
    ARBITRARY_GEOM["coordinates"][0][1][0],
    ARBITRARY_GEOM["coordinates"][0][1][1],
]


@pytest.fixture
def example_uri() -> str:
    return str(DATA_FILES / "example-landsat8.json")


@pytest.fixture
def proj_item(example_uri: str) -> Item:
    return pystac.Item.from_file(example_uri)


@pytest.fixture
def example_summaries_uri() -> str:
    return str(DATA_FILES / "collection-with-summaries.json")


def test_to_from_dict(example_uri: str) -> None:
    with open(example_uri) as f:
        d = json.load(f)
    d2 = pystac.Item.from_dict(d, migrate=False).to_dict()
    assert d == d2


def test_apply() -> None:
    item = Item("test-item", ARBITRARY_GEOM, ARBITRARY_BBOX, datetime.now(), {})
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
def test_partial_apply(proj_item: Item) -> None:
    ProjectionExtension.ext(proj_item).apply(epsg=1111)

    assert ProjectionExtension.ext(proj_item).epsg == 1111
    proj_item.validate()


@pytest.mark.vcr()
def test_validate_proj(proj_item: Item) -> None:
    proj_item.validate()


@pytest.mark.vcr()
def test_epsg(proj_item: Item) -> None:
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
    proj_item = pystac.Item.from_file(str(DATA_FILES / "optional-epsg.json"))

    # No proj info on item
    assert "proj:epsg" not in proj_item.properties
    assert "proj:code" not in proj_item.properties

    # Some proj info on assets
    asset_no_prop = proj_item.assets["metadata"]
    assert ProjectionExtension.ext(asset_no_prop).epsg is None

    asset_prop = proj_item.assets["visual"]
    assert ProjectionExtension.ext(asset_prop).epsg == 32618


@pytest.mark.vcr()
def test_wkt2(proj_item: Item) -> None:
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
def test_projjson(proj_item: Item) -> None:
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


def test_crs_string(proj_item: Item) -> None:
    ProjectionExtension.remove_from(proj_item)
    for key in list(proj_item.properties.keys()):
        if key.startswith("proj:"):
            proj_item.properties.pop(key)
    assert proj_item.properties.get("proj:code") is None
    assert proj_item.properties.get("proj:epsg") is None
    assert proj_item.properties.get("proj:wkt2") is None
    assert proj_item.properties.get("proj:projjson") is None

    projection = ProjectionExtension.ext(proj_item, add_if_missing=True)
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
def test_geometry(proj_item: Item) -> None:
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
def test_bbox(proj_item: Item) -> None:
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
def test_centroid(proj_item: Item) -> None:
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
def test_shape(proj_item: Item) -> None:
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
def test_transform(proj_item: Item) -> None:
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


def test_extension_not_implemented(proj_item: Item) -> None:
    # Should raise exception if Item does not include extension URI
    proj_item.stac_extensions.remove(ProjectionExtension.get_schema_uri())

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = ProjectionExtension.ext(proj_item)

    # Should raise exception if owning Item does not include extension URI
    asset = proj_item.assets["B8"]

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = ProjectionExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = ProjectionExtension.ext(ownerless_asset)


def test_item_ext_add_to(proj_item: Item) -> None:
    proj_item.stac_extensions.remove(ProjectionExtension.get_schema_uri())
    assert ProjectionExtension.get_schema_uri() not in proj_item.stac_extensions

    _ = ProjectionExtension.ext(proj_item, add_if_missing=True)

    assert ProjectionExtension.get_schema_uri() in proj_item.stac_extensions


def test_asset_ext_add_to(proj_item: Item) -> None:
    proj_item.stac_extensions.remove(ProjectionExtension.get_schema_uri())
    assert ProjectionExtension.get_schema_uri() not in proj_item.stac_extensions
    asset = proj_item.assets["B8"]

    _ = ProjectionExtension.ext(asset, add_if_missing=True)

    assert ProjectionExtension.get_schema_uri() in proj_item.stac_extensions


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


def test_migrate_item_on_1_2() -> None:
    old = "https://stac-extensions.github.io/projection/v1.2.0/schema.json"
    current = "https://stac-extensions.github.io/projection/v2.0.0/schema.json"

    path = str(DATA_FILES / "example-with-version-1.2.json")
    with pytest.warns(UserWarning, match="surprising behavior"):
        item = Item.from_file(path)

    assert old not in item.stac_extensions
    assert current in item.stac_extensions

    assert item.ext.proj.epsg == 32613
    assert item.ext.proj.code == "EPSG:32613"

    assert item.assets["B1"].ext.proj.epsg == 32613
    assert item.assets["B1"].ext.proj.code == "EPSG:32613"

    assert item.assets["B8"].ext.proj.epsg == 9998
    assert item.assets["B8"].ext.proj.code == "EPSG:9998"


def test_migrate_item_on_1_1() -> None:
    old = "https://stac-extensions.github.io/projection/v1.1.0/schema.json"
    current = "https://stac-extensions.github.io/projection/v2.0.0/schema.json"

    path = str(DATA_FILES / "example-with-version-1.1.json")
    item = Item.from_file(path)

    assert old not in item.stac_extensions
    assert current in item.stac_extensions

    assert item.ext.proj.epsg == 32614
    assert item.ext.proj.code == "EPSG:32614"

    assert item.assets["B1"].ext.proj.epsg == 32614
    assert item.assets["B1"].ext.proj.code == "EPSG:32614"

    assert item.assets["B8"].ext.proj.epsg == 9999
    assert item.assets["B8"].ext.proj.code == "EPSG:9999"


def test_migrate_collection_item_assets() -> None:
    old = "https://stac-extensions.github.io/projection/v1.1.0/schema.json"
    current = "https://stac-extensions.github.io/projection/v2.0.0/schema.json"

    path = str(DATA_FILES / "collection-with-summaries.json")
    collection = pystac.Collection.from_file(path)

    assert old not in collection.stac_extensions
    assert current in collection.stac_extensions

    for item_asset in collection.item_assets.values():
        assert item_asset.ext.proj.epsg == 32659
        assert item_asset.ext.proj.code == "EPSG:32659"


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
    with open(str(DATA_FILES / "example-with-version-1.1.json")) as f:
        data = json.load(f)
    item = pystac.Item.from_dict(data, migrate=False)
    assert item.ext.proj.epsg is not None
    assert item.ext.proj.crs_string is not None


def test_v1_crs_string() -> None:
    with open(str(DATA_FILES / "another-1.1.json")) as f:
        data = json.load(f)
    item = pystac.Item.from_dict(data, migrate=False)
    assert item.ext.proj.epsg is not None
    assert item.ext.proj.crs_string == "EPSG:32617"


def test_none_epsg(item: Item) -> None:
    # https://github.com/stac-utils/pystac/issues/1543
    d = item.to_dict(include_self_link=False, transform_hrefs=False)
    d["stac_version"] = "1.0.0"
    d["stac_extensions"] = [
        "https://stac-extensions.github.io/projection/v1.1.0/schema.json"
    ]
    d["properties"]["proj:epsg"] = None
    item = Item.from_dict(d, migrate=True)
    assert item.ext.proj.code is None


def test_migrate_by_default() -> None:
    with open(str(DATA_FILES / "example-with-version-1.1.json")) as f:
        data = json.load(f)
    item = pystac.Item.from_dict(data)  # default used to be migrate=False
    assert item.ext.proj.code == "EPSG:32614"
