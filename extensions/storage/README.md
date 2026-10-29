# pystac-ext-storage

[PySTAC](https://pypi.org/project/pystac/) extension package for the [Storage Extension](https://github.com/stac-extensions/storage).
This extension provides fields for describing cloud storage attributes of assets, including storage platform, region, tier, and requester-pays configuration.

## Supported versions

- [v2.0.0](https://stac-extensions.github.io/storage/v2.0.0/schema.json)
- [v1.0.0](https://stac-extensions.github.io/storage/v1.0.0/schema.json)

## Versioning

This package's MAJOR and MINOR versions match the version of the extension itself, e.g. **pystac-ext-storage** v2.0.0 corresponds to the [v2.0.0](https://github.com/stac-extensions/storage/releases/tag/v2.0.0) release of the **storage** extension.
When we release updates to the package code without changing the target extension version, we use [PATCH releases](https://packaging.python.org/en/latest/discussions/versioning/#valid-version-numbers).
