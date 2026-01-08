# Reading and Writing

This guide covers PySTAC's I/O system for reading and writing STAC objects.

## Reading STAC Objects

### From Files

```python
import pystac

# Read any STAC object (auto-detects type)
obj = pystac.STACObject.from_file("path/to/stac.json")

# Read specific types
item = pystac.Item.from_file("path/to/item.json")
catalog = pystac.Catalog.from_file("path/to/catalog.json")
collection = pystac.Collection.from_file("path/to/collection.json")
```

### From URLs

```python
# Read from HTTP/HTTPS
item = pystac.Item.from_file("https://example.com/item.json")

# Works with any accessible URL
catalog = pystac.Catalog.from_file("https://example.com/catalog.json")
```

### From Dictionaries

```python
# From Python dict
item_dict = {
    "type": "Feature",
    "stac_version": "1.1.0",
    "id": "example",
    # ... other fields
}

item = pystac.Item.from_dict(item_dict)
```

## Writing STAC Objects

### Save Individual Objects

```python
# Save to specific path
item.save("/path/to/output/item.json")

# Save with pretty printing (default)
item.save("/path/to/output/item.json")
```

### Render and Save Hierarchies

When working with catalogs, use `render()` to set hrefs before saving:

```python
# Create catalog structure
catalog = pystac.Catalog(id="root", description="Root catalog")
catalog.add_item(item1)
catalog.add_item(item2)

# Render sets hrefs for all objects
catalog.render(root="/path/to/output")

# Save writes all objects
catalog.save()
```

## Custom I/O

PySTAC v2.0 uses protocol-based I/O for flexibility.

### Read Protocol

Implement these methods for custom reading:

```python
class CustomReader:
    def read_json_from_path(self, path: str) -> dict:
        """Read JSON from a path."""
        # Custom implementation
        pass

    def read_json_from_url(self, url: str) -> dict:
        """Read JSON from a URL."""
        # Custom implementation
        pass
```

### Write Protocol

Implement these methods for custom writing:

```python
class CustomWriter:
    def write_json_to_path(self, data: dict, path: str) -> None:
        """Write JSON to a path."""
        # Custom implementation
        pass

    def write_json_to_url(self, data: dict, url: str) -> None:
        """Write JSON to a URL."""
        # Custom implementation
        pass
```

### Using Custom I/O

```python
# Use custom reader
reader = CustomReader()
item = pystac.Item.from_file("custom://path", reader=reader)

# Use custom writer
writer = CustomWriter()
item.save("custom://path", writer=writer)
```

## Cloud Storage

### Using obstore

For S3, GCS, and Azure Blob Storage:

```bash
pip install 'pystac[obstore]'
```

```python
from pystac.io import ObstoreReader, ObstoreWriter

# Configure for S3
reader = ObstoreReader("s3://bucket-name")
writer = ObstoreWriter("s3://bucket-name")

# Read from S3
item = pystac.Item.from_file("s3://bucket-name/item.json", reader=reader)

# Write to S3
item.save("s3://bucket-name/output/item.json", writer=writer)
```

## Rendering Strategies

The renderer controls how hrefs are set when saving.

### Best Practices Renderer (Default)

```python
from pystac.render import BestPracticesRenderer

renderer = BestPracticesRenderer()
catalog.render(root="/path/to/output", renderer=renderer)
```

Creates this structure:
```
output/
├── catalog.json
├── collection-1/
│   ├── collection.json
│   └── item-1/
│       └── item-1.json
└── catalog-2/
    └── catalog.json
```

### Custom Renderer

```python
class CustomRenderer:
    def render(self, obj, root):
        """Set href for object and render children."""
        # Custom layout logic
        pass

# Use custom renderer
catalog.render(root="/path/to/output", renderer=CustomRenderer())
```

## Lazy Loading

Links support lazy loading to avoid loading entire hierarchies:

```python
# Read catalog
catalog = pystac.Catalog.from_file("path/to/catalog.json")

# Links are not resolved until accessed
for link in catalog.links:
    if link.rel == "child":
        # Object loaded only when needed
        child = link.get_stac_object()
```

## Href Resolution

PySTAC handles absolute and relative hrefs:

```python
from pystac.utils import make_absolute_href, make_relative_href

# Make absolute
absolute = make_absolute_href("./item.json", "/base/path/catalog.json")
# Result: "/base/path/item.json"

# Make relative
relative = make_relative_href("/path/to/item.json", "/path/catalog.json")
# Result: "./to/item.json"
```

## Error Handling

```python
try:
    item = pystac.Item.from_file("path/to/item.json")
except FileNotFoundError:
    print("File not found")
except pystac.STACError as e:
    print(f"STAC error: {e}")
```

## Performance Tips

1. **Use lazy loading** for large catalogs
2. **Limit recursion depth** when traversing
3. **Use specific type methods** instead of auto-detection
4. **Consider caching** for remote catalogs

```python
# Specify recursion limit
for item in catalog.get_items(recursive=True, max_depth=2):
    process(item)
```

## Next Steps

- Learn about [Core Concepts](concepts.md)
- Explore the [I/O API Reference](../api/io.md)
