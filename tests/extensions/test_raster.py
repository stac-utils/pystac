import json

import pytest

import pystac
from pystac import ExtensionTypeError, Item
from pystac.extensions.raster import (
    DataType,
    Histogram,
    NoDataStrings,
    RasterBand,
    RasterExtension,
    Sampling,
    Statistics,
)
from pystac.utils import get_opt
from tests.conftest import get_data_file
from tests.utils import TestCases, assert_to_from_dict

PLANET_EXAMPLE_URI = get_data_file("raster/raster-planet-example.json")


@pytest.fixture
def ext_item() -> pystac.Item:
    return pystac.Item.from_file(PLANET_EXAMPLE_URI)


SENTINEL2_EXAMPLE_URI = TestCases.get_path(
    "data-files/raster/raster-sentinel2-example.json"
)


LANDSAT_COLLECTION_EXAMPLE_URI = TestCases.get_path(
    "data-files/raster/landsat-collection-example.json"
)


def test_to_from_dict() -> None:
    with open(PLANET_EXAMPLE_URI) as f:
        item_dict = json.load(f)
    assert_to_from_dict(Item, item_dict)


@pytest.mark.vcr()
def test_validate_raster(ext_item: pystac.Item) -> None:
    item2 = pystac.Item.from_file(SENTINEL2_EXAMPLE_URI)
    ext_item.validate()
    item2.validate()


@pytest.mark.vcr()
def test_asset_bands(ext_item: pystac.Item) -> None:
    item2 = pystac.Item.from_file(SENTINEL2_EXAMPLE_URI)

    # Get
    data_asset = ext_item.assets["data"]
    asset_bands = RasterExtension.ext(data_asset).bands
    assert asset_bands is not None
    assert len(asset_bands) == 4
    assert asset_bands[0].nodata == 0
    assert asset_bands[0].sampling == Sampling.AREA
    assert asset_bands[0].unit == "W⋅sr−1⋅m−2⋅nm−1"
    assert asset_bands[0].data_type == DataType.UINT16
    assert asset_bands[0].scale == 0.01
    assert asset_bands[0].offset == 0
    assert asset_bands[0].spatial_resolution == 3

    band0_stats = asset_bands[0].statistics
    assert band0_stats is not None
    assert band0_stats.minimum == 1962
    assert band0_stats.maximum == 32925
    assert band0_stats.mean == 8498.9400644319
    assert band0_stats.stddev == 5056.1292002722
    assert band0_stats.valid_percent == 61.09

    band0_hist = asset_bands[0].histogram
    assert band0_hist is not None
    assert band0_hist.count == 256
    assert band0_hist.min == 1901.288235294118
    assert band0_hist.max == 32985.71176470588
    assert len(band0_hist.buckets) == band0_hist.count

    index_asset = ext_item.assets["metadata"]
    asset_bands = RasterExtension.ext(index_asset).bands
    assert None is asset_bands

    b09_asset = item2.assets["B09"]
    b09_bands = RasterExtension.ext(b09_asset).bands
    assert b09_bands is not None
    assert b09_bands[0].nodata == "nan"

    # Set
    b2_asset = item2.assets["B02"]
    assert (
        get_opt(get_opt(RasterExtension.ext(b2_asset).bands)[0].statistics).maximum
        == 19264
    )
    b1_asset = item2.assets["B01"]
    RasterExtension.ext(b2_asset).bands = RasterExtension.ext(b1_asset).bands

    new_b2_asset_bands = RasterExtension.ext(item2.assets["B02"]).bands

    assert get_opt(get_opt(new_b2_asset_bands)[0].statistics).maximum == 20567
    new_b2_asset_band0 = get_opt(new_b2_asset_bands)[0]
    new_b2_asset_band0.nodata = NoDataStrings.INF

    item2.validate()

    # Check adding a new asset
    new_stats = [
        Statistics.create(
            minimum=0, maximum=10000, mean=5000, stddev=10, valid_percent=88
        ),
        Statistics.create(minimum=-1, maximum=1, mean=0, stddev=1, valid_percent=100),
        Statistics.create(
            minimum=1, maximum=255, mean=200, stddev=3, valid_percent=100
        ),
    ]
    # new_histograms = []
    with open(TestCases.get_path("data-files/raster/gdalinfo.json")) as gdaljson_file:
        gdaljson_data = json.load(gdaljson_file)
        new_histograms = list(
            map(
                lambda band: Histogram.from_dict(band["histogram"]),
                gdaljson_data["bands"],
            )
        )
    new_bands = [
        RasterBand.create(
            nodata=1,
            unit="test1",
            statistics=new_stats[0],
            histogram=new_histograms[0],
        ),
        RasterBand.create(
            nodata=2,
            unit="test2",
            statistics=new_stats[1],
            histogram=new_histograms[1],
        ),
        RasterBand.create(
            nodata=NoDataStrings.NINF,
            unit="test3",
            statistics=new_stats[2],
            histogram=new_histograms[2],
        ),
    ]
    asset = pystac.Asset(href="some/path.tif", media_type=pystac.MediaType.GEOTIFF)
    RasterExtension.ext(asset).bands = new_bands
    ext_item.add_asset("test", asset)

    assert len(ext_item.assets["test"].extra_fields["raster:bands"]) == 3
    assert (
        ext_item.assets["test"].extra_fields["raster:bands"][1]["statistics"]["minimum"]
        == -1
    )
    assert (
        ext_item.assets["test"].extra_fields["raster:bands"][1]["histogram"]["min"]
        == 3848.354901960784
    )
    assert ext_item.assets["test"].extra_fields["raster:bands"][2]["nodata"] == "-inf"

    for s in new_stats:
        s.minimum = None
        s.maximum = None
        s.mean = None
        s.stddev = None
        s.valid_percent = None
        assert len(s.properties) == 0

    for b in new_bands:
        b.bits_per_sample = None
        b.data_type = None
        b.histogram = None
        b.nodata = None
        b.sampling = None
        b.scale = None
        b.spatial_resolution = None
        b.statistics = None
        b.unit = None
        b.offset = None
        assert len(b.properties) == 0

    new_stats[2].apply(minimum=0, maximum=10000, mean=5000, stddev=10, valid_percent=88)
    new_stats[1].apply(minimum=-1, maximum=1, mean=0, stddev=1, valid_percent=100)
    new_stats[0].apply(minimum=1, maximum=255, mean=200, stddev=3, valid_percent=100)
    new_bands[2].apply(
        nodata=1,
        unit="test1",
        statistics=new_stats[2],
        histogram=new_histograms[0],
    )
    new_bands[1].apply(
        nodata=2,
        unit="test2",
        statistics=new_stats[1],
        histogram=new_histograms[1],
    )
    new_bands[0].apply(
        nodata=NoDataStrings.NAN,
        unit="test3",
        statistics=new_stats[0],
        histogram=new_histograms[2],
    )
    RasterExtension.ext(ext_item.assets["test"]).apply(new_bands)
    assert (
        ext_item.assets["test"].extra_fields["raster:bands"][0]["statistics"]["minimum"]
        == 1
    )
    assert ext_item.assets["test"].extra_fields["raster:bands"][0]["nodata"] == "nan"


def test_extension_not_implemented(ext_item: pystac.Item) -> None:
    # Should raise exception if Item does not include extension URI
    ext_item.stac_extensions.remove(RasterExtension.get_schema_uri())

    # Should raise exception if owning Item does not include extension URI
    asset = ext_item.assets["data"]

    with pytest.raises(pystac.ExtensionNotImplemented):
        _ = RasterExtension.ext(asset)

    # Should succeed if Asset has no owner
    ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
    _ = RasterExtension.ext(ownerless_asset)


def test_ext_add_to(ext_item: pystac.Item) -> None:
    ext_item.stac_extensions.remove(RasterExtension.get_schema_uri())
    asset = ext_item.assets["data"]

    _ = RasterExtension.ext(asset, add_if_missing=True)

    assert RasterExtension.get_schema_uri() in ext_item.stac_extensions


def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError, match=r"^RasterExtension does not apply to type 'object'$"
    ):
        # calling it wrong on purpose so --------v
        RasterExtension.ext(object())  # type: ignore


def test_summaries_adds_uri() -> None:
    col = pystac.Collection.from_file(LANDSAT_COLLECTION_EXAMPLE_URI)
    col.stac_extensions = []
    with pytest.raises(
        pystac.ExtensionNotImplemented,
        match="Extension 'raster' is not implemented",
    ):
        RasterExtension.summaries(col, add_if_missing=False)

    RasterExtension.summaries(col, True)

    assert RasterExtension.get_schema_uri() in col.stac_extensions

    RasterExtension.remove_from(col)
    assert RasterExtension.get_schema_uri() not in col.stac_extensions


def test_collection_item_asset() -> None:
    coll = pystac.Collection.from_file(LANDSAT_COLLECTION_EXAMPLE_URI)

    assert coll.item_assets

    qa = coll.item_assets["qa"]
    ang = coll.item_assets["ang"]

    assert qa.ext.raster.bands is not None
    assert ang.ext.raster.bands is None


def test_older_extension_version(ext_item: pystac.Item) -> None:
    old = "https://stac-extensions.github.io/raster/v1.0.0/schema.json"
    new = "https://stac-extensions.github.io/raster/v1.1.0/schema.json"

    stac_extensions = set(ext_item.stac_extensions)
    stac_extensions.remove(new)
    stac_extensions.add(old)
    item_as_dict = ext_item.to_dict(include_self_link=False, transform_hrefs=False)
    item_as_dict["stac_extensions"] = list(stac_extensions)
    item = pystac.Item.from_dict(item_as_dict, migrate=False)
    assert RasterExtension.has_extension(item)
    assert old in item.stac_extensions

    migrated_item = pystac.Item.from_dict(item_as_dict, migrate=True)
    assert RasterExtension.has_extension(migrated_item)
    assert new in migrated_item.stac_extensions
