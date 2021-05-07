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


# catch error?
# def test_custom_item_remote_schema_v080():
#     stac_file = "test_validation/test_data/v080/items/digitalglobe-sample.json"
#     with open(stac_file) as f:
#         js = json.load(f)
#     result = validate_dict(js)
#     assert result == []


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

def test_collection_v090():
    stac_file = "test_validation/test_data/v090/collections/sentinel2.json"
    with open(stac_file) as f:
        js = json.load(f)
    result = validate_dict(js)
    assert result == [
        'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.9.0/collection-spec/json-schema/collection.json'
    ]


def test_item_local_extensions_v090():
    stac_file = "test_validation/test_data/v090/items/CBERS_4.json"
    with open(stac_file) as f:
        js = json.load(f)
    result = validate_dict(js)
    assert result == [
        'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.9.0/item-spec/json-schema/item.json', 
        'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.9.0/extensions/eo/json-schema/schema.json', 
        'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.9.0/extensions/view/json-schema/schema.json'
    ]

def test_item_extensions_v090():
    stac_file = "test_validation/test_data/v090/extensions/eo/examples/example-landsat8.json"
    with open(stac_file) as f:
        js = json.load(f)
    result = validate_dict(js)
    assert result == [
        'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.9.0/item-spec/json-schema/item.json', 
        'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.9.0/extensions/eo/json-schema/schema.json', 
        'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.9.0/extensions/view/json-schema/schema.json'
    ]


# test error message - catch error?
# def test_bad_item_local_v090():
#     stac_file = "test_validation/test_data/v090/items/CBERS_4.json"
#     with open(stac_file) as f:
#         js = json.load(f)
#     result = validate_dict(js)
#     assert result == [
#         'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.9.0/item-spec/json-schema/item.json', 
#         'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.9.0/extensions/eo/json-schema/schema.json', 
#         'https://raw.githubusercontent.com/radiantearth/stac-spec/v0.9.0/extensions/view/json-schema/schema.json'
#     ]

# catch error?
# def test_bad_item_v090():
#     stac_file = "test_validation/test_data/bad_data/bad_item_v090.json"
#     with open(stac_file) as f:
#         js = json.load(f)
#     result = validate_dict(js)
#     assert result = []



def test_collection_v1beta1():
    stac_file = "test_validation/test_data/1beta1/sentinel2.json"
    with open(stac_file) as f:
        js = json.load(f)
    result = validate_dict(js)
    assert result == [
        'https://cdn.staclint.com/v1.0.0-beta.1/collection.json'
    ]


def test_item_local_v1beta2():
    stac_file = "test_validation/test_data/1beta2/stac_item.json"
    with open(stac_file) as f:
        js = json.load(f)
    result = validate_dict(js)
    assert result = [
        'https://schemas.stacspec.org/v1.0.0-beta.2/item-spec/json-schema/item.json'
    ]

def test_item_extensions_v1beta2():
    stac_file = "test_validation/test_data/1beta2/CBERS_4.json"
    with open(stac_file) as f:
        js = json.load(f)
    result = validate_dict(js)
    assert result = [
        'https://schemas.stacspec.org/v1.0.0-beta.2/item-spec/json-schema/item.json', 
        'https://schemas.stacspec.org/v1.0.0-beta.2/extensions/view/json-schema/schema.json', 
        'https://schemas.stacspec.org/v1.0.0-beta.2/extensions/projection/json-schema/schema.json'
    ]


def test_item_local_v1rc1():
    stac_file = "test_validation/test_data/1rc1/collectionless-item.json"
    with open(stac_file) as f:
        js = json.load(f)
    result = validate_dict(js)
    assert result = [
        'https://schemas.stacspec.org/v1.0.0-rc.1/item-spec/json-schema/item.json', 
        'https://schemas.stacspec.org/v1.0.0-rc.1/extensions/eo/json-schema/schema.json', 
        'https://schemas.stacspec.org/v1.0.0-rc.1/extensions/view/json-schema/schema.json'
    ]


def test_collection_local_v1rc1():
    stac_file = "test_validation/test_data/1rc1/collection.json"
    with open(stac_file) as f:
        js = json.load(f)
    result = validate_dict(js)
    assert result = [
        'https://schemas.stacspec.org/v1.0.0-rc.1/collection-spec/json-schema/collection.json'
    ]

def test_default_catalog_v1rc2():
    stac_file = "test_validation/test_data/1rc2/catalog.json"
    with open(stac_file) as f:
        js = json.load(f)
    result = validate_dict(js)
    assert result = [
        'https://schemas.stacspec.org/v1.0.0-rc.2/catalog-spec/json-schema/catalog.json'
    ]


def test_item_v1rc2():
    stac_file = "test_validation/test_data/1rc2/simple-item.json"
    with open(stac_file) as f:
        js = json.load(f)
    result = validate_dict(js)
    assert result = [
        'https://schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/item.json'
    ]

def test_item_extended_v1rc2():
    stac_file = "test_validation/test_data/1rc2/extended-item.json"
    with open(stac_file) as f:
        js = json.load(f)
    result = validate_dict(js)
    assert result = [
        'https://schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/item.json', 
        'https://stac-extensions.github.io/eo/v1.0.0/schema.json', 
        'https://stac-extensions.github.io/projection/v1.0.0/schema.json', 
        'https://stac-extensions.github.io/view/v1.0.0/schema.json', 
        'https://stac-extensions.github.io/scientific/v1.0.0/schema.json', 
        'https://stac-extensions.github.io/remote-data/v1.0.0/schema.json'
    ]

def test_catalog_v1rc2():
    stac_file = "test_validation/test_data/1rc2/catalog.json"
    with open(stac_file) as f:
        js = json.load(f)
    result = validate_dict(js)
    assert result = [
        'https://schemas.stacspec.org/v1.0.0-rc.2/catalog-spec/json-schema/catalog.json'
    ]


# catch error?
# def test_collection_eo_error_v1rc2():
#     stac_file = "test_validation/test_data/1rc2/extensions-collection/./proj-example/proj-example.json"
#     with open(stac_file) as f:
#         js = json.load(f)
#     result = validate_dict(js)
#     assert result = [
#     ]


# test remote file
# def test_item_remote_proj_v1b2():
#     stac_file = "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l1c/items/S2A_51SXT_20210415_0_L1C"
#     with open(stac_file) as f:
#         js = json.load(f)
#     result = validate_dict(js)
#     assert result = [
#     ]

# def test_item_extensions_remote_v1rc3():
#     stac_file = "https://raw.githubusercontent.com/radiantearth/stac-spec/master/examples/extended-item.json"
#     with open(stac_file) as f:
#         js = json.load(f)
#     result = validate_dict(js)
#     assert result = [
#     ]