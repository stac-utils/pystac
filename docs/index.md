# PySTAC

[![Build Status](https://github.com/stac-utils/pystac/actions/workflows/continuous-integration.yml/badge.svg)](https://github.com/stac-utils/pystac/actions/workflows/continuous-integration.yml)
[![PyPI version](https://badge.fury.io/py/pystac.svg)](https://badge.fury.io/py/pystac)
[![Documentation](https://readthedocs.org/projects/pystac/badge/?version=latest)](https://pystac.readthedocs.io/en/latest/)

PySTAC is a Python library for working with the [SpatioTemporal Asset Catalog (STAC)](https://stacspec.org) specification.

## What is STAC?

The SpatioTemporal Asset Catalog (STAC) specification provides a common language to describe geospatial information, so it can more easily be worked with, indexed, and discovered. STAC is a specification for describing geospatial data using JSON and GeoJSON.

## What is PySTAC?

PySTAC is a library that provides a Python API for working with STAC catalogs, collections, and items. It allows you to:

- **Read** STAC catalogs, collections, and items from files or URLs
- **Create** new STAC objects programmatically
- **Modify** existing STAC objects
- **Write** STAC objects to disk
- **Validate** STAC objects against the specification
- **Traverse** STAC hierarchies

## PySTAC v2.0

This is the v2.0 rewrite of PySTAC with improved design principles:

- **Stable core APIs**: Keep data structure APIs (Item, Catalog, Collection) consistent
- **Flexible validation**: Accept almost anything with warnings for corrections
- **Simplified implementation**: Do fewer things at once, single responsibility methods
- **Low dependencies**: Minimal dependencies by default, optional extras for additional features

## Quick Example

```python
import pystac

# Read a STAC item
item = pystac.Item.from_file("path/to/item.json")

# Access item properties
print(f"Item ID: {item.id}")
print(f"Datetime: {item.datetime}")

# Access assets
for key, asset in item.assets.items():
    print(f"Asset {key}: {asset.href}")

# Create a new catalog
catalog = pystac.Catalog(
    id="my-catalog",
    description="A catalog of imagery"
)

# Add the item to the catalog
catalog.add_item(item)

# Save the catalog
catalog.render(root="/path/to/output")
catalog.save()
```

## Features

- **Core STAC Types**: Full support for Item, Catalog, and Collection
- **Links and Assets**: Complete link and asset management
- **I/O**: Flexible I/O system with pluggable readers and writers
- **Validation**: Optional validation against STAC JSON schemas
- **Extensions**: Preserve extension data through extra_fields
- **Type Safety**: Full type hints with strict type checking

## Get Started

Check out the [Installation Guide](getting-started/installation.md) to install PySTAC, then follow the [Quickstart](getting-started/quickstart.md) to learn the basics.

## Links

- [GitHub Repository](https://github.com/stac-utils/pystac)
- [PyPI Package](https://pypi.org/project/pystac/)
- [STAC Specification](https://stacspec.org)
- [Issue Tracker](https://github.com/stac-utils/pystac/issues)
