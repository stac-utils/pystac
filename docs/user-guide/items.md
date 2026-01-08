# Working with Items

A STAC Item is a GeoJSON Feature that represents a single spatiotemporal asset or scene. This guide covers creating, reading, and manipulating STAC Items.

## Creating Items

```python
import pystac
from datetime import datetime, timezone

item = pystac.Item(
    id="example-item",
    geometry={
        "type": "Polygon",
        "coordinates": [[
            [-105.0, 40.0],
            [-104.0, 40.0],
            [-104.0, 39.0],
            [-105.0, 39.0],
            [-105.0, 40.0]
        ]]
    },
    bbox=[-105.0, 39.0, -104.0, 40.0],
    datetime=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    properties={
        "platform": "satellite-1",
        "instruments": ["camera"]
    }
)
```

## Item Properties

### Required Properties

- **id**: Unique identifier for the item
- **geometry**: GeoJSON geometry object (or `None` for non-spatial items)
- **bbox**: Bounding box `[min_lon, min_lat, max_lon, max_lat]`
- **datetime**: Single datetime, or `None` if using datetime range
- **properties**: Dictionary of additional metadata

### Datetime Handling

Items can have either a single datetime or a datetime range:

```python
# Single datetime
item = pystac.Item(
    id="single-time",
    geometry=geometry,
    bbox=bbox,
    datetime=datetime.now(timezone.utc),
    properties={}
)

# Datetime range
item = pystac.Item(
    id="time-range",
    geometry=geometry,
    bbox=bbox,
    datetime=None,  # Must be None for ranges
    properties={
        "start_datetime": "2024-01-01T00:00:00Z",
        "end_datetime": "2024-01-02T00:00:00Z"
    }
)
```

## Adding Assets

Assets represent the actual data files:

```python
# Add a data asset
item.assets["data"] = pystac.Asset(
    href="https://example.com/data.tif",
    type="image/tiff; application=geotiff",
    title="COG Data",
    roles=["data"]
)

# Add a thumbnail
item.assets["thumbnail"] = pystac.Asset(
    href="https://example.com/thumbnail.png",
    type="image/png",
    roles=["thumbnail"]
)

# Add metadata
item.assets["metadata"] = pystac.Asset(
    href="https://example.com/metadata.xml",
    type="application/xml",
    roles=["metadata"]
)
```

## Links

Items typically have links to:
- Parent catalog or collection
- Self (canonical location)
- Collection (if part of a collection)

```python
# Link to collection
item.add_link(pystac.Link(
    rel="collection",
    target="https://example.com/collection.json"
))

# Access links
collection_link = item.get_single_link("collection")
if collection_link:
    collection = collection_link.get_stac_object()
```

## Collection Membership

Items can reference their collection:

```python
# Set collection reference
item.collection_id = "my-collection"

# Or when adding to a collection
collection.add_item(item)  # Automatically sets collection_id
```

## Reading Items

```python
# From file
item = pystac.Item.from_file("path/to/item.json")

# From dict
item = pystac.Item.from_dict(item_dict)

# From URL
item = pystac.Item.from_file("https://example.com/item.json")
```

## Saving Items

```python
# Save to specific path
item.save("/path/to/output/item.json")

# Or render with parent and save
catalog.add_item(item)
catalog.render(root="/path/to/output")
catalog.save()  # Saves catalog and all items
```

## Item Validation

```python
from pystac.validate import JsonschemaValidator

validator = JsonschemaValidator()
errors = validator.validate(item.to_dict())

if errors:
    for error in errors:
        print(f"Error: {error}")
else:
    print("Item is valid!")
```

## Common Metadata

Items often include common metadata fields:

```python
item.properties.update({
    "title": "Example Scene",
    "description": "An example satellite scene",
    "platform": "satellite-1",
    "instruments": ["camera-1"],
    "constellation": "sat-constellation",
    "gsd": 10.0  # Ground sample distance in meters
})
```

## Next Steps

- Learn about [Catalogs](catalogs.md)
- Learn about [Collections](collections.md)
- Explore the [Item API Reference](../api/item.md)
