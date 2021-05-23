import os
from datetime import datetime
import csv
from typing import Any, Dict, List

import pystac
from pystac import (
    Catalog,
    Collection,
    Item,
    Asset,
    Extent,
    TemporalExtent,
    SpatialExtent,
    MediaType,
)
from pystac.extensions.label import (
    LabelExtension,
    LabelOverview,
    LabelClasses,
    LabelCount,
    LabelType,
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

ARBITRARY_GEOM: Dict[str, Any] = {
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

ARBITRARY_BBOX: List[float] = [
    ARBITRARY_GEOM["coordinates"][0][0][0],
    ARBITRARY_GEOM["coordinates"][0][0][1],
    ARBITRARY_GEOM["coordinates"][0][1][0],
    ARBITRARY_GEOM["coordinates"][0][1][1],
]

ARBITRARY_EXTENT = Extent(
    spatial=SpatialExtent.from_coordinates(ARBITRARY_GEOM["coordinates"]),
    temporal=TemporalExtent.from_now(),
)  # noqa: E126


class ExampleInfo:
    def __init__(
        self,
        path: str,
        object_type: pystac.STACObjectType,
        stac_version: str,
        extensions: List[str],
        valid: bool,
    ) -> None:
        self.path = path
        self.object_type = object_type
        self.stac_version = stac_version
        self.extensions = extensions
        self.valid = valid


class TestCases:
    @staticmethod
    def get_path(rel_path: str) -> str:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", rel_path))

    @staticmethod
    def get_examples_info() -> List[ExampleInfo]:
        examples: List[ExampleInfo] = []

        info_path = TestCases.get_path("data-files/examples/example-info.csv")
        with open(TestCases.get_path("data-files/examples/example-info.csv")) as f:
            for row in csv.reader(f):
                path = os.path.abspath(os.path.join(os.path.dirname(info_path), row[0]))
                object_type = row[1]
                stac_version = row[2]
                extensions: List[str] = []
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
    def all_test_catalogs() -> List[Catalog]:
        return [
            TestCases.test_case_1(),
            TestCases.test_case_2(),
            TestCases.test_case_3(),
            TestCases.test_case_4(),
            TestCases.test_case_5(),
            TestCases.test_case_7(),
            TestCases.test_case_8(),
        ]

    @staticmethod
    def test_case_1() -> Catalog:
        return Catalog.from_file(
            TestCases.get_path("data-files/catalogs/test-case-1/catalog.json")
        )

    @staticmethod
    def test_case_2() -> Catalog:
        return Catalog.from_file(
            TestCases.get_path("data-files/catalogs/test-case-2/catalog.json")
        )

    @staticmethod
    def test_case_3() -> Catalog:
        root_cat = Catalog(
            id="test3", description="test case 3 catalog", title="test case 3 title"
        )

        image_item = Item(
            id="imagery-item",
            geometry=ARBITRARY_GEOM,
            bbox=ARBITRARY_BBOX,
            datetime=datetime.utcnow(),
            properties={},
        )

        image_item.add_asset(
            "ortho", Asset(href="some/geotiff.tiff", media_type=MediaType.GEOTIFF)
        )

        overviews = [
            LabelOverview.create(
                "label",
                counts=[LabelCount.create("one", 1), LabelCount.create("two", 2)],
            )
        ]

        label_item = Item(
            id="label-items",
            geometry=ARBITRARY_GEOM,
            bbox=ARBITRARY_BBOX,
            datetime=datetime.utcnow(),
            properties={},
        )

        LabelExtension.add_to(label_item)
        label_ext = LabelExtension.ext(label_item)
        label_ext.apply(
            label_description="ML Labels",
            label_type=LabelType.VECTOR,
            label_properties=["label"],
            label_classes=[LabelClasses.create(classes=["one", "two"], name="label")],
            label_tasks=["classification"],
            label_methods=["manual"],
            label_overviews=overviews,
        )
        label_ext.add_source(image_item, assets=["ortho"])

        root_cat.add_item(image_item)
        root_cat.add_item(label_item)

        return root_cat

    @staticmethod
    def test_case_4():
        """Test case that is based on a local copy of the Tier 1 dataset from
        DrivenData's OpenCities AI Challenge.
        See: https://www.drivendata.org/competitions/60/building-segmentation-disaster-resilience
        """  # noqa
        return Catalog.from_file(
            TestCases.get_path("data-files/catalogs/test-case-4/catalog.json")
        )

    @staticmethod
    def test_case_5():
        """Based on a subset of https://cbers.stac.cloud/"""
        return Catalog.from_file(
            TestCases.get_path("data-files/catalogs/test-case-5/catalog.json")
        )

    @staticmethod
    def test_case_6():
        """Based on a subset of CBERS, contains a root and 4 empty children"""
        return Catalog.from_file(
            TestCases.get_path("data-files/catalogs/cbers-partial/catalog.json")
        )

    @staticmethod
    def test_case_7():
        """Test case 4 as STAC version 0.8.1"""
        return Catalog.from_file(
            TestCases.get_path("data-files/catalogs/label_catalog-v0.8.1/catalog.json")
        )

    @staticmethod
    def test_case_8() -> Collection:
        """Planet disaster data example catalog, 1.0.0-beta.2"""
        return Collection.from_file(
            TestCases.get_path(
                "data-files/catalogs/" "planet-example-v1.0.0-beta.2/collection.json"
            )
        )
