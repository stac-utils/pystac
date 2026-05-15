# Migration Guide: PySTAC v1 to v2

This guide helps you migrate your PySTAC code from v1.x to v2.0. PySTAC v2.0 is a ground-up rewrite that changes how you read, write, and work with STAC catalogs. While the core data structure APIs remain familiar, **there are significant breaking changes** you need to address.

## What's Different

The key differences between v1 and v2 are:

- **`CatalogType` is removed** - use explicit boolean arguments instead
- **`StacIO` is replaced** with `Reader` and `Writer` classes
- **Reading methods move to classes** - `pystac.read_file()` becomes `Item.from_file()`, etc.
- **Collection is no longer a Catalog subclass** - both inherit from `Container` instead
- **Href handling is explicit** - `normalize_hrefs()` must be called before serialization
- **No auto-mutation on read** - data is not modified when loading
- **Assets require keyword arguments** - only `href` is positional
- **Extents have stricter structure**

## V1 to V2 migration examples

### CatalogType is Removed

**What changed:** The `CatalogType` enum no longer exists. Href behavior is now controlled with explicit boolean arguments.

**v1:**
```python
from pystac import Catalog, CatalogType

catalog = Catalog("my-catalog", "A catalog")
catalog.normalize_hrefs("./catalog")
catalog.save(CatalogType.SELF_CONTAINED)  # or CatalogType.ABSOLUTE
```

**v2:**
```python
catalog = Catalog("my-catalog", "A catalog")
catalog.normalize_hrefs("./catalog")
catalog.save(use_absolute_hrefs=False, include_self_href=True)
```

With this change, `CatalogType.SELF_CONTAINED` is equivalent to `use_absolute_hrefs=False`.
`CatalogType.ABSOLUTE` is equivalent to `use_absolute_hrefs=True`.
`CatalogType.RELATIVE` is equivalent to `use_absolute_hrefs=False, include_self_href=False`.
Additionally, the `save()` method no longer requires `catalog_type` - it's inferred from the normalize_hrefs call.

### StacIO is Replaced with Reader and Writer

**What changed:** The `StacIO` class is replaced by separate `Reader` and `Writer` classes. Reading is now a method on objects rather than a top-level function.

**v1:**
```python
from pystac import pystac
from pystac.stac_io import StacIO

class MyStacIO(StacIO):
    def read_text(self, source):
        # custom reading logic
        return "..."
    
    def write_text(self, dest, text):
        # custom writing logic
        pass

io = MyStacIO()
item = pystac.read_file("item.json", io=io)
catalog = pystac.read_file("catalog.json", io=io)
catalog.save(dest="./output", stac_io=io)
```

**v2:**
```python
from pystac import Item, Catalog
from pystac.io import Reader, Writer

class MyReader(Reader):
    def read_text(self, source):
        # custom reading logic
        return "..."

class MyWriter(Writer):
    def write_text(self, dest, text):
        # custom writing logic
        pass

reader = MyReader()
writer = MyWriter()
item = Item.from_file("item.json", reader=reader)
catalog = Catalog.from_file("catalog.json", reader=reader)
catalog.save(writer=writer)
```

### Collection is No Longer a Catalog Subclass

**What changed:** `Collection` and `Catalog` both now inherit from an abstract `Container` base class. This breaks code that checks `isinstance(obj, Catalog)` which was used in v1 as `Collection` inherited from `Catalog`. You should now check against a union or one or the other.

**v1:**
```python
from pystac import Catalog, Collection

collection = Collection("my-collection", "A collection")
if isinstance(collection, Catalog):
    print("This is true in v1!")
```

**v2:**
```python
from pystac import Catalog, Collection, Container

collection = Collection("my-collection", "A collection")
if isinstance(collection, Catalog):
    print("This is now FALSE in v2!")

if isinstance(collection, Container):
    print("Use Container to check for both Catalog and Collection")
```

### Href Handling is Now Explicit

**What changed:** In v1, `Link.to_dict()` would mutate the href based on `CatalogType` and other factors. In v2, hrefs are only modified during the `normalize_hrefs()` call, not during serialization. You must call `normalize_hrefs()` before saving.

**v1:**
```python
from pystac import Catalog, Item, CatalogType

catalog = Catalog("root", "Root")
item = Item("item-1")
catalog.add_item(item)

# v1: href mutation happens during to_dict()
data = catalog.to_dict()  # hrefs are relative based on CatalogType
catalog.save(CatalogType.SELF_CONTAINED)
```

**v2:**
```python
from pystac import Catalog, Item

catalog = Catalog("root", "Root")
item = Item("item-1")
catalog.add_item(item)

# v2: must explicitly normalize before serialization
catalog.normalize_hrefs("./output")  # href mutation happens here
data = catalog.to_dict()  # hrefs are now correct and won't change
catalog.save()
```

### Assets Now Require Keyword Arguments

**What changed:** In v1, `Asset` could accept multiple positional arguments. In v2, only `href` is positional—all other parameters must be passed as keyword arguments.

**v1:**
```python
from pystac import Item, Asset

item = Item("item-1")
# Could pass multiple positional arguments:
asset = Asset("data.tif", "image/tiff", "Data", "Raster data")
item.add_asset("data", asset)
```

**v2:**
```python
from pystac import Item, Asset

item = Item("item-1")
# Only href is positional, everything else must be keyword arguments:
asset = Asset(
    href="data.tif",
    media_type="image/tiff",
    title="Data",
    description="Raster data",
    roles=["data"],
)
item.add_asset("data", asset)
```

### Extents: Spatial and Temporal Structures Changed

**What changed:** In v1, `Extent` had nested `SpatialExtent` and `TemporalExtent` classes with specific property patterns. In v2, these structures are more explicitly defined with stricter typing and validation.

**v1:**
```python
from pystac import Collection, SpatialExtent, TemporalExtent
from datetime import datetime

# v1: Used convenience constructors
spatial = SpatialExtent.from_coordinates(0, 0, 1, 1)
temporal = TemporalExtent.from_now()

collection = Collection("col-1", "A collection")
```

**v2:**
```python
from pystac import Collection, Extent, SpatialExtent, TemporalExtent
from datetime import datetime, timezone

# v2: Build structures directly with proper parameter names
spatial = SpatialExtent(bbox=[[0, 0, 1, 1]])
temporal = TemporalExtent(interval=[[datetime.now(timezone.utc), None]])
extent = Extent(spatial=spatial, temporal=temporal)

collection = Collection("col-1", "A collection", extent=extent)

# Access via new property names:
bbox = collection.extent.spatial.bbox  # Was bboxes, now bbox
interval = collection.extent.temporal.interval  # Was intervals, now interval
```

### TODO: Copying Items in v2

Add a short example here that shows how to copy an item in PySTAC v2, including what changed from v1.

### TODO: Saving Items in v2

Add a short example here that shows how to save items in PySTAC v2, including any v2-specific changes.
