"""
Description: Test the validator

"""
__authors__ = "Jonathan Healy"

import json
from pystac.validation import validate_dict

with open('test_validation/test_data/1beta1/sample.json') as f:
    js = json.load(f)
result = validate_dict(js)
print(result)

# Core

# 0.7.0 is not functional in pystac validation
def test_collection_local_v070():
    stac_file = "test_validation/test_data/v070/collections/sentinel2.json"
    with open(stac_file) as f:
        js = json.load(f)
    result = validate_dict(js)
    assert result == []


def test_item_local_v080():
    stac_file = "test_validation/test_data/v080/items/sample-full.json"
    with open(stac_file) as f:
        js = json.load(f)
    result = validate_dict(js)
    assert result == []

# remote - figure this out?
# def test_collection_remote_v090():
#     stac_file = "https://raw.githubusercontent.com/stac-utils/pystac/main/tests/data-files/examples/0.9.0/collection-spec/examples/landsat-collection.json"
#     with open(stac_file) as f:
#         js = json.load(f)
#     result = validate_dict(js)
#     assert result == []


def test_item_local_v090():
    stac_file = "test_validation/test_data/v090/items/good_item_v090.json"
    with open(stac_file) as f:
        js = json.load(f)
    result = validate_dict(js)
    assert result == [
        'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.9.0/item-spec/json-schema/item.json', 
        'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.9.0/extensions/eo/json-schema/schema.json', 
        'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.9.0/extensions/view/json-schema/schema.json'
    ]



def test_item_local_extensions_v090():
    stac_file = "tests/test_data/v090/items/CBERS_4.json"
    with open(stac_file) as f:
        js = json.load(f)
    result = validate_dict(js)
    assert result == [
        'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.9.0/item-spec/json-schema/item.json', 
        'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.9.0/extensions/eo/json-schema/schema.json', 
        'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.9.0/extensions/view/json-schema/schema.json'
    ]


def test_core_bad_item_local_v090():
    stac_file = "tests/test_data/bad_data/bad_item_v090.json"
    stac = stac_validator.StacValidate(stac_file, core=True)
    stac.run()
    assert stac.message == [
        {
            "version": "0.9.0",
            "path": "tests/test_data/bad_data/bad_item_v090.json",
            "asset_type": "ITEM",
            "validation_method": "core",
            "schema": ["https://cdn.staclint.com/v0.9.0/item.json"],
            "valid_stac": False,
            "error_type": "ValidationError",
            "error_message": "'id' is a required property of the root of the STAC object",
        }
    ]


def test_core_v1beta1():
    stac_file = "tests/test_data/1beta1/sentinel2.json"
    stac = stac_validator.StacValidate(stac_file, core=True)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-beta.1",
            "path": "tests/test_data/1beta1/sentinel2.json",
            "schema": ["https://cdn.staclint.com/v1.0.0-beta.1/collection.json"],
            "asset_type": "COLLECTION",
            "validation_method": "core",
            "valid_stac": True,
        }
    ]


def test_core_item_local_v1beta2():
    stac_file = "tests/test_data/1beta2/stac_item.json"
    stac = stac_validator.StacValidate(stac_file, core=True)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-beta.2",
            "path": "tests/test_data/1beta2/stac_item.json",
            "schema": [
                "https://schemas.stacspec.org/v1.0.0-beta.2/item-spec/json-schema/item.json"
            ],
            "asset_type": "ITEM",
            "validation_method": "core",
            "valid_stac": True,
        }
    ]


def test_core_item_local_v1rc1():
    stac_file = "tests/test_data/1rc1/collectionless-item.json"
    stac = stac_validator.StacValidate(stac_file, core=True)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-rc.1",
            "path": "tests/test_data/1rc1/collectionless-item.json",
            "schema": [
                "https://schemas.stacspec.org/v1.0.0-rc.1/item-spec/json-schema/item.json"
            ],
            "asset_type": "ITEM",
            "validation_method": "core",
            "valid_stac": True,
        }
    ]


def test_core_collection_local_v1rc1():
    stac_file = "tests/test_data/1rc1/collection.json"
    stac = stac_validator.StacValidate(stac_file, core=True)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-rc.1",
            "path": "tests/test_data/1rc1/collection.json",
            "schema": [
                "https://schemas.stacspec.org/v1.0.0-rc.1/collection-spec/json-schema/collection.json"
            ],
            "asset_type": "COLLECTION",
            "validation_method": "core",
            "valid_stac": True,
        }
    ]


# Custom


def test_custom_item_remote_schema_v080():
    schema = "https://cdn.staclint.com/v0.8.0/item.json"
    stac_file = "tests/test_data/v080/items/digitalglobe-sample.json"
    stac = stac_validator.StacValidate(stac_file, custom=schema)
    stac.run()
    assert stac.message == [
        {
            "version": "0.8.0",
            "path": "tests/test_data/v080/items/digitalglobe-sample.json",
            "schema": ["https://cdn.staclint.com/v0.8.0/item.json"],
            "asset_type": "ITEM",
            "validation_method": "custom",
            "valid_stac": False,
            "error_type": "ValidationError",
            "error_message": "'bbox' is a required property of the root of the STAC object",
        }
    ]


def test_custom_item_remote_schema_v090():
    schema = "https://cdn.staclint.com/v0.9.0/catalog.json"
    stac_file = "https://raw.githubusercontent.com/stac-utils/pystac/main/tests/data-files/examples/0.9.0/collection-spec/examples/landsat-collection.json"
    stac = stac_validator.StacValidate(stac_file, custom=schema)
    stac.run()
    assert stac.message == [
        {
            "version": "0.9.0",
            "path": "https://raw.githubusercontent.com/stac-utils/pystac/main/tests/data-files/examples/0.9.0/collection-spec/examples/landsat-collection.json",
            "schema": ["https://cdn.staclint.com/v0.9.0/catalog.json"],
            "asset_type": "COLLECTION",
            "validation_method": "custom",
            "valid_stac": True,
        }
    ]


def test_custom_item_local_schema_v090():
    schema = "tests/test_data/schema/v0.9.0/catalog.json"

    stac_file = "https://raw.githubusercontent.com/stac-utils/pystac/main/tests/data-files/examples/0.9.0/collection-spec/examples/landsat-collection.json"
    stac = stac_validator.StacValidate(stac_file, custom=schema)
    stac.run()
    assert stac.message == [
        {
            "version": "0.9.0",
            "path": "https://raw.githubusercontent.com/stac-utils/pystac/main/tests/data-files/examples/0.9.0/collection-spec/examples/landsat-collection.json",
            "schema": ["tests/test_data/schema/v0.9.0/catalog.json"],
            "asset_type": "COLLECTION",
            "validation_method": "custom",
            "valid_stac": True,
        }
    ]


def test_custom_bad_item_remote_schema_v090():
    schema = "https://cdn.staclint.com/v0.9.0/item.json"
    stac_file = "tests/test_data/bad_data/bad_item_v090.json"
    stac = stac_validator.StacValidate(stac_file, custom=schema)
    stac.run()
    assert stac.message == [
        {
            "path": "tests/test_data/bad_data/bad_item_v090.json",
            "asset_type": "ITEM",
            "version": "0.9.0",
            "validation_method": "custom",
            "schema": ["https://cdn.staclint.com/v0.9.0/item.json"],
            "valid_stac": False,
            "error_type": "ValidationError",
            "error_message": "'id' is a required property of the root of the STAC object",
        }
    ]


def test_custom_item_remote_schema_v1rc2():
    schema = "https://schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/item.json"

    stac_file = "tests/test_data/1rc2/simple-item.json"
    stac = stac_validator.StacValidate(stac_file, custom=schema)
    stac.run()
    assert stac.message == [
        {
            "path": "tests/test_data/1rc2/simple-item.json",
            "asset_type": "ITEM",
            "version": "1.0.0-rc.2",
            "validation_method": "custom",
            "schema": [
                "https://schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/item.json"
            ],
            "valid_stac": True,
        }
    ]


def test_custom_eo_error_v1rc2():
    schema = "https://stac-extensions.github.io/eo/v1.0.0/schema.json"
    stac_file = (
        "tests/test_data/1rc2/extensions-collection/./proj-example/proj-example.json"
    )
    stac = stac_validator.StacValidate(stac_file, custom=schema)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-rc.2",
            "path": "tests/test_data/1rc2/extensions-collection/./proj-example/proj-example.json",
            "schema": ["https://stac-extensions.github.io/eo/v1.0.0/schema.json"],
            "asset_type": "ITEM",
            "validation_method": "custom",
            "valid_stac": False,
            "error_type": "ValidationError",
            "error_message": "'panchromatic' is not one of ['coastal', 'blue', 'green', 'red', 'rededge', 'yellow', 'pan', 'nir', 'nir08', 'nir09', 'cirrus', 'swir16', 'swir22', 'lwir', 'lwir11', 'lwir12']. Error is in assets -> B8 -> eo:bands -> 0 -> common_name",
        }
    ]


# Default


def test_default_v070():
    stac_file = "https://radarstac.s3.amazonaws.com/stac/catalog.json"
    stac = stac_validator.StacValidate(stac_file)
    stac.run()
    assert stac.message == [
        {
            "version": "0.7.0",
            "path": "https://radarstac.s3.amazonaws.com/stac/catalog.json",
            "asset_type": "CATALOG",
            "validation_method": "default",
            "schema": ["https://cdn.staclint.com/v0.7.0/catalog.json"],
            "valid_stac": True,
        }
    ]


def test_default_item_local_v080():
    stac_file = "tests/test_data/v080/items/sample-full.json"
    stac = stac_validator.StacValidate(stac_file)
    stac.run()
    assert stac.message == [
        {
            "version": "0.8.0",
            "path": "tests/test_data/v080/items/sample-full.json",
            "schema": [
                "https://cdn.staclint.com/v0.8.0/extension/eo.json",
                "https://cdn.staclint.com/v0.8.0/item.json",
            ],
            "asset_type": "ITEM",
            "validation_method": "default",
            "valid_stac": True,
        }
    ]


def test_default_v090():
    stac = stac_validator.StacValidate("tests/test_data/v090/items/good_item_v090.json")
    stac.run()
    print(stac.message)
    assert stac.message == [
        {
            "version": "0.9.0",
            "path": "tests/test_data/v090/items/good_item_v090.json",
            "schema": [
                "https://cdn.staclint.com/v0.9.0/extension/eo.json",
                "https://cdn.staclint.com/v0.9.0/extension/view.json",
                "https://cdn.staclint.com/v0.9.0/item.json",
            ],
            "asset_type": "ITEM",
            "validation_method": "default",
            "valid_stac": True,
        }
    ]


def test_default_v1beta1():
    stac_file = "tests/test_data/1beta1/sentinel2.json"
    stac = stac_validator.StacValidate(stac_file)
    stac.run()
    assert stac.message == [
        {
            "path": "tests/test_data/1beta1/sentinel2.json",
            "asset_type": "COLLECTION",
            "version": "1.0.0-beta.1",
            "validation_method": "default",
            "schema": ["https://cdn.staclint.com/v1.0.0-beta.1/collection.json"],
            "valid_stac": True,
        }
    ]


def test_default_proj_v1b2():
    stac_file = "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l1c/items/S2A_51SXT_20210415_0_L1C"
    stac = stac_validator.StacValidate(stac_file)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-beta.2",
            "path": "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l1c/items/S2A_51SXT_20210415_0_L1C",
            "schema": [
                "https://cdn.staclint.com/v1.0.0-beta.1/extension/eo.json",
                "https://cdn.staclint.com/v1.0.0-beta.1/extension/view.json",
                "https://cdn.staclint.com/v1.0.0-beta.1/extension/projection.json",
                "https://schemas.stacspec.org/v1.0.0-beta.2/item-spec/json-schema/item.json",
            ],
            "asset_type": "ITEM",
            "validation_method": "default",
            "valid_stac": True,
        }
    ]


def test_default_simple_v1rc2():
    stac_file = "tests/test_data/1rc2/simple-item.json"
    stac = stac_validator.StacValidate(stac_file)
    stac.run()
    assert stac.message == [
        {
            "path": "tests/test_data/1rc2/simple-item.json",
            "asset_type": "ITEM",
            "version": "1.0.0-rc.2",
            "validation_method": "default",
            "schema": [
                "https://schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/item.json"
            ],
            "valid_stac": True,
        }
    ]


def test_default_extended_v1rc2():
    stac_file = "tests/test_data/1rc2/extended-item.json"
    stac = stac_validator.StacValidate(stac_file)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-rc.2",
            "path": "tests/test_data/1rc2/extended-item.json",
            "schema": [
                "https://stac-extensions.github.io/eo/v1.0.0/schema.json",
                "https://stac-extensions.github.io/projection/v1.0.0/schema.json",
                "https://stac-extensions.github.io/scientific/v1.0.0/schema.json",
                "https://stac-extensions.github.io/view/v1.0.0/schema.json",
                "https://stac-extensions.github.io/remote-data/v1.0.0/schema.json",
                "https://schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/item.json",
            ],
            "asset_type": "ITEM",
            "validation_method": "default",
            "valid_stac": True,
        }
    ]


def test_default_catalog_v1rc2():
    stac_file = "tests/test_data/1rc2/catalog.json"
    stac = stac_validator.StacValidate(stac_file)
    stac.run()
    assert stac.message == [
        {
            "path": "tests/test_data/1rc2/catalog.json",
            "asset_type": "CATALOG",
            "version": "1.0.0-rc.2",
            "validation_method": "default",
            "schema": [
                "https://schemas.stacspec.org/v1.0.0-rc.2/catalog-spec/json-schema/catalog.json"
            ],
            "valid_stac": True,
        }
    ]


# Extensions


def test_extensions_item_local_v080():
    stac_file = "tests/test_data/v080/items/sample-full.json"
    stac = stac_validator.StacValidate(stac_file, extensions=True)
    stac.run()
    assert stac.message == [
        {
            "version": "0.8.0",
            "path": "tests/test_data/v080/items/sample-full.json",
            "asset_type": "ITEM",
            "validation_method": "extensions",
            "schema": ["https://cdn.staclint.com/v0.8.0/extension/eo.json"],
            "valid_stac": True,
        }
    ]


def test_extensions_v090():
    stac_file = "tests/test_data/v090/extensions/eo/examples/example-landsat8.json"
    stac = stac_validator.StacValidate(stac_file, extensions=True)
    stac.run()
    assert stac.message == [
        {
            "version": "0.9.0",
            "path": "tests/test_data/v090/extensions/eo/examples/example-landsat8.json",
            "asset_type": "ITEM",
            "validation_method": "extensions",
            "schema": [
                "https://cdn.staclint.com/v0.9.0/extension/eo.json",
                "https://cdn.staclint.com/v0.9.0/extension/view.json",
            ],
            "valid_stac": True,
        }
    ]


def test_extensions_v1beta1():
    stac_file = "tests/test_data/1beta1/sentinel2.json"
    stac = stac_validator.StacValidate(stac_file, extensions=True)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-beta.1",
            "path": "tests/test_data/1beta1/sentinel2.json",
            "schema": [
                "https://cdn.staclint.com/v1.0.0-beta.1/collection.json",
            ],
            "asset_type": "COLLECTION",
            "validation_method": "extensions",
            "valid_stac": True,
        }
    ]


def test_no_extensions_v1beta2():
    stac_file = "tests/test_data/1beta2/stac_item.json"
    stac = stac_validator.StacValidate(stac_file, extensions=True)
    stac.run()
    assert stac.message == [
        {
            "path": "tests/test_data/1beta2/stac_item.json",
            "asset_type": "ITEM",
            "version": "1.0.0-beta.2",
            "validation_method": "extensions",
            "schema": [],
            "valid_stac": True,
        }
    ]


def test_extensions_v1beta2():
    stac_file = "tests/test_data/1beta2/CBERS_4.json"
    stac = stac_validator.StacValidate(stac_file, extensions=True)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-beta.2",
            "path": "tests/test_data/1beta2/CBERS_4.json",
            "schema": [
                "https://cdn.staclint.com/v1.0.0-beta.1/extension/projection.json",
                "https://cdn.staclint.com/v1.0.0-beta.1/extension/view.json",
            ],
            "asset_type": "ITEM",
            "validation_method": "extensions",
            "valid_stac": True,
        }
    ]


def test_extensions_remote_v1rc3():
    stac_file = "https://raw.githubusercontent.com/radiantearth/stac-spec/master/examples/extended-item.json"
    stac = stac_validator.StacValidate(stac_file, extensions=True)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-rc.3",
            "path": "https://raw.githubusercontent.com/radiantearth/stac-spec/master/examples/extended-item.json",
            "schema": [
                "https://stac-extensions.github.io/eo/v1.0.0/schema.json",
                "https://stac-extensions.github.io/projection/v1.0.0/schema.json",
                "https://stac-extensions.github.io/scientific/v1.0.0/schema.json",
                "https://stac-extensions.github.io/view/v1.0.0/schema.json",
                "https://stac-extensions.github.io/remote-data/v1.0.0/schema.json",
            ],
            "valid_stac": True,
            "asset_type": "ITEM",
            "validation_method": "extensions",
        }
    ]


def test_extensions_local_v1rc2():
    stac_file = (
        "tests/test_data/1rc2/extensions-collection/./proj-example/proj-example.json"
    )
    stac = stac_validator.StacValidate(stac_file, extensions=True)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-rc.2",
            "path": "tests/test_data/1rc2/extensions-collection/./proj-example/proj-example.json",
            "schema": ["https://stac-extensions.github.io/eo/v1.0.0/schema.json"],
            "valid_stac": False,
            "error_type": "ValidationError",
            "error_message": "'panchromatic' is not one of ['coastal', 'blue', 'green', 'red', 'rededge', 'yellow', 'pan', 'nir', 'nir08', 'nir09', 'cirrus', 'swir16', 'swir22', 'lwir', 'lwir11', 'lwir12']. Error is in assets -> B8 -> eo:bands -> 0 -> common_name",
        }
    ]


def test_extensions_catalog_v1rc2():
    stac_file = "tests/test_data/1rc2/catalog.json"
    stac = stac_validator.StacValidate(stac_file, extensions=True)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-rc.2",
            "path": "tests/test_data/1rc2/catalog.json",
            "schema": [
                "https://schemas.stacspec.org/v1.0.0-rc.2/catalog-spec/json-schema/catalog.json"
            ],
            "asset_type": "CATALOG",
            "validation_method": "extensions",
            "valid_stac": True,
        }
    ]


# Recursive


def test_recursive_lvl_3_v070():
    stac_file = "https://radarstac.s3.amazonaws.com/stac/catalog.json"
    stac = stac_validator.StacValidate(stac_file, recursive=4)
    stac.run()
    assert stac.message == [
        {
            "version": "0.7.0",
            "path": "https://radarstac.s3.amazonaws.com/stac/catalog.json",
            "schema": ["https://cdn.staclint.com/v0.7.0/catalog.json"],
            "asset_type": "CATALOG",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "0.7.0",
            "path": "https://radarstac.s3.amazonaws.com/stac/radarsat-1/collection.json",
            "schema": ["https://cdn.staclint.com/v0.7.0/collection.json"],
            "asset_type": "COLLECTION",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "0.7.0",
            "path": "https://radarstac.s3.amazonaws.com/stac/radarsat-1/slc/catalog.json",
            "schema": ["https://cdn.staclint.com/v0.7.0/catalog.json"],
            "asset_type": "CATALOG",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "0.7.0",
            "path": "https://radarstac.s3.amazonaws.com/stac/radarsat-1/slc/2012-05-13/RS1_M0630938_F2N_20120513_225708_HH_SLC.json",
            "schema": ["https://cdn.staclint.com/v0.7.0/item.json"],
            "asset_type": "ITEM",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "0.7.0",
            "path": "https://radarstac.s3.amazonaws.com/stac/radarsat-1/slc/2012-06-14/RS1_M0634796_F3F_20120614_110317_HH_SLC.json",
            "schema": ["https://cdn.staclint.com/v0.7.0/item.json"],
            "asset_type": "ITEM",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "0.7.0",
            "path": "https://radarstac.s3.amazonaws.com/stac/radarsat-1/slc/2012-06-14/RS1_M0634795_F3F_20120614_110311_HH_SLC.json",
            "schema": ["https://cdn.staclint.com/v0.7.0/item.json"],
            "asset_type": "ITEM",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "0.7.0",
            "path": "https://radarstac.s3.amazonaws.com/stac/radarsat-1/slc/2012-10-12/RS1_M0634798_F3F_20121012_110325_HH_SLC.json",
            "schema": ["https://cdn.staclint.com/v0.7.0/item.json"],
            "asset_type": "ITEM",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "0.7.0",
            "path": "https://radarstac.s3.amazonaws.com/stac/radarsat-1/slc/2012-10-12/RS1_M0634799_F3F_20121012_110331_HH_SLC.json",
            "schema": ["https://cdn.staclint.com/v0.7.0/item.json"],
            "asset_type": "ITEM",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "0.7.0",
            "path": "https://radarstac.s3.amazonaws.com/stac/radarsat-1/raw/catalog.json",
            "schema": ["https://cdn.staclint.com/v0.7.0/catalog.json"],
            "asset_type": "CATALOG",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "0.7.0",
            "path": "https://radarstac.s3.amazonaws.com/stac/radarsat-1/raw/2012-05-13/RS1_M0000676_F2N_20120513_225701_HH_RAW.json",
            "schema": ["https://cdn.staclint.com/v0.7.0/item.json"],
            "asset_type": "ITEM",
            "validation_method": "recursive",
            "valid_stac": True,
        },
    ]


def test_recursive_local_v090():
    stac_file = "tests/test_data/v090/catalog.json"
    stac = stac_validator.StacValidate(stac_file, recursive=1)
    stac.run()
    assert stac.message == [
        {
            "version": "0.9.0",
            "path": "tests/test_data/v090/catalog.json",
            "schema": ["https://cdn.staclint.com/v0.9.0/catalog.json"],
            "asset_type": "CATALOG",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "0.9.0",
            "path": "tests/test_data/v090/items/sample.json",
            "schema": ["https://cdn.staclint.com/v0.9.0/item.json"],
            "asset_type": "ITEM",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "0.9.0",
            "path": "tests/test_data/v090/items/good_item_v090.json",
            "schema": [
                "https://cdn.staclint.com/v0.9.0/extension/eo.json",
                "https://cdn.staclint.com/v0.9.0/extension/view.json",
                "https://cdn.staclint.com/v0.9.0/item.json",
            ],
            "asset_type": "ITEM",
            "validation_method": "recursive",
            "valid_stac": True,
        },
    ]


def test_recursive_v1beta1():
    stac_file = "tests/test_data/1beta1/sentinel2.json"
    stac = stac_validator.StacValidate(stac_file, recursive=0)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-beta.1",
            "path": "tests/test_data/1beta1/sentinel2.json",
            "schema": ["https://cdn.staclint.com/v1.0.0-beta.1/collection.json"],
            "asset_type": "COLLECTION",
            "validation_method": "recursive",
            "valid_stac": True,
        }
    ]


def test_recursive_v1beta2():
    stac_file = "https://raw.githubusercontent.com/stac-utils/pystac/main/tests/data-files/examples/1.0.0-beta.2/collection-spec/examples/sentinel2.json"
    stac = stac_validator.StacValidate(stac_file, recursive=0)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-beta.2",
            "path": "https://raw.githubusercontent.com/stac-utils/pystac/main/tests/data-files/examples/1.0.0-beta.2/collection-spec/examples/sentinel2.json",
            "schema": [
                "https://schemas.stacspec.org/v1.0.0-beta.2/collection-spec/json-schema/collection.json"
            ],
            "asset_type": "COLLECTION",
            "validation_method": "recursive",
            "valid_stac": True,
        }
    ]


def test_recursion_collection_local_v1rc1():
    stac_file = "tests/test_data/1rc1/collection.json"
    stac = stac_validator.StacValidate(stac_file, recursive=1)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-rc.1",
            "path": "tests/test_data/1rc1/collection.json",
            "schema": [
                "https://schemas.stacspec.org/v1.0.0-rc.1/collection-spec/json-schema/collection.json"
            ],
            "asset_type": "COLLECTION",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "1.0.0-rc.1",
            "path": "tests/test_data/1rc1/./simple-item.json",
            "schema": [
                "https://schemas.stacspec.org/v1.0.0-rc.1/item-spec/json-schema/item.json"
            ],
            "asset_type": "ITEM",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "1.0.0-rc.1",
            "path": "tests/test_data/1rc1/./core-item.json",
            "schema": [
                "https://schemas.stacspec.org/v1.0.0-rc.1/item-spec/json-schema/item.json"
            ],
            "asset_type": "ITEM",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "1.0.0-rc.1",
            "path": "tests/test_data/1rc1/./extended-item.json",
            "schema": [
                "https://cdn.staclint.com/v1.0.0-rc.1/extension/eo.json",
                "https://cdn.staclint.com/v1.0.0-rc.1/extension/projection.json",
                "https://cdn.staclint.com/v1.0.0-rc.1/extension/scientific.json",
                "https://cdn.staclint.com/v1.0.0-rc.1/extension/view.json",
                "https://schemas.stacspec.org/v1.0.0-rc.1/item-spec/json-schema/item.json",
            ],
            "asset_type": "ITEM",
            "validation_method": "recursive",
            "valid_stac": True,
        },
    ]


def test_recursion_collection_local_v1rc2():
    stac_file = "tests/test_data/1rc2/collection.json"
    stac = stac_validator.StacValidate(stac_file, recursive=1)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-rc.2",
            "path": "tests/test_data/1rc2/collection.json",
            "schema": [
                "https://schemas.stacspec.org/v1.0.0-rc.2/collection-spec/json-schema/collection.json"
            ],
            "asset_type": "COLLECTION",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "1.0.0-rc.2",
            "path": "tests/test_data/1rc2/./simple-item.json",
            "schema": [
                "https://schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/item.json"
            ],
            "asset_type": "ITEM",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "1.0.0-rc.2",
            "path": "tests/test_data/1rc2/./core-item.json",
            "schema": [
                "https://schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/item.json"
            ],
            "asset_type": "ITEM",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "1.0.0-rc.2",
            "path": "tests/test_data/1rc2/./extended-item.json",
            "schema": [
                "https://stac-extensions.github.io/eo/v1.0.0/schema.json",
                "https://stac-extensions.github.io/projection/v1.0.0/schema.json",
                "https://stac-extensions.github.io/scientific/v1.0.0/schema.json",
                "https://stac-extensions.github.io/view/v1.0.0/schema.json",
                "https://stac-extensions.github.io/remote-data/v1.0.0/schema.json",
                "https://schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/item.json",
            ],
            "asset_type": "ITEM",
            "validation_method": "recursive",
            "valid_stac": True,
        },
    ]


def test_recursion_collection_local_2_v1rc2():
    stac_file = "tests/test_data/1rc2/extensions-collection/collection.json"
    stac = stac_validator.StacValidate(stac_file, recursive=1)
    stac.run()
    assert stac.message == [
        {
            "version": "1.0.0-rc.2",
            "path": "tests/test_data/1rc2/extensions-collection/collection.json",
            "schema": [
                "https://schemas.stacspec.org/v1.0.0-rc.2/collection-spec/json-schema/collection.json"
            ],
            "asset_type": "COLLECTION",
            "validation_method": "recursive",
            "valid_stac": True,
        },
        {
            "version": "1.0.0-rc.2",
            "path": "tests/test_data/1rc2/extensions-collection/./proj-example/proj-example.json",
            "schema": [
                "https://stac-extensions.github.io/eo/v1.0.0/schema.json",
                "https://schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/item.json",
            ],
            "asset_type": "ITEM",
            "validation_method": "recursive",
            "valid_stac": True,
        },
    ]


# manual tests - take a long time
# stac_validator https://radarstac.s3.amazonaws.com/stac/catalog.json --recursive 5 --verbose
# stac_validator https://cmr.earthdata.nasa.gov/stac --recursive 5 --verbose
# stac_validator https://spot-canada-ortho.s3.amazonaws.com/catalog.json --recursive 5 --verbose

# """ -------------- Test Folder - Good Items ---------------- """

# # @pytest.mark.smoke
# def test_good_items_in_folder():
#     for (_, _, test_files) in os.walk("tests/test_data/1rc2"):
#         for f in test_files:
#             if f[-4:] == "json":
#                 stac = stac_validator.StacValidate(
#                     f"tests/test_data/1rc2/{f}", core=True
#                 )
#                 stac.run()
#                 assert stac.message[0]["valid_stac"] is True
