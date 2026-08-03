from __future__ import annotations

from datetime import datetime
from typing import TypeAlias

import pytest

import pystac
from pystac.extensions.osc import (
    EXPERIMENT_PROP,
    MISSIONS_PROP,
    OSC_EXTENSION_HOOKS,
    PROJECT_PROP,
    REGION_PROP,
    SCHEMA_URI,
    STATUS_PROP,
    TYPE_PROP,
    VARIABLES_PROP,
    WORKFLOWS_PROP,
    OscExtension,
    OscStatus,
    OscType,
)

TemporalIntervals: TypeAlias = list[list[datetime | None]]


def make_item() -> pystac.Item:
    return pystac.Item(
        id="product-item",
        geometry={"type": "Point", "coordinates": [0.0, 0.0]},
        bbox=[0.0, 0.0, 0.0, 0.0],
        datetime=pystac.utils.str_to_datetime("2026-01-01T00:00:00Z"),
        properties={},
    )


def make_collection() -> pystac.Collection:
    temporal_intervals: TemporalIntervals = [[None, None]]
    return pystac.Collection(
        id="science-project",
        description="Test science project",
        extent=pystac.Extent(
            pystac.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
            pystac.TemporalExtent(temporal_intervals),
        ),
        license="proprietary",
    )


def test_enum_values_match_schema() -> None:
    assert {value.value for value in OscType} == {"project", "product"}
    assert {value.value for value in OscStatus} == {
        "planned",
        "ongoing",
        "completed",
    }


def test_apply_project_to_collection_and_accessor() -> None:
    collection = make_collection()
    ext = OscExtension.ext(collection, add_if_missing=True)
    ext.apply_project(
        status=OscStatus.ONGOING,
        workflows=["water-cycle-workflow", "atmosphere-workflow"],
    )

    assert SCHEMA_URI in collection.stac_extensions
    assert collection.extra_fields == {
        TYPE_PROP: "project",
        STATUS_PROP: "ongoing",
        WORKFLOWS_PROP: ["water-cycle-workflow", "atmosphere-workflow"],
    }
    assert ext.osc_type == OscType.PROJECT
    assert ext.status == OscStatus.ONGOING
    assert ext.workflows == ["water-cycle-workflow", "atmosphere-workflow"]
    assert collection.ext.osc.osc_type == OscType.PROJECT


def test_apply_product_to_item_roundtrip() -> None:
    item = make_item()
    ext = OscExtension.ext(item, add_if_missing=True)
    ext.apply_product(
        status=OscStatus.COMPLETED,
        project="ocean-science-project",
        region="Arctic",
        variables=["Sea surface temperature", "Wind stress"],
        missions=["Sentinel-1", "Sentinel-3"],
        experiment="experiment-42",
    )

    assert item.properties[TYPE_PROP] == "product"
    assert item.properties[STATUS_PROP] == "completed"
    assert item.properties[PROJECT_PROP] == "ocean-science-project"
    assert item.properties[REGION_PROP] == "Arctic"
    assert item.properties[VARIABLES_PROP] == [
        "Sea surface temperature",
        "Wind stress",
    ]
    assert item.properties[MISSIONS_PROP] == ["Sentinel-1", "Sentinel-3"]
    assert item.properties[EXPERIMENT_PROP] == "experiment-42"
    assert WORKFLOWS_PROP not in item.properties

    roundtripped = pystac.Item.from_dict(item.to_dict())
    roundtripped_ext = OscExtension.ext(roundtripped)
    assert roundtripped_ext.osc_type == OscType.PRODUCT
    assert roundtripped_ext.status == OscStatus.COMPLETED
    assert roundtripped_ext.project == "ocean-science-project"
    assert roundtripped_ext.region == "Arctic"
    assert roundtripped_ext.variables == [
        "Sea surface temperature",
        "Wind stress",
    ]
    assert roundtripped_ext.missions == ["Sentinel-1", "Sentinel-3"]
    assert roundtripped_ext.experiment == "experiment-42"
    assert roundtripped.ext.osc.project == "ocean-science-project"


def test_switching_shapes_removes_mutually_exclusive_fields() -> None:
    item = make_item()
    ext = OscExtension.ext(item, add_if_missing=True)
    ext.apply_product(
        status=OscStatus.PLANNED,
        project="project-1",
        region="Agulhas",
        variables=["Ocean colour"],
        missions=["Sentinel-3"],
        experiment="experiment-1",
    )
    ext.apply_project(status=OscStatus.ONGOING, workflows=["workflow-1"])

    assert item.properties == {
        TYPE_PROP: "project",
        STATUS_PROP: "ongoing",
        WORKFLOWS_PROP: ["workflow-1"],
    }

    ext.apply_product(status=OscStatus.COMPLETED, project="project-2")
    assert item.properties == {
        TYPE_PROP: "product",
        STATUS_PROP: "completed",
        PROJECT_PROP: "project-2",
    }


def test_catalog_support() -> None:
    catalog = pystac.Catalog(id="project-catalog", description="Project catalog")
    ext = OscExtension.ext(catalog, add_if_missing=True)
    ext.apply_project(status=OscStatus.PLANNED)

    assert catalog.extra_fields == {
        TYPE_PROP: "project",
        STATUS_PROP: "planned",
    }
    assert catalog.ext.osc.status == OscStatus.PLANNED


def test_optional_properties_can_be_cleared() -> None:
    item = make_item()
    ext = OscExtension.ext(item, add_if_missing=True)
    ext.apply_product(
        status=OscStatus.ONGOING,
        project="project-1",
        region="Arctic",
        variables=["Wind stress"],
        missions=["Aeolus"],
        experiment="experiment-1",
    )

    ext.region = None
    ext.variables = None
    ext.missions = None
    ext.experiment = None

    assert REGION_PROP not in item.properties
    assert VARIABLES_PROP not in item.properties
    assert MISSIONS_PROP not in item.properties
    assert EXPERIMENT_PROP not in item.properties


def test_ext_requires_existing_extension_when_not_adding() -> None:
    with pytest.raises(pystac.ExtensionNotImplemented):
        OscExtension.ext(make_item())


def test_ext_rejects_unsupported_type() -> None:
    with pytest.raises(pystac.ExtensionTypeError):
        OscExtension.ext("not-a-stac-object")  # type: ignore[type-var]


def test_extension_hooks_are_declared() -> None:
    assert OSC_EXTENSION_HOOKS.schema_uri == OscExtension.get_schema_uri()
    assert OSC_EXTENSION_HOOKS.prev_extension_ids == set()
    assert pystac.STACObjectType.CATALOG in OSC_EXTENSION_HOOKS.stac_object_types
    assert pystac.STACObjectType.COLLECTION in OSC_EXTENSION_HOOKS.stac_object_types
    assert pystac.STACObjectType.ITEM in OSC_EXTENSION_HOOKS.stac_object_types
