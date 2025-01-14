import json
import unittest

import pytest

import pystac
from pystac import ExtensionTypeError, Item
from pystac.errors import ExtensionNotImplemented, RequiredPropertyMissing
from pystac.extensions.eo import PREFIX, SNOW_COVER_PROP, Band, EOExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.summaries import RangeSummary
from pystac.utils import get_opt
from tests.conftest import get_data_file
from tests.utils import TestCases, assert_to_from_dict


class BandsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None

    def test_create(self) -> None:
        band = Band.create(
            name="B01",
            common_name="red",
            description=Band.band_description("red"),
            center_wavelength=0.65,
            full_width_half_max=0.1,
            solar_illumination=42.0,
        )

        self.assertEqual(band.name, "B01")
        self.assertEqual(band.common_name, "red")
        self.assertEqual(band.description, "Common name: red, Range: 0.6 to 0.7")
        self.assertEqual(band.center_wavelength, 0.65)
        self.assertEqual(band.full_width_half_max, 0.1)
        self.assertEqual(band.solar_illumination, 42.0)
        self.assertEqual(band.__repr__(), "<Band name=B01>")

    def test_band_description_unknown_band(self) -> None:
        desc = Band.band_description("rainbow")

        self.assertIsNone(desc)


class EOTest(unittest.TestCase):
    LANDSAT_EXAMPLE_URI = TestCases.get_path("data-files/eo/eo-landsat-example.json")
    BANDS_IN_ITEM_URI = TestCases.get_path(
        "data-files/eo/sample-bands-in-item-properties.json"
    )
    EO_COLLECTION_URI = TestCases.get_path("data-files/eo/eo-collection.json")
    S2_ITEM_URI = TestCases.get_path("data-files/eo/eo-sentinel2-item.json")
    PLAIN_ITEM = TestCases.get_path("data-files/item/sample-item.json")

    def setUp(self) -> None:
        self.maxDiff = None

    def test_to_from_dict(self) -> None:
        with open(self.LANDSAT_EXAMPLE_URI) as f:
            item_dict = json.load(f)
        assert_to_from_dict(Item, item_dict)

    def test_add_to(self) -> None:
        item = Item.from_file(self.PLAIN_ITEM)
        self.assertNotIn(EOExtension.get_schema_uri(), item.stac_extensions)

        # Check that the URI gets added to stac_extensions
        EOExtension.add_to(item)
        self.assertIn(EOExtension.get_schema_uri(), item.stac_extensions)

        # Check that the URI only gets added once, regardless of how many times add_to
        # is called.
        EOExtension.add_to(item)
        EOExtension.add_to(item)

        eo_uris = [
            uri for uri in item.stac_extensions if uri == EOExtension.get_schema_uri()
        ]
        self.assertEqual(len(eo_uris), 1)

    @pytest.mark.vcr()
    def test_validate_eo(self) -> None:
        item = pystac.Item.from_file(self.LANDSAT_EXAMPLE_URI)
        item2 = pystac.Item.from_file(self.BANDS_IN_ITEM_URI)
        item.validate()
        item2.validate()

    @pytest.mark.vcr()
    def test_bands(self) -> None:
        item = pystac.Item.from_file(self.BANDS_IN_ITEM_URI)

        # Get
        self.assertIn("eo:bands", item.properties)
        bands = EOExtension.ext(item).bands
        assert bands is not None
        self.assertEqual(
            list(map(lambda x: x.name, bands)), ["band1", "band2", "band3", "band4"]
        )

        # Set
        new_bands = [
            Band.create(name="red", description=Band.band_description("red")),
            Band.create(name="green", description=Band.band_description("green")),
            Band.create(name="blue", description=Band.band_description("blue")),
        ]

        EOExtension.ext(item).bands = new_bands
        self.assertEqual(
            "Common name: red, Range: 0.6 to 0.7",
            item.properties["eo:bands"][0]["description"],
        )
        self.assertEqual(len(EOExtension.ext(item).bands or []), 3)
        item.validate()

    def test_asset_bands_s2(self) -> None:
        item = pystac.Item.from_file(self.S2_ITEM_URI)
        mtd_asset = item.get_assets()["mtd"]
        self.assertIsNone(EOExtension.ext(mtd_asset).bands)

    @pytest.mark.vcr()
    def test_asset_bands(self) -> None:
        item = pystac.Item.from_file(self.LANDSAT_EXAMPLE_URI)

        # Get

        b1_asset = item.assets["B1"]
        asset_bands = EOExtension.ext(b1_asset).bands
        assert asset_bands is not None
        self.assertEqual(len(asset_bands), 1)
        self.assertEqual(asset_bands[0].name, "B1")
        self.assertEqual(asset_bands[0].solar_illumination, 2000)

        index_asset = item.assets["index"]
        asset_bands = EOExtension.ext(index_asset).bands
        self.assertIs(None, asset_bands)

        # No asset specified
        item_bands = EOExtension.ext(item).bands
        self.assertIsNot(None, item_bands)

        # Set
        b2_asset = item.assets["B2"]
        self.assertEqual(get_opt(EOExtension.ext(b2_asset).bands)[0].name, "B2")
        EOExtension.ext(b2_asset).bands = EOExtension.ext(b1_asset).bands

        new_b2_asset_bands = EOExtension.ext(item.assets["B2"]).bands

        self.assertEqual(get_opt(new_b2_asset_bands)[0].name, "B1")

        item.validate()

        # Check adding a new asset
        new_bands = [
            Band.create(
                name="red",
                description=Band.band_description("red"),
                solar_illumination=1900,
            ),
            Band.create(
                name="green",
                description=Band.band_description("green"),
                solar_illumination=1950,
            ),
            Band.create(
                name="blue",
                description=Band.band_description("blue"),
                solar_illumination=2000,
            ),
        ]
        asset = pystac.Asset(href="some/path.tif", media_type=pystac.MediaType.GEOTIFF)
        EOExtension.ext(asset).bands = new_bands
        item.add_asset("test", asset)

        self.assertEqual(len(item.assets["test"].extra_fields["eo:bands"]), 3)

    @pytest.mark.vcr()
    def test_cloud_cover(self) -> None:
        item = pystac.Item.from_file(self.LANDSAT_EXAMPLE_URI)

        # Get
        self.assertIn("eo:cloud_cover", item.properties)
        cloud_cover = EOExtension.ext(item).cloud_cover
        self.assertEqual(cloud_cover, 78)

        # Set
        EOExtension.ext(item).cloud_cover = 50
        self.assertEqual(item.properties["eo:cloud_cover"], 50)

        # Get from Asset
        b2_asset = item.assets["B2"]
        self.assertEqual(
            EOExtension.ext(b2_asset).cloud_cover, EOExtension.ext(item).cloud_cover
        )

        b3_asset = item.assets["B3"]
        self.assertEqual(EOExtension.ext(b3_asset).cloud_cover, 20)

        # Set on Asset
        EOExtension.ext(b2_asset).cloud_cover = 10
        self.assertEqual(EOExtension.ext(b2_asset).cloud_cover, 10)

        item.validate()

    def test_summaries(self) -> None:
        col = pystac.Collection.from_file(self.EO_COLLECTION_URI)
        eo_summaries = EOExtension.summaries(col)

        # Get

        cloud_cover_summaries = eo_summaries.cloud_cover
        assert cloud_cover_summaries is not None
        self.assertEqual(cloud_cover_summaries.minimum, 0.0)
        self.assertEqual(cloud_cover_summaries.maximum, 80.0)

        snow_cover_summaries = eo_summaries.snow_cover
        assert snow_cover_summaries is not None
        self.assertEqual(snow_cover_summaries.minimum, 0.0)
        self.assertEqual(snow_cover_summaries.maximum, 80.0)

        bands = eo_summaries.bands
        assert bands is not None
        self.assertEqual(len(bands), 11)

        # Set

        eo_summaries.cloud_cover = RangeSummary(1.0, 2.0)
        eo_summaries.snow_cover = RangeSummary(4.0, 23)
        eo_summaries.bands = [Band.create(name="test")]

        col_dict = col.to_dict()
        self.assertEqual(len(col_dict["summaries"]["eo:bands"]), 1)
        self.assertEqual(col_dict["summaries"]["eo:cloud_cover"]["minimum"], 1.0)
        self.assertEqual(col_dict["summaries"]["eo:snow_cover"]["minimum"], 4.0)

    def test_summaries_adds_uri(self) -> None:
        col = pystac.Collection.from_file(self.EO_COLLECTION_URI)
        col.stac_extensions = []
        with pytest.raises(
            pystac.ExtensionNotImplemented, match="Extension 'eo' is not implemented"
        ):
            EOExtension.summaries(col, add_if_missing=False)

        EOExtension.summaries(col, add_if_missing=True)

        self.assertIn(EOExtension.get_schema_uri(), col.stac_extensions)

        EOExtension.remove_from(col)
        self.assertNotIn(EOExtension.get_schema_uri(), col.stac_extensions)

    def test_read_pre_09_fields_into_common_metadata(self) -> None:
        eo_item = pystac.Item.from_file(
            TestCases.get_path(
                "data-files/examples/0.8.1/item-spec/examples/" "landsat8-sample.json"
            )
        )

        self.assertEqual(eo_item.common_metadata.platform, "landsat-8")
        self.assertEqual(eo_item.common_metadata.instruments, ["oli_tirs"])

    def test_reads_asset_bands_in_pre_1_0_version(self) -> None:
        item = pystac.Item.from_file(
            TestCases.get_path(
                "data-files/examples/0.9.0/item-spec/examples/" "landsat8-sample.json"
            )
        )

        bands = EOExtension.ext(item.assets["B9"]).bands

        self.assertEqual(len(bands or []), 1)
        self.assertEqual(get_opt(bands)[0].common_name, "cirrus")

    def test_reads_gsd_in_pre_1_0_version(self) -> None:
        eo_item = pystac.Item.from_file(
            TestCases.get_path(
                "data-files/examples/0.9.0/item-spec/examples/" "landsat8-sample.json"
            )
        )

        self.assertEqual(eo_item.common_metadata.gsd, 30.0)

    def test_item_apply(self) -> None:
        item = pystac.Item.from_file(self.LANDSAT_EXAMPLE_URI)
        eo_ext = EOExtension.ext(item)
        test_band = Band.create(name="test")

        self.assertEqual(eo_ext.cloud_cover, 78)
        self.assertNotIn(test_band, eo_ext.bands or [])

        eo_ext.apply(bands=[test_band], cloud_cover=15)
        assert eo_ext.bands is not None

        self.assertEqual(test_band.to_dict(), eo_ext.bands[0].to_dict())
        self.assertEqual(eo_ext.cloud_cover, 15)

    def test_extend_invalid_object(self) -> None:
        link = pystac.Link("child", "https://some-domain.com/some/path/to.json")

        with self.assertRaises(pystac.ExtensionTypeError):
            EOExtension.ext(link)  # type: ignore

    def test_extension_not_implemented(self) -> None:
        # Should raise exception if Item does not include extension URI
        item = pystac.Item.from_file(self.PLAIN_ITEM)

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = EOExtension.ext(item)

        # Should raise exception if owning Item does not include extension URI
        asset = item.assets["thumbnail"]

        with self.assertRaises(pystac.ExtensionNotImplemented):
            _ = EOExtension.ext(asset)

        # Should succeed if Asset has no owner
        ownerless_asset = pystac.Asset.from_dict(asset.to_dict())
        _ = EOExtension.ext(ownerless_asset)

    def test_item_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.PLAIN_ITEM)
        self.assertNotIn(EOExtension.get_schema_uri(), item.stac_extensions)

        _ = EOExtension.ext(item, add_if_missing=True)

        self.assertIn(EOExtension.get_schema_uri(), item.stac_extensions)

    def test_asset_ext_add_to(self) -> None:
        item = pystac.Item.from_file(self.PLAIN_ITEM)
        self.assertNotIn(EOExtension.get_schema_uri(), item.stac_extensions)
        asset = item.assets["thumbnail"]

        _ = EOExtension.ext(asset, add_if_missing=True)

        self.assertIn(EOExtension.get_schema_uri(), item.stac_extensions)

    def test_asset_ext_add_to_ownerless_asset(self) -> None:
        item = pystac.Item.from_file(self.PLAIN_ITEM)
        asset_dict = item.assets["thumbnail"].to_dict()
        asset = pystac.Asset.from_dict(asset_dict)

        with self.assertRaises(pystac.STACError):
            _ = EOExtension.ext(asset, add_if_missing=True)

    def test_should_raise_exception_when_passing_invalid_extension_object(
        self,
    ) -> None:
        self.assertRaisesRegex(
            ExtensionTypeError,
            r"^EOExtension does not apply to type 'object'$",
            EOExtension.ext,
            object(),
        )


class EOMigrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.item_0_8_path = TestCases.get_path(
            "data-files/examples/0.8.1/item-spec/examples/sentinel2-sample.json"
        )

    def test_migration(self) -> None:
        with open(self.item_0_8_path) as src:
            item_dict = json.load(src)

        self.assertIn("eo:epsg", item_dict["properties"])

        item = Item.from_file(self.item_0_8_path)

        self.assertNotIn("eo:epsg", item.properties)
        self.assertIn("proj:code", item.properties)
        self.assertIn(ProjectionExtension.get_schema_uri(), item.stac_extensions)
        assert item.ext.proj.epsg == item_dict["properties"]["eo:epsg"]


@pytest.fixture
def ext_item_uri() -> str:
    return get_data_file("eo/eo-landsat-example.json")


@pytest.fixture
def ext_item(ext_item_uri: str) -> pystac.Item:
    return pystac.Item.from_file(ext_item_uri)


def test_to_from_dict(ext_item_uri: str, ext_item: pystac.Item) -> None:
    with open(ext_item_uri) as f:
        d = json.load(f)
    actual = ext_item.to_dict(include_self_link=False)
    assert actual == d


@pytest.mark.parametrize("field", ["cloud_cover", "snow_cover"])
def test_get_field(ext_item: pystac.Item, field: str) -> None:
    prop = ext_item.properties[f"{PREFIX}{field}"]
    attr = getattr(EOExtension.ext(ext_item), field)

    assert attr is not None
    assert attr == prop


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "field,value",
    [
        ("cloud_cover", 7.8),
        ("snow_cover", 99),
    ],
)
def test_set_field(ext_item: pystac.Item, field: str, value) -> None:  # type: ignore
    original = ext_item.properties[f"{PREFIX}{field}"]
    setattr(EOExtension.ext(ext_item), field, value)
    new = ext_item.properties[f"{PREFIX}{field}"]

    assert new != original
    assert new == value
    assert ext_item.validate()


def test_snow_cover_set_to_none_pops_from_dict(ext_item: pystac.Item) -> None:
    assert SNOW_COVER_PROP in ext_item.properties

    EOExtension.ext(ext_item).snow_cover = None
    assert SNOW_COVER_PROP not in ext_item.properties


def test_snow_cover_raises_informative_error(ext_item: pystac.Item) -> None:
    with pytest.raises(ValueError, match="must be number"):
        EOExtension.ext(ext_item).snow_cover = True

    with pytest.raises(ValueError, match="must be between 0 and 100"):
        EOExtension.ext(ext_item).snow_cover = 100.5


def test_older_extension_version(ext_item: Item) -> None:
    old = "https://stac-extensions.github.io/eo/v1.0.0/schema.json"
    new = "https://stac-extensions.github.io/eo/v1.1.0/schema.json"

    stac_extensions = set(ext_item.stac_extensions)
    stac_extensions.remove(new)
    stac_extensions.add(old)
    item_as_dict = ext_item.to_dict(include_self_link=False, transform_hrefs=False)
    item_as_dict["stac_extensions"] = list(stac_extensions)
    item = Item.from_dict(item_as_dict)
    assert EOExtension.has_extension(item)
    assert old in item.stac_extensions

    migrated_item = pystac.Item.from_dict(item_as_dict, migrate=True)
    assert EOExtension.has_extension(migrated_item)
    assert new in migrated_item.stac_extensions


@pytest.mark.parametrize(
    "filter,count",
    [
        (dict(), 11),
        ({"name": "B4"}, 1),
        ({"common_name": "blue"}, 1),
        ({"name": "B4", "common_name": "red"}, 1),
        ({"name": "B4", "common_name": "green"}, 0),
    ],
)
def test_get_assets(ext_item: pystac.Item, filter: dict[str, str], count: int) -> None:
    assets = EOExtension.ext(ext_item).get_assets(**filter)  # type:ignore
    assert len(assets) == count


def test_get_assets_works_even_if_band_info_is_incomplete(
    ext_item: pystac.Item,
) -> None:
    name = ext_item.assets["B4"].extra_fields["eo:bands"][0].pop("name")
    common_name = ext_item.assets["B2"].extra_fields["eo:bands"][0].pop("common_name")

    eo_ext = EOExtension.ext(ext_item)

    assets = eo_ext.get_assets(name=name)  # type:ignore
    assert len(assets) == 0

    assets = eo_ext.get_assets(common_name=common_name)  # type:ignore
    assert len(assets) == 0


def test_exception_should_include_hint_if_obj_is_collection(
    collection: pystac.Collection,
) -> None:
    with pytest.raises(
        ExtensionTypeError,
        match="Hint: Did you mean to use `EOExtension.summaries` instead?",
    ):
        EOExtension.ext(collection)  # type:ignore


def test_ext_syntax(ext_item: pystac.Item) -> None:
    assert ext_item.ext.eo.cloud_cover == 78
    assert (bands := ext_item.assets["B1"].ext.eo.bands)
    assert bands[0].name == "B1"


def test_ext_syntax_remove(ext_item: pystac.Item) -> None:
    ext_item.ext.remove("eo")
    assert ext_item.ext.has("eo") is False
    with pytest.raises(ExtensionNotImplemented):
        ext_item.ext.eo


def test_ext_syntax_add(item: pystac.Item) -> None:
    item.ext.add("eo")
    assert item.ext.has("eo") is True
    assert isinstance(item.ext.eo, EOExtension)


def test_required_property_missing(ext_item: pystac.Item) -> None:
    # https://github.com/stac-utils/pystac/issues/1402
    d = ext_item.to_dict(include_self_link=False, transform_hrefs=False)
    del d["assets"]["B1"]["eo:bands"][0]["name"]
    item = pystac.Item.from_dict(d)
    bands = item.assets["B1"].ext.eo.bands
    assert bands is not None
    with pytest.raises(RequiredPropertyMissing):
        bands[0].name
