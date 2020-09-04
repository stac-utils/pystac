# Changelog

## [v0.5.3]

### Added

- Added support for the pointcloud extension ([#176](https://github.com/stac-utils/pystac/pull/176))

## [v0.5.2]

Thank you to all the new contributors that contributed during STAC Sprint 6!

### Added

- Added support for the timestamps extension([#161](https://github.com/stac-utils/pystac/pull/161))
- `update_extent_from_items` method to Collection for updating Extent objects within a collection based on the contained items. ([#168](https://github.com/stac-utils/pystac/pull/168))
- `validate_all` method to Catalogs (and by inheritance collections) for validating all catalogs, collections and items contained in that catalog ([#162](https://github.com/azavea/pystac/pull/162))
- `validate_all` method to pystac.validdation for validating all catalogs, collections and items contained in STAC JSON dicts across STAC versions. ([#162](https://github.com/azavea/pystac/pull/162))
- Additional test coverage. ([#165](https://github.com/azavea/pystac/pull/165), [#171](https://github.com/azavea/pystac/pull/171))
- Added codecov to CI ([#163](https://github.com/stac-utils/pystac/pull/164))

### Fixed

- Fix bug that caused get_children to miss some links. ([#172](https://github.com/stac-utils/pystac/pull/172))
- Fixed bug in ExtensionIndex that was causing errors when trying to read help() for that object ([#159](https://github.com/stac-utils/pystac/pull/159))

### Changed

- Remove spaces in CBERS test library ([#157](https://github.com/stac-utils/pystac/pull/157))
- Changed some unit test assertions for better error messages ([#158](https://github.com/stac-utils/pystac/pull/158))
- Moved PySTAC to the [stac-utils](https://github.com/stac-utils) GitHub organization.

## [v0.5.1]

### Added

- A tutorial for creating extensions ([#150](https://github.com/azavea/pystac/pull/150))

### Fixed

- Fixed Satellite extension ID, using `sat` instead of `satellite` ([#146](https://github.com/azavea/pystac/pull/146), [#147](https://github.com/azavea/pystac/pull/147))

## [v0.5.0]

### Added

- Added support for the Projection extension([#125](https://github.com/azavea/pystac/pull/125))
- Add support for Item Asset properties ([#127](https://github.com/azavea/pystac/pull/127))
- Added support for dynamically changing the STAC version via `pystac.set_stac_version` and `pystac.get_stac_version` ([#130](https://github.com/azavea/pystac/pull/130))
- Added support for prerelease versions in version comparisions for the `pystac.serialization.identify` package ([#138](https://github.com/azavea/pystac/pull/138))
- Added validation for PySTAC STACObjects as well as arbitrary STAC JSON ([#139](https://github.com/azavea/pystac/pull/139))
- Added the ability to read HTTP and HTTPS uris by default ([#139](https://github.com/azavea/pystac/pull/139))

### Changed

- Clarification on null geometries, making bbox not required if a null geometry is used. ([#123](https://github.com/azavea/pystac/pull/123))
- Multiple extents (bounding boxes / intervals) are allowed per Collection ([#123](https://github.com/azavea/pystac/pull/123))
- Moved eo:gsd from eo extension to core gsd field in Item common metadata ([#123](https://github.com/azavea/pystac/pull/123))
asset extension renamed to item-assets and renamed assets field in Collections to item_assets ([#123](https://github.com/azavea/pystac/pull/123))
- `get_asset_bands` and `set_asset_bands` were renamed `get_bands` and `set_bands` and follow the new item asset property access pattern.
- Modified the `single-file-stac` extension to extend `Catalog` ([#128](https://github.com/azavea/pystac/pull/128))

### Removed

- ItemCollection was removed. ([#123](https://github.com/azavea/pystac/pull/123))
- The commons extension was removed. Collection properties will still be merged for pre-1.0.0-beta.1 items where appropriate ([#129](https://github.com/azavea/pystac/pull/129))
- Removed `pystac.STAC_VERSION`. See addition of `get_stac_version` above. ([#130](https://github.com/azavea/pystac/pull/130))

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
