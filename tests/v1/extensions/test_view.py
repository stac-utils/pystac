import json

import pytest
from pystac.extensions.view import ViewExtension
from pystac.summaries import RangeSummary

import pystac
from pystac import ExtensionTypeError, Item
from pystac.collection import Collection
from tests.v1.utils import TestCases, assert_to_from_dict

EXAMPLE_URI = TestCases.get_path("data-files/view/example-landsat8.json")


@pytest.fixture
def item() -> Item:
    return pystac.Item.from_file(EXAMPLE_URI)


@pytest.fixture
def collection() -> Collection:
    return Collection.from_file(
        TestCases.get_path("data-files/view/collection-with-summaries.json")
    )


def test_to_from_dict() -> None:
    with open(EXAMPLE_URI) as f:
        d = json.load(f)
    assert_to_from_dict(pystac.Item, d)


def test_apply() -> None:
    item = next(TestCases.case_2().get_items(recursive=True))
    assert not ViewExtension.has_extension(item)

    ViewExtension.add_to(item)
    ViewExtension.ext(item).apply(
        off_nadir=1.0,
        incidence_angle=2.0,
        azimuth=3.0,
        sun_azimuth=4.0,
        sun_elevation=5.0,
    )

    assert ViewExtension.ext(item).off_nadir == 1.0
    assert ViewExtension.ext(item).incidence_angle == 2.0
    assert ViewExtension.ext(item).azimuth == 3.0
    assert ViewExtension.ext(item).sun_azimuth == 4.0
    assert ViewExtension.ext(item).sun_elevation == 5.0


@pytest.mark.vcr()
def test_validate_view(item: Item) -> None:
    assert ViewExtension.has_extension(item)
    item.validate()


@pytest.mark.vcr()
def test_off_nadir(item: Item) -> None:
    # Get
    assert "view:off_nadir" in item.properties
    view_off_nadir = ViewExtension.ext(item).off_nadir
    assert view_off_nadir is not None
    assert view_off_nadir == item.properties["view:off_nadir"]

    # Set
    ViewExtension.ext(item).off_nadir = view_off_nadir + 10
    assert view_off_nadir + 10 == item.properties["view:off_nadir"]

    # Get from Asset
    asset_no_prop = item.assets["blue"]
    asset_prop = item.assets["red"]
    assert (
        ViewExtension.ext(asset_no_prop).off_nadir == ViewExtension.ext(item).off_nadir
    )
    assert ViewExtension.ext(asset_prop).off_nadir == 3.0

    # Set to Asset
    asset_value = 13.0
    ViewExtension.ext(asset_no_prop).off_nadir = asset_value
    assert (
        ViewExtension.ext(asset_no_prop).off_nadir != ViewExtension.ext(item).off_nadir
    )
    assert ViewExtension.ext(asset_no_prop).off_nadir == asset_value

    # Validate
    item.validate()


@pytest.mark.vcr()
def test_incidence_angle(item: Item) -> None:
    # Get
    assert "view:incidence_angle" in item.properties
    view_incidence_angle = ViewExtension.ext(item).incidence_angle
    assert view_incidence_angle is not None
    assert view_incidence_angle == item.properties["view:incidence_angle"]
    # Set
    ViewExtension.ext(item).incidence_angle = view_incidence_angle + 10
    assert view_incidence_angle + 10 == item.properties["view:incidence_angle"]
    # Get from Asset
    asset_no_prop = item.assets["blue"]
    asset_prop = item.assets["red"]
    assert (
        ViewExtension.ext(asset_no_prop).incidence_angle
        == ViewExtension.ext(item).incidence_angle
    )
    assert ViewExtension.ext(asset_prop).incidence_angle == 4.0

    # Set to Asset
    asset_value = 14.0
    ViewExtension.ext(asset_no_prop).incidence_angle = asset_value
    assert (
        ViewExtension.ext(asset_no_prop).incidence_angle
        != ViewExtension.ext(item).incidence_angle
    )
    assert ViewExtension.ext(asset_no_prop).incidence_angle == asset_value

    # Validate
    item.validate()


@pytest.mark.vcr()
def test_azimuth(item: Item) -> None:
    # Get
    assert "view:azimuth" in item.properties
    view_azimuth = ViewExtension.ext(item).azimuth
    assert view_azimuth is not None
    assert view_azimuth == item.properties["view:azimuth"]

    # Set
    ViewExtension.ext(item).azimuth = view_azimuth + 100
    assert view_azimuth + 100 == item.properties["view:azimuth"]

    # Get from Asset
    asset_no_prop = item.assets["blue"]
    asset_prop = item.assets["red"]
    assert ViewExtension.ext(asset_no_prop).azimuth == ViewExtension.ext(item).azimuth
    assert ViewExtension.ext(asset_prop).azimuth == 5.0

    # Set to Asset
    asset_value = 15.0
    ViewExtension.ext(asset_no_prop).azimuth = asset_value
    assert ViewExtension.ext(asset_no_prop).azimuth != ViewExtension.ext(item).azimuth
    assert ViewExtension.ext(asset_no_prop).azimuth == asset_value

    # Validate
    item.validate()


@pytest.mark.vcr()
def test_sun_azimuth(item: Item) -> None:
    # Get
    assert "view:sun_azimuth" in item.properties
    view_sun_azimuth = ViewExtension.ext(item).sun_azimuth
    assert view_sun_azimuth is not None
    assert view_sun_azimuth == item.properties["view:sun_azimuth"]

    # Set
    ViewExtension.ext(item).sun_azimuth = view_sun_azimuth + 100
    assert view_sun_azimuth + 100 == item.properties["view:sun_azimuth"]
    # Get from Asset
    asset_no_prop = item.assets["blue"]
    asset_prop = item.assets["red"]
    assert (
        ViewExtension.ext(asset_no_prop).sun_azimuth
        == ViewExtension.ext(item).sun_azimuth
    )
    assert ViewExtension.ext(asset_prop).sun_azimuth == 1.0

    # Set to Asset
    asset_value = 11.0
    ViewExtension.ext(asset_no_prop).sun_azimuth = asset_value
    assert (
        ViewExtension.ext(asset_no_prop).sun_azimuth
        != ViewExtension.ext(item).sun_azimuth
    )
    assert ViewExtension.ext(asset_no_prop).sun_azimuth == asset_value

    # Validate
    item.validate()


@pytest.mark.vcr()
def test_sun_elevation(item: Item) -> None:
    # Get
    assert "view:sun_elevation" in item.properties
    view_sun_elevation = ViewExtension.ext(item).sun_elevation
    assert view_sun_elevation is not None
    assert view_sun_elevation == item.properties["view:sun_elevation"]

    # Set
    ViewExtension.ext(item).sun_elevation = view_sun_elevation + 10
    assert view_sun_elevation + 10 == item.properties["view:sun_elevation"]
    # Get from Asset
    asset_no_prop = item.assets["blue"]
    asset_prop = item.assets["red"]
    assert (
        ViewExtension.ext(asset_no_prop).sun_elevation
        == ViewExtension.ext(item).sun_elevation
    )
    assert ViewExtension.ext(asset_prop).sun_elevation == 2.0

    # Set to Asset
    asset_value = 12.0
    ViewExtension.ext(asset_no_prop).sun_elevation = asset_value
    assert (
        ViewExtension.ext(asset_no_prop).sun_elevation
        != ViewExtension.ext(item).sun_elevation
    )
    assert ViewExtension.ext(asset_no_prop).sun_elevation == asset_value

    # Validate
    item.validate()


def test_extension_not_implemented(item: Item) -> None:
    # Should raise exception if Item does not include extension URI
    item.stac_extensions.remove(ViewExtension.get_schema_uri())

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = ViewExtension.ext(item)

    # Should raise exception if owning Item does not include extension URI
    asset = item.assets["blue"]

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = ViewExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = ViewExtension.ext(ownerless_asset)


def test_item_ext_add_to(item: Item) -> None:
    item.stac_extensions.remove(ViewExtension.get_schema_uri())
    assert ViewExtension.get_schema_uri() not in item.stac_extensions

    _ = ViewExtension.ext(item, add_if_missing=True)

    assert ViewExtension.get_schema_uri() in item.stac_extensions


def test_asset_ext_add_to(item: Item) -> None:
    item.stac_extensions.remove(ViewExtension.get_schema_uri())
    assert ViewExtension.get_schema_uri() not in item.stac_extensions
    asset = item.assets["blue"]

    _ = ViewExtension.ext(asset, add_if_missing=True)

    assert ViewExtension.get_schema_uri() in item.stac_extensions


def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError, match=r"^ViewExtension does not apply to type 'object'$"
    ):
        # calling it wrong on purpose so ------v
        ViewExtension.ext(object())  # type: ignore


def test_get_off_nadir_summaries(collection: Collection) -> None:
    off_nadirs = ViewExtension.summaries(collection, True).off_nadir

    assert off_nadirs is not None

    assert {"minimum": 0.5, "maximum": 7.3} == off_nadirs.to_dict()


def test_get_incidence_angle_summaries(collection: Collection) -> None:
    incidence_angles = ViewExtension.summaries(collection, True).incidence_angle

    assert incidence_angles is not None

    assert {"minimum": 23, "maximum": 35} == incidence_angles.to_dict()


def test_get_azimuth_summaries(collection: Collection) -> None:
    azimuths = ViewExtension.summaries(collection, True).azimuth

    assert azimuths is not None

    assert {"minimum": 20, "maximum": 186} == azimuths.to_dict()


def test_get_sun_azimuth_summaries(collection: Collection) -> None:
    sun_azimuths = ViewExtension.summaries(collection, True).sun_azimuth

    assert sun_azimuths is not None

    assert {"minimum": 48, "maximum": 78} == sun_azimuths.to_dict()


def test_get_sun_elevation_summaries(collection: Collection) -> None:
    sun_elevations = ViewExtension.summaries(collection, True).sun_elevation

    assert sun_elevations is not None

    assert {"minimum": 10, "maximum": 45} == sun_elevations.to_dict()


def test_set_off_nadir_summaries(collection: Collection) -> None:
    view_summaries = ViewExtension.summaries(collection, True)

    view_summaries.off_nadir = RangeSummary(0, 10)
    assert {"minimum": 0, "maximum": 10} == view_summaries.off_nadir.to_dict()


def test_set_incidence_angle_summaries(collection: Collection) -> None:
    view_summaries = ViewExtension.summaries(collection, True)

    view_summaries.incidence_angle = RangeSummary(5, 15)
    assert {"minimum": 5, "maximum": 15} == view_summaries.incidence_angle.to_dict()


def test_set_azimuth_summaries(collection: Collection) -> None:
    view_summaries = ViewExtension.summaries(collection, True)

    view_summaries.azimuth = None
    assert view_summaries.azimuth is None


def test_set_sun_azimuth_summaries(collection: Collection) -> None:
    view_summaries = ViewExtension.summaries(collection, True)

    view_summaries.sun_azimuth = RangeSummary(210, 275)
    assert {"minimum": 210, "maximum": 275} == view_summaries.sun_azimuth.to_dict()


def test_set_sun_elevation_summaries(collection: Collection) -> None:
    view_summaries = ViewExtension.summaries(collection, True)

    view_summaries.sun_elevation = RangeSummary(-10, 38)
    assert {"minimum": -10, "maximum": 38} == view_summaries.sun_elevation.to_dict()


def test_summaries_adds_uri(collection: Collection) -> None:
    collection.stac_extensions = []
    with pytest.raises(
        pystac.ExtensionNotImplemented,
        match="Extension 'view' is not implemented",
    ):
        ViewExtension.summaries(collection, add_if_missing=False)

    _ = ViewExtension.summaries(collection, True)

    assert ViewExtension.get_schema_uri() in collection.stac_extensions

    ViewExtension.remove_from(collection)
    assert ViewExtension.get_schema_uri() not in collection.stac_extensions
