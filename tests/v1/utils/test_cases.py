import csv
import os
from datetime import datetime, timezone
from typing import Any

import pystac
from pystac import (
    Asset,
    Catalog,
    Collection,
    Extent,
    Item,
    MediaType,
    SpatialExtent,
    TemporalExtent,
)

TEST_LABEL_CATALOG = {
    "country-1": {
        "area-1-1": {
            "dsm": "area-1-1_dsm.tif",
            "ortho": "area-1-1_ortho.tif",
            "labels": "area-1-1_labels.geojson",
        },
        "area-1-2": {
            "dsm": "area-1-2_dsm.tif",
            "ortho": "area-1-2_ortho.tif",
            "labels": "area-1-2_labels.geojson",
        },
    },
    "country-2": {
        "area-2-1": {
            "dsm": "area-2-1_dsm.tif",
            "ortho": "area-2-1_ortho.tif",
            "labels": "area-2-1_labels.geojson",
        },
        "area-2-2": {
            "dsm": "area-2-2_dsm.tif",
            "ortho": "area-2-2_ortho.tif",
            "labels": "area-2-2_labels.geojson",
        },
    },
}

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

ARBITRARY_EXTENT = Extent(
    spatial=SpatialExtent.from_coordinates(ARBITRARY_GEOM["coordinates"]),
    temporal=TemporalExtent.from_now(),
)


class ExampleInfo:
    def __init__(
        self,
        path: str,
        object_type: pystac.STACObjectType,
        stac_version: str,
        extensions: list[str],
        valid: bool,
    ) -> None:
        self.path = path
        self.object_type = object_type
        self.stac_version = stac_version
        self.extensions = extensions
        self.valid = valid


class TestCases:
    bad_catalog_case = "data-files/catalogs/invalid-catalog/catalog.json"

    @staticmethod
    def get_path(rel_path: str) -> str:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", rel_path))

    @staticmethod
    def get_examples_info() -> list[ExampleInfo]:
        examples: list[ExampleInfo] = []

        info_path = TestCases.get_path("data-files/examples/example-info.csv")
        with open(TestCases.get_path("data-files/examples/example-info.csv")) as f:
            for row in csv.reader(f):
                path = os.path.abspath(os.path.join(os.path.dirname(info_path), row[0]))
                object_type = row[1]
                stac_version = row[2]
                extensions: list[str] = []
                if row[3]:
                    extensions = row[3].split("|")

                valid = True
                if len(row) > 4:
                    # The 5th column will be "INVALID" if the example
                    # shouldn't pass validation
                    valid = row[4] != "INVALID"

                examples.append(
                    ExampleInfo(
                        path=path,
                        object_type=pystac.STACObjectType(object_type),
                        stac_version=stac_version,
                        extensions=extensions,
                        valid=valid,
                    )
                )
        return examples

    @staticmethod
    def all_test_catalogs() -> list[Catalog]:
        return [
            TestCases.case_1(),
            TestCases.case_2(),
            TestCases.case_3(),
            TestCases.case_4(),
            TestCases.case_5(),
            TestCases.case_7(),
            TestCases.case_8(),
        ]

    @staticmethod
    def case_1() -> Catalog:
        return Catalog.from_file(
            TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
        )

    @staticmethod
    def case_2() -> Catalog:
        return Catalog.from_file(
            TestCases.get_path("data-files/catalogs/test-case-2/catalog.json")
        )

    @staticmethod
    def case_3() -> Catalog:
        root_cat = Catalog(
            id="test3", description="test case 3 catalog", title="test case 3 title"
        )

        image_item = Item(
            id="imagery-item",
            geometry=ARBITRARY_GEOM,
            bbox=ARBITRARY_BBOX,
            datetime=datetime.now(timezone.utc),
            properties={},
        )

        image_item.add_asset(
            "ortho", Asset(href="some/geotiff.tiff", media_type=MediaType.GEOTIFF)
        )

        label_item = Item(
            id="label-items",
            geometry=ARBITRARY_GEOM,
            bbox=ARBITRARY_BBOX,
            datetime=datetime.now(timezone.utc),
            properties={},
        )

        root_cat.add_item(image_item)
        root_cat.add_item(label_item)

        return root_cat

    @staticmethod
    def case_4() -> Catalog:
        """Test case that is based on a local copy of the Tier 1 dataset from
        DrivenData's OpenCities AI Challenge.
        See: https://www.drivendata.org/competitions/60/building-segmentation-disaster\
-resilience
        """
        return Catalog.from_file(
            TestCases.get_path("data-files/catalogs/test-case-4/catalog.json")
        )

    @staticmethod
    def case_5() -> Catalog:
        """Based on a subset of https://cbers.stac.cloud/"""
        return Catalog.from_file(
            TestCases.get_path("data-files/catalogs/test-case-5/catalog.json")
        )

    @staticmethod
    def case_6() -> Catalog:
        """Based on a subset of CBERS, contains a root and 4 empty children"""
        return Catalog.from_file(
            TestCases.get_path("data-files/catalogs/cbers-partial/catalog.json")
        )

    @staticmethod
    def case_7() -> Catalog:
        """Test case 4 as STAC version 0.8.1"""
        return Catalog.from_file(
            TestCases.get_path("data-files/catalogs/label_catalog-v0.8.1/catalog.json")
        )

    @staticmethod
    def case_8() -> Collection:
        """Planet disaster data example catalog, 1.0.0-beta.2"""
        return Collection.from_file(
            TestCases.get_path(
                "data-files/catalogs/planet-example-v1.0.0-beta.2/collection.json"
            )
        )
