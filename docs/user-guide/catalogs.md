# Working with Catalogs

A STAC Catalog provides organizational structure for Items and other Catalogs. This guide covers creating, traversing, and managing STAC Catalogs.

## Creating Catalogs

```python
import pystac

catalog = pystac.Catalog(
    id="my-catalog",
    description="A catalog of satellite imagery",
    title="My Satellite Catalog"  # Optional
)
```

## Adding Items and Children

```python
# Add an item
item = pystac.Item(...)
catalog.add_item(item)

# Add a child catalog
child = pystac.Catalog(
    id="child-catalog",
    description="A subcatalog"
)
catalog.add_child(child)

# Add a collection
collection = pystac.Collection(...)
catalog.add_child(collection)
```

## Traversing Catalogs

### Get Direct Children

```python
# Get all direct children (catalogs and collections)
for child in catalog.get_children():
    print(f"Child: {child.id}")

# Get all direct items
for item in catalog.get_items():
    print(f"Item: {item.id}")
```

### Recursive Traversal

```python
# Walk the entire catalog tree
for obj in catalog.walk():
    if isinstance(obj, pystac.Item):
        print(f"Item: {obj.id}")
    elif isinstance(obj, pystac.Collection):
        print(f"Collection: {obj.id}")
    elif isinstance(obj, pystac.Catalog):
        print(f"Catalog: {obj.id}")
```

## Reading Catalogs

```python
# Read from file
catalog = pystac.Catalog.from_file("path/to/catalog.json")

# Read from URL
catalog = pystac.Catalog.from_file("https://example.com/catalog.json")

# Traverse after reading
for item in catalog.get_items(recursive=True):
    print(f"Found item: {item.id}")
```

## Catalog Structure

### Links

Catalogs use links to connect to other objects:

- `root`: Link to the root catalog
- `parent`: Link to parent catalog (if not root)
- `child`: Links to child catalogs/collections
- `item`: Links to items
- `self`: Canonical location

```python
# Get root
root_link = catalog.get_root_link()
if root_link:
    root = root_link.get_stac_object()

# Get parent
parent_link = catalog.get_single_link("parent")
if parent_link:
    parent = parent_link.get_stac_object()
```

## Saving Catalogs

```python
# Render sets hrefs for catalog and all children
catalog.render(root="/path/to/output")

# Save writes all objects to disk
catalog.save()
```

### Render Strategies

The default renderer creates a directory structure:

```
output/
├── catalog.json
├── child-catalog/
│   ├── catalog.json
│   └── item-1/
│       └── item-1.json
└── collection-1/
    ├── collection.json
    └── item-2/
        └── item-2.json
```

## Catalog Organization Patterns

### Geographic Organization

```python
root = pystac.Catalog(id="root", description="Root catalog")

# Organize by region
north_america = pystac.Catalog(id="north-america", description="North America")
europe = pystac.Catalog(id="europe", description="Europe")

root.add_child(north_america)
root.add_child(europe)

# Add items to appropriate regions
north_america.add_item(usa_item)
europe.add_item(france_item)
```

### Temporal Organization

```python
root = pystac.Catalog(id="root", description="Root catalog")

# Organize by year
year_2023 = pystac.Catalog(id="2023", description="2023 imagery")
year_2024 = pystac.Catalog(id="2024", description="2024 imagery")

root.add_child(year_2023)
root.add_child(year_2024)
```

## Batch Operations

```python
# Set STAC version for all objects
catalog.set_stac_version("1.1.0")

# Clear all links of a specific type
for child in catalog.walk():
    child.clear_links("derived_from")
```

## Next Steps

- Learn about [Collections](collections.md)
- Learn about [Items](items.md)
- Explore the [Catalog API Reference](../api/catalog.md)
