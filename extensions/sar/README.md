# pystac-ext-sar

[PySTAC](https://pypi.org/project/pystac/) extension package for the [SAR Extension](https://github.com/stac-extensions/sar).
This extension provides fields for describing Synthetic-Aperture Radar (SAR) data, including instrument mode, frequency band, polarizations, product type, and observation direction.

## Supported versions

- [v1.3.2](https://stac-extensions.github.io/sar/v1.3.2/schema.json)

All SAR fields are optional. The implementation supports Items, Collection
fields, Item and Collection Assets, Item Asset Definitions, and Collection summaries.
Version 1.3.2 includes range bandwidth (`bandwidth`, in GHz), relative burst
numbers (`relative_burst`, starting at 1), beam identifiers (`beam_ids`), and
compact polarizations (`LH`, `LV`, `RH`, `RV`, `CH`, and `CV`).

`sar:product_type` is deprecated in favor of `product:type`, and
`sar:instrument_mode` is deprecated in favor of `instrument_modes` from the
instruments extension. Both remain available for compatibility.

## Versioning

This package's version corresponds to the version of the extension specification it targets.
When we release updates to the package code without changing the target extension version, we use [post releases](https://packaging.python.org/en/latest/discussions/versioning/#post-releases), e.g. `1.0.0.post1`.
