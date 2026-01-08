# Working with Collections

A STAC Collection extends Catalog with additional metadata about a group of related Items. This guide covers creating and managing Collections.

## Creating Collections

```python
import pystac
from datetime import datetime, timezone

collection = pystac.Collection(
    id="my-collection",
    description="Satellite imagery collection",
    title="My Satellite Collection",  # Optional
    license="CC-BY-4.0",
    extent=pystac.Extent(
        spatial=pystac.SpatialExtent([[-180, -90, 180, 90]]),
        temporal=pystac.TemporalExtent([
            [datetime(2020, 1, 1, tzinfo=timezone.utc), None]
        ])
    )
)
```

## Collection Properties

### Required Properties

- **id**: Unique identifier
- **description**: Detailed description
- **license**: License identifier or "proprietary"
- **extent**: Spatial and temporal extent of all items

### Optional Properties

```python
collection.title = "Human-readable title"
collection.keywords = ["satellite", "imagery", "earth observation"]
collection.providers = [
    pystac.Provider(
        name="Example Org",
        roles=["producer", "licensor"],
        url="https://example.com"
    )
]
```

## Extent

The extent describes the spatial and temporal coverage:

### Spatial Extent

```python
# Single bounding box
spatial_extent = pystac.SpatialExtent(
    bboxes=[[-180, -90, 180, 90]]
)

# Multiple bounding boxes
spatial_extent = pystac.SpatialExtent(
    bboxes=[
        [-180, -90, -90, 0],  # Western hemisphere, southern half
        [-90, 0, 0, 90]        # Northwestern quadrant
    ]
)
```

### Temporal Extent

```python
# Closed time range
temporal_extent = pystac.TemporalExtent(
    intervals=[
        [
            datetime(2020, 1, 1, tzinfo=timezone.utc),
            datetime(2024, 12, 31, tzinfo=timezone.utc)
        ]
    ]
)

# Open-ended (still collecting)
temporal_extent = pystac.TemporalExtent(
    intervals=[
        [datetime(2020, 1, 1, tzinfo=timezone.utc), None]
    ]
)
```

## Summaries

Summaries provide aggregate information about item properties:

```python
collection.summaries = pystac.Summaries({
    "platform": ["satellite-1", "satellite-2"],
    "instruments": ["camera-1", "camera-2"],
    "gsd": {"minimum": 10, "maximum": 30},
    "eo:cloud_cover": {"minimum": 0, "maximum": 50}
})
```

## Item Assets

Define common assets that appear in items:

```python
collection.item_assets = {
    "data": pystac.extensions.item_assets.AssetDefinition({
        "type": "image/tiff; application=geotiff",
        "roles": ["data"],
        "title": "Data"
    }),
    "thumbnail": pystac.extensions.item_assets.AssetDefinition({
        "type": "image/png",
        "roles": ["thumbnail"],
        "title": "Thumbnail"
    })
}
```

## Adding Items

```python
# Create and add an item
item = pystac.Item(
    id="item-1",
    geometry=geometry,
    bbox=bbox,
    datetime=datetime.now(timezone.utc),
    properties={}
)

# Add to collection (sets item.collection_id automatically)
collection.add_item(item)

# Update extent to include new items
collection.update_extent_from_items()
```

## Reading Collections

```python
# From file
collection = pystac.Collection.from_file("path/to/collection.json")

# From URL
collection = pystac.Collection.from_file("https://example.com/collection.json")

# Access items
for item in collection.get_items():
    print(f"Item: {item.id}")
    print(f"Collection: {item.collection_id}")
```

## Collection vs Catalog

When to use Collection vs Catalog:

**Use Collection when:**
- Items are related and share characteristics
- You want to provide aggregate metadata (extent, summaries)
- You need license information
- Items should be discoverable as a cohesive dataset

**Use Catalog when:**
- You only need organizational structure
- Items are heterogeneous
- You don't need collection-specific metadata

## Updating Extent

```python
# Manually update after adding items
collection.update_extent_from_items()

# Or calculate from specific items
items = [item1, item2, item3]
spatial_extent = pystac.SpatialExtent.from_items(items)
temporal_extent = pystac.TemporalExtent.from_items(items)

collection.extent = pystac.Extent(
    spatial=spatial_extent,
    temporal=temporal_extent
)
```

## Saving Collections

```python
# Render and save
collection.render(root="/path/to/output")
collection.save()

# Or add to catalog and save together
catalog.add_child(collection)
catalog.render(root="/path/to/output")
catalog.save()
```

## Next Steps

- Learn about [Items](items.md)
- Learn about [Catalogs](catalogs.md)
- Explore the [Collection API Reference](../api/collection.md)
