"""Tests for pystac.extensions.version."""

from collections.abc import Generator
from datetime import datetime

import pytest

from pystac import (
    Asset,
    Catalog,
    Collection,
    ExtensionNotImplemented,
    Extent,
    Item,
    SpatialExtent,
    TemporalExtent,
)
from pystac.errors import DeprecatedWarning, ExtensionTypeError
from pystac.extensions.version import (
    DEPRECATED,
    VERSION,
    VersionExtension,
    VersionRelType,
    ignore_deprecated,
)
from tests.v1.utils import TestCases

URL_TEMPLATE: str = "http://example.com/catalog/%s.json"


@pytest.fixture
def item() -> Item:
    return make_item(2011)


@pytest.fixture
def item_from_file() -> Item:
    return Item.from_file(TestCases.get_path("data-files/version/item.json"))


@pytest.fixture
def collection() -> Collection:
    return make_collection(2011)


@pytest.fixture
def catalog() -> Catalog:
    return make_catalog(2011)


@pytest.fixture
def version() -> str:
    return "1.2.3"


def make_item(year: int) -> Item:
    """Create basic test items that are only slightly different."""
    asset_id = f"USGS/GAP/CONUS/{year}"
    start = datetime(year, 1, 2)

    item = Item(id=asset_id, geometry=None, bbox=None, datetime=start, properties={})
    item.set_self_href(URL_TEMPLATE % year)

    VersionExtension.add_to(item)

    return item


def make_collection(year: int) -> Collection:
    asset_id = f"my/collection/of/things/{year}"
    start = datetime(2014, 8, 10)
    end = datetime(year, 1, 3, 4, 5)
    bboxes = [[-180.0, -90.0, 180.0, 90.0]]
    spatial_extent = SpatialExtent(bboxes)
    intervals: list[list[datetime | None]] = [[start, end]]
    temporal_extent = TemporalExtent(intervals)
    extent = Extent(spatial_extent, temporal_extent)

    collection = Collection(asset_id, "desc", extent)
    collection.set_self_href(URL_TEMPLATE % year)

    VersionExtension.add_to(collection)

    return collection


def make_catalog(year: int) -> Catalog:
    """Create basic test catalogs that are only slightly different."""
    asset_id = f"USGS/GAP/CONUS/{year}"

    catalog = Catalog(id=asset_id, description=str(year))
    VersionExtension.add_to(catalog)

    return catalog


def test_should_raise_exception_when_passing_invalid_extension_object() -> None:
    with pytest.raises(
        ExtensionTypeError, match="^VersionExtension does not apply to type 'object'$"
    ):
        VersionExtension.ext(object())  # type: ignore


def test_rel_types() -> None:
    assert VersionRelType.LATEST.value == "latest-version"
    assert VersionRelType.PREDECESSOR.value == "predecessor-version"
    assert VersionRelType.SUCCESSOR.value == "successor-version"


def test_stac_extensions(item: Item) -> None:
    assert item.ext.has("version")


@pytest.mark.vcr()
def test_add_version(item: Item, version: str) -> None:
    item.ext.version.apply(version)
    assert version == item.ext.version.version
    assert DEPRECATED not in item.properties
    assert not item.ext.version.deprecated
    item.validate()


@pytest.mark.vcr()
def test_version_in_properties(item: Item, version: str) -> None:
    item.ext.version.apply(version, deprecated=True)
    assert VERSION in item.properties
    assert DEPRECATED in item.properties
    item.validate()


@pytest.mark.vcr()
def test_add_not_deprecated_version(item: Item, version: str) -> None:
    item.ext.version.apply(version, deprecated=False)
    assert DEPRECATED in item.properties
    assert not item.ext.version.deprecated
    item.validate()


@pytest.mark.vcr()
def test_add_deprecated_version(item: Item, version: str) -> None:
    item.ext.version.apply(version, deprecated=True)
    assert DEPRECATED in item.properties
    assert item.ext.version.deprecated
    item.validate()


@pytest.mark.vcr()
def test_latest(item: Item, version: str) -> None:
    year = 2013
    latest = make_item(year)
    item.ext.version.apply(version, latest=latest)
    assert item.ext.version.latest is latest
    expected_href = URL_TEMPLATE % year
    link = item.get_links(VersionRelType.LATEST)[0]
    assert expected_href == link.get_href()
    item.validate()


@pytest.mark.vcr()
def test_predecessor(item: Item, version: str) -> None:
    year = 2010
    predecessor = make_item(year)
    item.ext.version.apply(version, predecessor=predecessor)
    assert item.ext.version.predecessor is predecessor
    expected_href = URL_TEMPLATE % year
    link = item.get_links(VersionRelType.PREDECESSOR)[0]
    assert expected_href == link.get_href()
    item.validate()


@pytest.mark.vcr()
def test_successor(item: Item, version: str) -> None:
    year = 2012
    successor = make_item(year)
    item.ext.version.apply(version, successor=successor)
    assert item.ext.version.successor is successor
    expected_href = URL_TEMPLATE % year
    link = item.get_links(VersionRelType.SUCCESSOR)[0]
    assert expected_href == link.get_href()
    item.validate()


@pytest.mark.vcr()
def test_all_links(item: Item, version: str) -> None:
    deprecated = True
    latest = make_item(2013)
    predecessor = make_item(2010)
    successor = make_item(2012)
    item.ext.version.apply(
        version,
        deprecated=deprecated,
        latest=latest,
        predecessor=predecessor,
        successor=successor,
    )
    item.validate()


def test_full_copy(test_case_1_catalog: Catalog) -> None:
    # Fetch two items from the catalog
    item1 = next(test_case_1_catalog.get_items("area-1-1-imagery", recursive=True))
    item2 = next(test_case_1_catalog.get_items("area-2-2-imagery", recursive=True))

    # Enable the version extension on each, and link them
    # as if they are different versions of the same Item
    item1.ext.add("version")
    item2.ext.add("version")

    item1.ext.version.apply(version="2.0", predecessor=item2)
    item2.ext.version.apply(version="1.0", successor=item1, latest=item1)

    # Make a full copy of the catalog
    cat_copy = test_case_1_catalog.full_copy()

    # Retrieve the copied version of the items
    item1_copy = next(cat_copy.get_items("area-1-1-imagery", recursive=True))
    item2_copy = next(cat_copy.get_items("area-2-2-imagery", recursive=True))

    # Check to see if the version links point to the instances of the
    # item objects as they should.

    predecessor = item1_copy.get_single_link(VersionRelType.PREDECESSOR)
    assert predecessor is not None
    predecessor_target = predecessor.target
    successor = item2_copy.get_single_link(VersionRelType.SUCCESSOR)
    assert successor is not None
    successor_target = successor.target
    latest = item2_copy.get_single_link(VersionRelType.LATEST)
    assert latest is not None
    latest_target = latest.target

    assert predecessor_target is item2_copy
    assert successor_target is item1_copy
    assert latest_target is item1_copy


def test_setting_none_clears_link(item: Item, version: str) -> None:
    deprecated = False
    latest = make_item(2013)
    predecessor = make_item(2010)
    successor = make_item(2012)
    item.ext.version.apply(
        version, deprecated, latest=latest, predecessor=predecessor, successor=successor
    )

    item.ext.version.latest = None
    links = item.get_links(VersionRelType.LATEST)
    assert 0 == len(links)

    item.ext.version.predecessor = None
    links = item.get_links(VersionRelType.PREDECESSOR)
    assert 0 == len(links)

    item.ext.version.successor = None
    links = item.get_links(VersionRelType.SUCCESSOR)
    assert 0 == len(links)


def test_multiple_link_setting(item: Item, version: str) -> None:
    deprecated = False
    latest1 = make_item(2013)
    predecessor1 = make_item(2010)
    successor1 = make_item(2012)
    item.ext.version.apply(
        version,
        deprecated,
        latest=latest1,
        predecessor=predecessor1,
        successor=successor1,
    )

    year = 2015
    latest2 = make_item(year)
    expected_href = URL_TEMPLATE % year
    item.ext.version.latest = latest2
    links = item.get_links(VersionRelType.LATEST)
    assert 1 == len(links)
    assert expected_href == links[0].get_href()

    year = 2009
    predecessor2 = make_item(year)
    expected_href = URL_TEMPLATE % year
    item.ext.version.predecessor = predecessor2
    links = item.get_links(VersionRelType.PREDECESSOR)
    assert 1 == len(links)
    assert expected_href == links[0].get_href()

    year = 2014
    successor2 = make_item(year)
    expected_href = URL_TEMPLATE % year
    item.ext.version.successor = successor2
    links = item.get_links(VersionRelType.SUCCESSOR)
    assert 1 == len(links)
    assert expected_href == links[0].get_href()


def test_extension_not_implemented(item_from_file: Item) -> None:
    # Should raise exception if Item does not include extension URI
    item_from_file.stac_extensions.remove(VersionExtension.get_schema_uri())
    with pytest.raises(ExtensionNotImplemented):
        item_from_file.ext.version


def test_ext_add_to(item_from_file: Item) -> None:
    item_from_file.stac_extensions.remove(VersionExtension.get_schema_uri())
    item_from_file.ext.add("version")
    assert VersionExtension.get_schema_uri() in item_from_file.stac_extensions


def test_collection_stac_extensions(collection: Collection) -> None:
    assert collection.ext.has("version")


@pytest.mark.vcr()
def test_collection_add_version(collection: Collection, version: str) -> None:
    collection.ext.version.apply(version)
    assert collection.ext.version.version == version
    assert DEPRECATED not in collection.extra_fields
    collection.validate()


@pytest.mark.vcr()
def test_collection_validate_all(collection: Collection, version: str) -> None:
    deprecated = True
    latest = make_collection(2013)
    predecessor = make_collection(2010)
    successor = make_collection(2012)
    collection.ext.version.apply(
        version, deprecated, latest=latest, predecessor=predecessor, successor=successor
    )

    links = collection.get_links(VersionRelType.LATEST)
    assert 1 == len(links)
    links = collection.get_links(VersionRelType.PREDECESSOR)
    assert 1 == len(links)
    links = collection.get_links(VersionRelType.SUCCESSOR)
    assert 1 == len(links)

    collection.validate()


def test_catalog_stac_extensions(catalog: Catalog) -> None:
    assert catalog.ext.has("version")


@pytest.mark.vcr()
def test_catalog_add_version(catalog: Catalog, version: str) -> None:
    catalog.ext.version.apply(version)
    assert catalog.ext.version.version == version
    assert DEPRECATED not in catalog.extra_fields
    catalog.validate()


@pytest.mark.vcr()
def test_catalog_validate_all(catalog: Catalog, version: str) -> None:
    deprecated = True
    latest = make_collection(2013)
    predecessor = make_collection(2010)
    successor = make_collection(2012)
    catalog.ext.version.apply(
        version, deprecated, latest=latest, predecessor=predecessor, successor=successor
    )

    links = catalog.get_links(VersionRelType.LATEST)
    assert 1 == len(links)
    links = catalog.get_links(VersionRelType.PREDECESSOR)
    assert 1 == len(links)
    links = catalog.get_links(VersionRelType.SUCCESSOR)
    assert 1 == len(links)

    catalog.validate()


def test_item_deprecation_warning(
    item: Item, recwarn: Generator[pytest.WarningsRecorder, None, None]
) -> None:
    item.ext.version.deprecated = True
    item_dict = item.to_dict()
    with pytest.warns(DeprecatedWarning, match="The item '.*' is deprecated."):
        _ = Item.from_dict(item_dict)

    item.ext.version.deprecated = False
    item_dict = item.to_dict()
    _ = Item.from_dict(item_dict)
    assert len(list(recwarn)) == 0

    item.ext.version.deprecated = None
    item_dict = item.to_dict()
    _ = Item.from_dict(item_dict)
    assert len(list(recwarn)) == 0

    item.ext.remove("version")
    item_dict = item.to_dict()
    _ = Item.from_dict(item_dict)
    assert len(list(recwarn)) == 0


def test_collection_deprecation_warning(
    collection: Collection,
    recwarn: Generator[pytest.WarningsRecorder, None, None],
) -> None:
    collection.ext.version.deprecated = True
    collection_dict = collection.to_dict()
    with pytest.warns(DeprecatedWarning, match="The collection '.*' is deprecated."):
        _ = Collection.from_dict(collection_dict)

    collection.ext.version.deprecated = False
    collection_dict = collection.to_dict()
    _ = Collection.from_dict(collection_dict)
    assert len(list(recwarn)) == 0

    collection.ext.version.deprecated = None
    collection_dict = collection.to_dict()
    _ = Collection.from_dict(collection_dict)
    assert len(list(recwarn)) == 0

    collection.ext.remove("version")
    collection_dict = collection.to_dict()
    _ = Collection.from_dict(collection_dict)
    assert len(list(recwarn)) == 0


def test_ignore_deprecated_context_manager(
    item: Item, recwarn: Generator[pytest.WarningsRecorder, None, None]
) -> None:
    version = VersionExtension.ext(item, add_if_missing=True)
    version.deprecated = True
    item_dict = item.to_dict()
    with ignore_deprecated():
        _ = Item.from_dict(item_dict)
    assert len(list(recwarn)) == 0


def test_experimental(item: Item) -> None:
    # Added in v1.2.0
    assert item.ext.version.experimental is None
    assert "experimental" not in item.properties
    item.ext.version.experimental = True
    assert item.ext.version.experimental
    assert item.properties["experimental"]
    item.ext.version.experimental = False
    assert not item.properties["experimental"]
    item.ext.version.experimental = None
    assert "experimental" not in item.properties


@pytest.mark.vcr
def test_optional_version(item: Item) -> None:
    # Changed in v1.1.0
    assert item.ext.version.version is None
    assert "version" not in item.properties
    item.validate()
    item.ext.version.version = "final_final_2"
    assert "version" in item.properties
    item.ext.version.version = None
    assert "version" not in item.properties


@pytest.mark.vcr
def test_assets(item: Item) -> None:
    item.ext.remove("version")
    asset = Asset("example.tif")
    item.add_asset("data", asset)

    assert not asset.ext.has("version")
    asset.ext.add("version")
    assert asset.ext.has("version")
    assert item.ext.has("version")

    asset.ext.version.version = "final_final_2"
    assert asset.ext.version.version == "final_final_2"
    assert "version" in asset.extra_fields

    item.validate()


@pytest.mark.parametrize("version", ["v1.0.0", "v1.1.0"])
def test_migrate(version: str, item: Item) -> None:
    item_dict = item.to_dict(include_self_link=False, transform_hrefs=False)
    item_dict["stac_extensions"] = [
        f"https://stac-extensions.github.io/version/{version}/schema.json"
    ]
    item = Item.from_dict(item_dict, migrate=True)
    assert (
        "https://stac-extensions.github.io/version/v1.2.0/schema.json"
        in item.stac_extensions
    )
