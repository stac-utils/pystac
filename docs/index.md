# PySTAC

**PySTAC** is a Python library for reading and writing [SpatioTemporal Asset Catalog (STAC)](https://stacspec.org) metadata.
To install:

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
