# pytest-pystac

A [pytest](https://docs.pytest.org/) plugin that provides common fixtures for testing with [PySTAC](https://github.com/stac-utils/pystac).

## Installation

```shell
pip install pytest-pystac
```

## Fixtures

Once installed, the following fixtures are available automatically in your tests:

| Fixture | Type | Description |
| --- | --- | --- |
| `catalog` | `Catalog` | A basic test catalog |
| `collection` | `Collection` | A basic test collection with an arbitrary extent |
| `item` | `Item` | A basic test item with arbitrary geometry and bbox |
| `asset` | `Asset` | An asset attached to an item |
| `link` | `Link` | A link attached to an item |
| `sample_item` | `Item` | An item loaded from a sample JSON file |

A `vcr_config` fixture (module-scoped) is also provided for use with [pytest-recording](https://github.com/kiwicom/pytest-recording), which scrubs request and response headers from recorded cassettes.

## Utilities

The plugin also exposes some test utilities from `pytest_pystac`:

- `ARBITRARY_GEOM` -- a simple polygon geometry
- `ARBITRARY_BBOX` -- bounding box derived from `ARBITRARY_GEOM`
- `ARBITRARY_EXTENT` -- an `Extent` built from the arbitrary geometry
- `assert_to_from_dict(stac_object_class, d)` -- asserts that a STAC object class can round-trip through `from_dict` / `to_dict`
