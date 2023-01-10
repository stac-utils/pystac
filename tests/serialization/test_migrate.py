import pytest

import pystac
from pystac import ExtensionTypeError
from pystac.cache import CollectionCache
from pystac.extensions.item_assets import ItemAssetsExtension
from pystac.extensions.view import ViewExtension
from pystac.serialization import (
    identify_stac_object,
    identify_stac_object_type,
    merge_common_properties,
    migrate_to_latest,
)
from pystac.utils import get_required, str_to_datetime
from tests.utils import TestCases
from tests.utils.test_cases import ExampleInfo


class TestMigrate:
    @pytest.mark.parametrize("example", TestCases.get_examples_info())
    def test_migrate(self, example: ExampleInfo) -> None:
        collection_cache = CollectionCache()
        path = example.path

        d = pystac.StacIO.default().read_json(path)
        if identify_stac_object_type(d) == pystac.STACObjectType.ITEM:
            merge_common_properties(
                d, json_href=path, collection_cache=collection_cache
            )

        info = identify_stac_object(d)

        migrated_d = migrate_to_latest(d, info)

        migrated_info = identify_stac_object(migrated_d)

        assert migrated_info.object_type == info.object_type
        assert (
            migrated_info.version_range.latest_valid_version()
            == pystac.get_stac_version()
        )

        # Ensure all stac_extensions are schema URIs
        for e_id in migrated_d["stac_extensions"]:
            assert e_id.endswith(".json"), f"{e_id} is not a JSON schema URI"

    def test_migrates_removed_extension(self) -> None:
        item = pystac.Item.from_file(
            TestCases.get_path(
                "data-files/examples/0.8.1/extensions/sar/examples/sentinel1.json"
            )
        )
        assert "dtr" not in item.stac_extensions
        assert item.common_metadata.start_datetime == str_to_datetime(
            "2018-11-03T23:58:55.121559Z"
        )

    def test_migrates_added_extension(self) -> None:
        item = pystac.Item.from_file(
            TestCases.get_path(
                "data-files/examples/0.8.1/item-spec/" "examples/planet-sample.json"
            )
        )
        assert ViewExtension.has_extension(item)
        view_ext = ViewExtension.ext(item)
        assert view_ext.sun_azimuth, 101.8
        assert view_ext.sun_elevation, 58.8
        assert view_ext.off_nadir, 1

    def test_migrates_renamed_extension(self) -> None:
        collection = pystac.Collection.from_file(
            TestCases.get_path(
                "data-files/examples/0.9.0/extensions/asset/"
                "examples/example-landsat8.json"
            )
        )

        assert ItemAssetsExtension.has_extension(collection)
        assert "item_assets" in collection.extra_fields

    def test_migrates_pre_1_0_0_rc1_stats_summary(self) -> None:
        collection = pystac.Collection.from_file(
            TestCases.get_path(
                "data-files/examples/1.0.0-beta.2/collection-spec/"
                "examples/sentinel2.json"
            )
        )
        datetime_summary = get_required(
            collection.summaries.get_range("datetime"), collection.summaries, "datetime"
        )
        assert datetime_summary.minimum == "2015-06-23T00:00:00Z"
        assert datetime_summary.maximum, "2019-07-10T13:44:56Z"

    def test_should_raise_exception_when_passing_invalid_extension_object(
        self,
    ) -> None:
        with pytest.raises(
            ExtensionTypeError,
            match=r"^Item Assets extension does not apply to type 'object'$",
        ):
            ItemAssetsExtension.ext(object())  # type: ignore
