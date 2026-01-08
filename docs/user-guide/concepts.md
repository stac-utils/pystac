# Core Concepts

This guide introduces the core concepts and architecture of PySTAC.

## STAC Objects

PySTAC provides Python classes for the main STAC specification types:

### Item

A **STAC Item** is a GeoJSON Feature with additional STAC-specific properties. It represents a single spatiotemporal asset or scene.

Key properties:
- `id`: Unique identifier
- `geometry`: GeoJSON geometry
- `bbox`: Bounding box
- `datetime` or `start_datetime`/`end_datetime`: Temporal information
- `properties`: Additional metadata
- `assets`: Dictionary of associated files
- `links`: Relationships to other STAC objects

### Catalog

A **STAC Catalog** is a collection of STAC Items and/or other Catalogs. It provides organizational structure.

Key properties:
- `id`: Unique identifier
- `description`: Human-readable description
- `links`: Relationships to children, items, and parent

### Collection

A **STAC Collection** extends Catalog with additional metadata about a group of related Items.

Key properties:
- All Catalog properties, plus:
- `extent`: Spatial and temporal extent of all items
- `license`: License information
- `providers`: Organizations involved
- `summaries`: Aggregate information about item properties
- `item_assets`: Common asset definitions

## Object Hierarchy

```
STACObject (Abstract Base)
├── Container (Abstract Base)
│   ├── Catalog
│   └── Collection
└── Item
```

All STAC objects inherit from `STACObject`, which provides:
- Serialization/deserialization (`from_dict()`, `to_dict()`, `from_file()`)
- Link management
- File I/O operations

`Container` is an abstract base for Catalog and Collection, providing:
- Hierarchy traversal (`walk()`, `get_children()`, `get_items()`)
- Child-parent relationship management
- Batch operations

## Links

Links connect STAC objects together, forming a graph structure. PySTAC uses the `Link` class to represent relationships.

Common link relation types:
- `root`: Link to the root catalog
- `parent`: Link to the parent catalog/collection
- `child`: Link to a child catalog/collection
- `item`: Link to an item
- `self`: Canonical location of the object
- `collection`: Link from an item to its collection

### Lazy Loading

Links support lazy loading - the target object is only loaded when accessed via `get_stac_object()`:

```python
parent_link = item.get_single_link("parent")
if parent_link:
    # Object is loaded only when needed
    parent = parent_link.get_stac_object()
```

## Assets

Assets represent the actual data files associated with an Item. Each asset has:

- `href`: URL or path to the file
- `type`: Media type (MIME type)
- `title`: Human-readable title
- `description`: Detailed description
- `roles`: Semantic roles (e.g., "data", "thumbnail", "metadata")

```python
asset = pystac.Asset(
    href="https://example.com/image.tif",
    type="image/tiff; application=geotiff",
    roles=["data"]
)
```

## I/O System

PySTAC v2.0 uses a protocol-based I/O system for flexibility:

### Read Protocol

- `read_json_from_path(path)`: Read from filesystem
- `read_json_from_url(url)`: Read from HTTP/HTTPS

### Write Protocol

- `write_json_to_path(data, path)`: Write to filesystem
- `write_json_to_url(data, url)`: Write to URL (custom implementations)

The default implementation uses Python's standard library for filesystem operations and `urllib` for HTTP.

### Custom I/O

You can provide custom readers/writers for cloud storage or other backends:

```python
# Custom implementation using duck typing
class S3Reader:
    def read_json_from_path(self, path):
        # S3 implementation
        pass

    def read_json_from_url(self, url):
        # S3 implementation
        pass

# Use with PySTAC
item = pystac.Item.from_file("s3://bucket/item.json", reader=S3Reader())
```

## Rendering

Before saving, STAC objects need their `href` properties set. The `render()` method handles this using a rendering strategy.

```python
# Set hrefs using best practices layout
catalog.render(root="/path/to/output")

# Then save all objects
catalog.save()
```

The default `BestPracticesRenderer` creates a standard layout:
- Items: `{id}/{id}.json`
- Catalogs: `{id}/catalog.json`
- Collections: `{id}/collection.json`

## Extensions

STAC Extensions add additional fields and functionality. PySTAC v2.0 uses a simplified approach:

- `stac_extensions`: List of extension URLs
- `extra_fields`: Dictionary for extension-specific fields

```python
# Extension data is preserved automatically
item = pystac.Item.from_dict({
    "type": "Feature",
    "stac_extensions": ["https://stac-extensions.github.io/eo/v1.0.0/schema.json"],
    "properties": {
        "eo:cloud_cover": 10.5
    },
    # ... other fields
})

# Access extension data
cloud_cover = item.properties.get("eo:cloud_cover")

# Or via extra_fields for root-level extension properties
# item.extra_fields["custom:field"]
```

## Validation

PySTAC provides optional validation against JSON schemas:

```python
from pystac.validate import JsonschemaValidator

validator = JsonschemaValidator()
errors = validator.validate(item.to_dict())
```

Validation requires the `validation` optional dependencies:

```bash
pip install 'pystac[validation]'
```

## PySTAC v2.0 Design Principles

### Stable Core APIs

Core data structure APIs (Item, Catalog, Collection) remain stable across versions.

### Relaxed Validation

Initializers accept almost anything, with warnings for corrections. This makes it easier to work with imperfect real-world data.

### Single Responsibility

Methods do one thing well, rather than combining multiple operations.

### Low Dependencies

Minimal required dependencies. Additional features available via optional dependency groups.

## Next Steps

- [Working with Items](items.md)
- [Working with Catalogs](catalogs.md)
- [Working with Collections](collections.md)
- [Reading and Writing](io.md)
