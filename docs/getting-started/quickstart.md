# Quickstart

This guide will walk you through the basics of using PySTAC to work with STAC catalogs, collections, and items.

## Reading STAC Objects

### Reading an Item

```python
import pystac

# Read a STAC item from a file
item = pystac.Item.from_file("path/to/item.json")

# Access basic properties
print(f"Item ID: {item.id}")
print(f"Datetime: {item.datetime}")
print(f"Geometry: {item.geometry}")
print(f"Bounding Box: {item.bbox}")

# Access custom properties
print(f"Properties: {item.properties}")
```

### Reading a Catalog

```python
# Read a catalog
catalog = pystac.Catalog.from_file("path/to/catalog.json")

print(f"Catalog ID: {catalog.id}")
print(f"Description: {catalog.description}")

# Iterate through items
for item in catalog.get_items():
    print(f"Item: {item.id}")

# Recursively walk through the catalog
for child in catalog.walk():
    if isinstance(child, pystac.Item):
        print(f"Found item: {child.id}")
    elif isinstance(child, pystac.Collection):
        print(f"Found collection: {child.id}")
    else:
        print(f"Found catalog: {child.id}")
```

### Reading a Collection

```python
# Read a collection
collection = pystac.Collection.from_file("path/to/collection.json")

print(f"Collection ID: {collection.id}")
print(f"License: {collection.license}")
print(f"Extent: {collection.extent}")

# Access items in the collection
for item in collection.get_items():
    print(f"Item: {item.id}")
```

## Creating STAC Objects

### Creating an Item

```python
import pystac
from datetime import datetime, timezone

# Create a new item
item = pystac.Item(
    id="my-item",
    geometry={
        "type": "Point",
        "coordinates": [-105.0, 40.0]
    },
    bbox=[-105.0, 40.0, -105.0, 40.0],
    datetime=datetime.now(timezone.utc),
    properties={"key": "value"}
)

# Add an asset
item.assets["thumbnail"] = pystac.Asset(
    href="https://example.com/thumbnail.png",
    type="image/png",
    roles=["thumbnail"]
)
```

### Creating a Catalog

```python
# Create a catalog
catalog = pystac.Catalog(
    id="my-catalog",
    description="My STAC catalog"
)

# Add items
catalog.add_item(item)

# Add a child catalog
child_catalog = pystac.Catalog(
    id="child-catalog",
    description="A child catalog"
)
catalog.add_child(child_catalog)
```

### Creating a Collection

```python
# Create a collection
collection = pystac.Collection(
    id="my-collection",
    description="My STAC collection",
    license="CC-BY-4.0",
    extent=pystac.Extent(
        spatial=pystac.SpatialExtent([[-180, -90, 180, 90]]),
        temporal=pystac.TemporalExtent([[datetime.now(timezone.utc), None]])
    )
)

# Add items
collection.add_item(item)
```

## Working with Links

```python
# Access links
for link in item.links:
    print(f"Link rel: {link.rel}, href: {link.href}")

# Add a link
item.add_link(pystac.Link(
    rel="related",
    target="https://example.com/related.json"
))

# Get specific links
parent_link = item.get_single_link("parent")
if parent_link:
    print(f"Parent: {parent_link.href}")
```

## Working with Assets

```python
# Access assets
for key, asset in item.assets.items():
    print(f"Asset {key}:")
    print(f"  href: {asset.href}")
    print(f"  type: {asset.type}")
    print(f"  roles: {asset.roles}")

# Add an asset
item.assets["data"] = pystac.Asset(
    href="https://example.com/data.tif",
    type="image/tiff; application=geotiff",
    roles=["data"]
)

# Remove an asset
del item.assets["thumbnail"]
```

## Saving STAC Objects

```python
# Render sets hrefs for the catalog and all children
catalog.render(root="/path/to/output")

# Save writes all objects to disk
catalog.save()

# Or save a single object
item.save("/path/to/item.json")
```

## Validation

If you've installed the validation dependencies, you can validate STAC objects:

```python
from pystac.validate import JsonschemaValidator

validator = JsonschemaValidator()

# Validate an item
errors = validator.validate(item.to_dict())
if errors:
    for error in errors:
        print(f"Validation error: {error}")
else:
    print("Item is valid!")
```

## Next Steps

- Learn more about core concepts in the [User Guide](../user-guide/concepts.md)
- Explore the [API Reference](../api/stac-object.md) for detailed documentation
- Check out specific guides for [Items](../user-guide/items.md), [Catalogs](../user-guide/catalogs.md), and [Collections](../user-guide/collections.md)
