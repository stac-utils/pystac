import json
from pathlib import Path
from typing import cast

import pytest
from pytest_pystac.plugin import assert_to_from_dict

import pystac
from pystac import DataType, ExtensionTypeError, Item, NoDataStrings, Statistics
from pystac.extensions.raster import (
    Histogram,
    RasterExtension,
    Sampling,
)
from pystac.utils import get_opt

DATA_FILES = Path(__file__).resolve().parent / "data-files"

PLANET_EXAMPLE_URI = str(DATA_FILES / "raster-planet-example.json")


@pytest.fixture
def ext_item() -> pystac.Item:
    return pystac.Item.from_file(PLANET_EXAMPLE_URI)


SENTINEL2_EXAMPLE_URI = str(DATA_FILES / "raster-sentinel2-example.json")


LANDSAT_COLLECTION_EXAMPLE_URI = str(DATA_FILES / "landsat-collection-example.json")


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
    assert data_asset.common_metadata.bands is not None
    asset_bands_raster = RasterExtension.ext(data_asset).get_bands()
    assert asset_bands_raster is not None
    assert len(asset_bands_raster) == 4

    # nodata, data_type, statistics and unit have been moved to
    # STAC common metadata since v2.0.0

    asset_bands = data_asset.common_metadata.bands
    assert [b.name for b in asset_bands] == ["band-1", "band-2", "band-3", "band-4"]

    assert data_asset.common_metadata.nodata == 0
    assert data_asset.ext.raster.sampling == Sampling.AREA
    assert data_asset.common_metadata.unit == "W⋅sr−1⋅m−2"
    assert data_asset.common_metadata.data_type == DataType.UINT16
    assert asset_bands[0].ext.raster.scale == 0.01
    assert asset_bands[0].ext.raster.offset == 0
    assert data_asset.ext.raster.spatial_resolution == 3

    band0_stats = asset_bands[0].ext.raster.get_statistics()
    assert band0_stats is not None
    assert band0_stats.minimum == 1962
    assert band0_stats.maximum == 32925
    assert band0_stats.mean == 8498.9400644319
    assert band0_stats.stddev == 5056.1292002722
    assert band0_stats.valid_percent == 61.09

    band0_hist = asset_bands[0].ext.raster.histogram
    assert band0_hist is not None
    assert band0_hist.count == 256
    assert band0_hist.min == 1901.288235294118
    assert band0_hist.max == 32985.71176470588
    assert len(band0_hist.buckets) == band0_hist.count

    index_asset = ext_item.assets["metadata"]
    asset_bands_raster = RasterExtension.ext(index_asset).get_bands()
    assert asset_bands_raster is None

    b09_asset = item2.assets["B09"]
    b09_bands = RasterExtension.ext(b09_asset).get_bands()
    assert b09_bands is None
    assert b09_asset.ext.raster.spatial_resolution == 60
    assert b09_asset.common_metadata.nodata == "nan"

    # Set
    b2_asset = item2.assets["B02"]
    assert get_opt(b2_asset.common_metadata.statistics).maximum == 19264
    b1_asset = item2.assets["B01"]
    b2_asset.common_metadata.statistics = b1_asset.common_metadata.statistics
    b2_asset.common_metadata.nodata = b1_asset.common_metadata.nodata

    assert get_opt(b2_asset.common_metadata.statistics).maximum == 20567
    b2_asset.common_metadata.nodata = NoDataStrings.INF

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
    with open(DATA_FILES / "gdalinfo.json") as gdaljson_file:
        gdaljson_data = json.load(gdaljson_file)
        new_histograms: list[Histogram] = list(
            map(
                lambda band: Histogram.from_dict(band["histogram"]),
                gdaljson_data["bands"],
            )
        )
    new_bands = [
        pystac.Band.create(name=f"raster-band-{band_n}") for band_n in range(1, 4)
    ]
    new_bands_raster_data = [
        dict(
            nodata=1,
            unit="test1",
            statistics=new_stats[0],
            histogram=new_histograms[0],
        ),
        dict(
            nodata=2,
            unit="test2",
            statistics=new_stats[1],
            histogram=new_histograms[1],
        ),
        dict(
            nodata=NoDataStrings.NINF,
            unit="test3",
            statistics=new_stats[2],
            histogram=new_histograms[2],
        ),
    ]
    asset = pystac.Asset(href="some/path.tif", media_type=pystac.MediaType.GEOTIFF)
    modified_bands: list[pystac.Band] = []

    for band, raster_data in zip(new_bands, new_bands_raster_data):
        band.extra_fields = {
            k: v.to_dict() if isinstance(v, Statistics) else v
            for k, v in raster_data.items()
            if k != "histogram"
        }
        raster_band = RasterExtension.ext(band)
        raster_band.apply(histogram=cast(Histogram, raster_data["histogram"]))
        modified_bands.append(band)

    asset.common_metadata.bands = modified_bands

    ext_item.add_asset("test", asset)

    assert (
        ext_item.assets["test"].extra_fields["bands"][1]["statistics"]["minimum"] == -1
    )
    assert (
        ext_item.assets["test"].extra_fields["bands"][1]["raster:histogram"]["min"]
        == 3848.354901960784
    )
    assert ext_item.assets["test"].extra_fields["bands"][2]["nodata"] == "-inf"

    for s in new_stats:
        s.minimum = None
        s.maximum = None
        s.mean = None
        s.stddev = None
        s.valid_percent = None
        assert len(s.properties) == 0

    for b in modified_bands:
        b.set_prop("raster:bits_per_sample", None)
        b.set_prop("data_type", None)
        b.set_prop("raster:histogram", None)
        b.set_prop("nodata", None)
        b.set_prop("raster:sampling", None)
        b.set_prop("raster:scale", None)
        b.set_prop("raster:spatial_resolution", None)
        b.set_prop("statistics", None)
        b.set_prop("unit", None)
        b.set_prop("raster:offset", None)
        assert len(b.extra_fields) == 0

    new_stats[2].apply(minimum=0, maximum=10000, mean=5000, stddev=10, valid_percent=88)
    new_stats[1].apply(minimum=-1, maximum=1, mean=0, stddev=1, valid_percent=100)
    new_stats[0].apply(minimum=1, maximum=255, mean=200, stddev=3, valid_percent=100)

    modified_bands[2].set_prop("nodata", 1)
    modified_bands[2].set_prop("unit", "test1")
    modified_bands[2].set_prop("statistics", new_stats[2])
    modified_bands[2].ext.raster.histogram = new_histograms[0]

    modified_bands[1].set_prop("nodata", 2)
    modified_bands[1].set_prop("unit", "test2")
    modified_bands[1].set_prop("statistics", new_stats[1])
    modified_bands[1].ext.raster.histogram = new_histograms[1]

    modified_bands[0].set_prop("nodata", NoDataStrings.NAN)
    modified_bands[0].set_prop("unit", "test3")
    modified_bands[0].set_prop("statistics", new_stats[0])
    modified_bands[0].ext.raster.histogram = new_histograms[2]

    ext_item.assets["test"].common_metadata.bands = modified_bands
    assert (
        ext_item.assets["test"].extra_fields["bands"][0]["statistics"]["minimum"] == 1
    )
    assert ext_item.assets["test"].extra_fields["bands"][0]["nodata"] == "nan"


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

    assert qa.ext.raster.scale is not None
    assert ang.ext.raster.scale is None


def test_older_extension_version(ext_item: pystac.Item) -> None:
    old = "https://stac-extensions.github.io/raster/v1.1.0/schema.json"
    new = "https://stac-extensions.github.io/raster/v2.0.0/schema.json"

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
