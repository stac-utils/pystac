# PySTAC

!!! warning

    These docs are for the work-in-progress v2 of PySTAC.
    For the current PySTAC v1 docs, see <https://pystac.readthedocs.io>.

    Our work plan for v2 goes like this:

    1. Rebuild the core data structures (`Item`, `Catalog`, `Collection`, etc) from scratch, with new tests
    2. Slowly re-add the old tests to the `tests/v1` one at a time, to make sure that we're breaking as little as possible
    3. If we intentionally break a test (e.g. by relaxing a check on inputs) we'll mark it `xfail` and copy it to test the new expected behavior

    This will take a while.
    Watch <https://github.com/stac-utils/pystac/tree/v2> to track our progress.
    We'll sometimes use pull requests, but sometimes not.

**PySTAC** is a Python library for reading and writing [SpatioTemporal Asset Catalog (STAC)](https://stacspec.org) metadata.
To install:

<!-- markdownlint-disable MD046 -->
```shell
python -m pip install pystac
```

## Creating

STAC has three data structure: `Item`, `Catalog`, and `Collection`.
Each can be created with sensible defaults:

```python
from pystac import Item, Catalog, Collection

item = Item("an-item-id")
catalog = Item("a-catalog-id", "A catalog description")
collection = Item("a-collection-id", "A collection description")
```

## Reading

Reading STAC from the local filesystem is supported out-of-the-box:

```python
item = pystac.read_file("item.json")
```

To read from remote locations, including HTTP(S) and blob storage, we use [obstore](https://developmentseed.org/obstore/).
Install with that optional dependency:

```shell
python -m pip install 'pystac[obstore]'
```

Then:

```python
from pystac.obstore import ObstoreReader
reader = ObstoreReader()  # provide any configuration values here, e.g. ObstoreReader(aws_region="us-east-1")
item = reader.read_file("s3://bucket/item.json")
```

!!! todo

    Add more examples, and maybe put them in a notebook so we can execute them.

## Supported versions

PySTAC v2.0 supports STAC v1.0 and STAC v1.1.
For pre-STAC v1.0 versions, use `pystac<2`.
