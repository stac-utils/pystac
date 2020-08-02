# Changelog

## Unreleased

### Added

- Added support for the Projection extension([#125](https://github.com/azavea/pystac/pull/125))

### Changed

- Clarification on null geometries, making bbox not required if a null geometry is used. ([#123](https://github.com/azavea/pystac/pull/123))
- Multiple extents (bounding boxes / intervals) are allowed per Collection ([#123](https://github.com/azavea/pystac/pull/123))
- Moved eo:gsd from eo extension to core gsd field in Item common metadata ([#123](https://github.com/azavea/pystac/pull/123))
asset extension renamed to item-assets and renamed assets field in Collections to item_assets ([#123](https://github.com/azavea/pystac/pull/123))

### Removed

- ItemCollection removed from stac-spec core repo, will migrate to stac-api-spec as that is the only place it is used. ([#123](https://github.com/azavea/pystac/pull/123))

## [v0.4.0]

The two major changes for this release are:
- Upgrade to STAC 0.9.0
- Refactor the extensions API to accomidate items that implement multiple extesions (e.g. `eo` and `view`)

See the [stac-spec 0.9.0 changelog](https://github.com/radiantearth/stac-spec/blob/v0.9.0/CHANGELOG.md) and issue [#65](https://github.com/azavea/pystac/issues/65) for more information.

### API Changes

These are the major API changes that will have to be accounted for when upgrading PySTAC:

#### Extensions are wrappers around Catalogs, Collection and Items, and no longer inheret.

This change affects the two extensions that were implemented for Item - `EOItem` and `LabelItem`
have become `EOItemExt` and `LabelItemExt`, and no longer inheret from Item.

This change was motivated by the 0.9 change that split some properties out from `eo` into
the `view` extension. If we kept an inheritance-based extension architecture, we would not
be able to account well for these new items that implemented both the `eo` and `view` extensions.

See the [Extensions section](https://pystac.readthedocs.io/en/0.4/concepts.html#extensions) in the
documentation for more information on the new way to use extensions.

#### Extensions have moved to their own package:
- `pystac.label` -> `pystac.extensions.label`
- `pystac.eo` -> `pystac.extensions.eo`
- `pystac.single_file_stac` -> `pystac.extensions.single_file_stac`

### Added

- `pystac.read_file` as a convenience function for reading in a STACObject from a file at a URI which delegates to `STACObject.from_file`.
- `pystac.read_file` as a convenience function for reading in a STACObject from a file at a URI.
- Added support for the [view](https://github.com/radiantearth/stac-spec/tree/v0.9.0/extensions/view) extension.
- Added support for the [commons](https://github.com/radiantearth/stac-spec/tree/v0.9.0/extensions/commons) extension.

### Changed
- Migrated CI workflows from Travis CI to GitHub Actions [#108](https://github.com/azavea/pystac/pull/108)
- Dropped support for Python 3.5 [#108](https://github.com/azavea/pystac/pull/108)

- Extension classes for label, eo and single-file-stac were moved to the `pystac.extensions` package.
- the eo and label extensions changed from being a subclass of Item to wrapping items. __Note__: This is a major change in the API for dealing with extensions. See the note below for more information.
- Renamed the class that enumerates extension names from `Extension` to `Extensions`
- Asset properties always return a dict instead of being None for Assets that have non-core properties.
- The `Band` constructor in the EO extension changed to taking a dict. To create a band from property values,
use `Band.create`


## [v0.3.4] - 2020-06-20

### Changed

- Further narrow version for SAR extension [#85](https://github.com/azavea/pystac/pull/85)

### Fixed

- Fixed issue with reading ItemCollections directly. [#86](https://github.com/azavea/pystac/pull/86)
- Fix bug in `make_absolute_href` [#94](https://github.com/azavea/pystac/pull/94)
- Fixed issues with `fully_resolve` [#98](https://github.com/azavea/pystac/pull/98)
- Fixed a bug when root link was not set [#100](https://github.com/azavea/pystac/pull/100)

## [v0.3.3] - 2020-02-05

### Added

- Allow for backwards compatibilty for reading STAC [#77](https://github.com/azavea/pystac/pull/70)

### Fixed

- Fix issue with multiple collection reads per item [#79](https://github.com/azavea/pystac/pull/79)
- Fix issue with iteration of children in `catalog.walk` [#78](https://github.com/azavea/pystac/pull/78)
- Allow v0.7.0 sar items to fit in version range [#80](https://github.com/azavea/pystac/pull/80)

## [v0.3.2] - 2020-01-28

### Added

- Add functionality for identifying STAC JSON information [#50](https://github.com/azavea/pystac/pull/50)

### Fixed

- Documentation improvements [#44](https://github.com/azavea/pystac/pull/44)
- Updated MediaTypes to reflect correct GeoTIFF and COG names [#66](https://github.com/azavea/pystac/pull/66)
- Fix utils to work with windows paths. [#68](https://github.com/azavea/pystac/pull/68)
- Modified output datetime strings to ISO8601. [#69](https://github.com/azavea/pystac/pull/69)
- Respect tzinfo in the provided datetime [#70](https://github.com/azavea/pystac/pull/70)
- Set asset owner to item when reading in items.[#71](https://github.com/azavea/pystac/pull/71)
- Fixed catalog and collection clone logic to avoid dupliction root link [#72](https://github.com/azavea/pystac/pull/72)

## [v0.3.1] - 2019-11-04

### Added

- Add methods for removing single items and children from catalogs.
- Add methods for removing objects from the ResolvedObjectCache.

### Fixed

- Fixed issue where cleared items and children were still in the root object cache.

### Changed

- Moved STAC version to 0.8.1
- LabelItem reduced validation as there is some confusion on how segmentation classes

## [v0.3.0] - 2019-10-31

Initial release.
