# Changelog

## unreleased

### Added

### Fixed

### Changed

### Removed

## [v0.5.6]

### Added

- HIERARCHICAL_LINKS array constant of all the types of hierarchical links (self is not included) ([#290](https://github.com/stac-utils/pystac/pull/290))

### Fixed

- Fixed error when accessing the statistics attribute of the pointcloud extension when no statistics were defined ([#282](https://github.com/stac-utils/pystac/pull/282))
- Fixed exception being thrown when calling set_self_href on items with assets that have relative hrefs ([#291](https://github.com/stac-utils/pystac/pull/291))

### Changed

- Link behavior - link URLs can be either relative or absolute. Hierarchical (e.g., parent, child) links are made relative or absolute based on the value of the root catalog's `catalog_type` field ([#290](https://github.com/stac-utils/pystac/pull/290))
- Internal self hrefs are set automatically when adding Items or Children to an existing catalog. This removes the need to call `normalize_hrefs` or manual setting of the hrefs for newly added STAC objects ([#294](https://github.com/stac-utils/pystac/pull/294))
- Catalog.generate_subcatalogs is an order of magnitude faster ([#295](https://github.com/stac-utils/pystac/pull/295))

### Removed

- Removed LinkType class and the `link_type` field from links ([#290](https://github.com/stac-utils/pystac/pull/290))

## [v0.5.5]

### Added

- Added support for STAC file extension ([#270](https://github.com/stac-utils/pystac/pull/270))

### Fixed

- Fix handling of optional properties when using apply on view extension ([#259](https://github.com/stac-utils/pystac/pull/259))
- Fixed issue with setting None into projection extension fields that are not required breaking validation ([#269](https://github.com/stac-utils/pystac/pull/269))

### Changed

- Subclass relevant classes from `enum.Enum`. This allows iterating over the class' contents. The `__str__` method is overwritten so this should not break backwards compatibility. ([#261](https://github.com/stac-utils/pystac/pull/261))
- Extract method to correctly handle setting properties in Item/Asset for ItemExtensions ([#272](https://github.com/stac-utils/pystac/pull/272))

## [v0.5.4]

### Added

- SAT Extension ([#236](https://github.com/stac-utils/pystac/pull/236))
- Add support for the scientific extension. ([#199](https://github.com/stac-utils/pystac/pull/199))

### Fixed

- Fix unexpected behaviour of `generate_subcatalogs` ([#241](https://github.com/stac-utils/pystac/pull/241))
- Get eo bands defined in assets only ([#243](https://github.com/stac-utils/pystac/pull/243))
- Collection TemporalExtent can be open ended ([#247](https://github.com/stac-utils/pystac/pull/247))
- Make asset HREFs relative or absolute based on CatalogType during save ([#251](https://github.com/stac-utils/pystac/pull/251))

### Changed

- Be more strict with CatalogType in `Catalog.save` ([#244](https://github.com/stac-utils/pystac/pull/244))


## [v0.5.3]

### Added

- Added support for the pointcloud extension ([#176](https://github.com/stac-utils/pystac/pull/176))
- Added support for the version extension ([#193](https://github.com/stac-utils/pystac/pull/193))
- Added support for the SAR extension ([#203](https://github.com/stac-utils/pystac/pull/203))
- Added the capability to more flexibly organize STACs using `normalize_hrefs` ([#219](https://github.com/stac-utils/pystac/pull/219))
- Added a 'generate_subcatalogs' to Catalog to allow for subcatalogs to be created by using item properties via a template string ([#219](https://github.com/stac-utils/pystac/pull/219))
- Added 'from_items' method to Extent ([#223](https://github.com/stac-utils/pystac/pull/223))
- Added a `catalog_type` property to track the CatalogType of read in or previously saved catalogs ([#224](https://github.com/stac-utils/pystac/pull/224))
- Added a tutorial for creating Landsat 8 STACs ([#181](https://github.com/stac-utils/pystac/pull/181))
- Added codespell to CI ([#206](https://github.com/stac-utils/pystac/pull/206))
- Added more testing to Links ([#211](https://github.com/stac-utils/pystac/pull/211))

### Fixed

- Fixed issue that can cause infinite recursion during full resolve ([#204](https://github.com/stac-utils/pystac/pull/193))
- Fixed issue that required label_classes in label items ([#201](https://github.com/stac-utils/pystac/pull/201))
- Fixed issue that caused geometries and bboxes produced by Shapely to fail PySTAC's validaton ([#201](https://github.com/stac-utils/pystac/pull/201))
- Allow for path prefixes like /vsitar/ ([#208](https://github.com/stac-utils/pystac/pull/208))
- Fix Item set_self_href to ensure item asset locations do not break ([#226](https://github.com/stac-utils/pystac/pull/226))
- Fixed an incorrect exception being thrown from Link.get_href() if there is no target_href ([#201](https://github.com/stac-utils/pystac/pull/201))
- Fixed issue where 0.9.0 items were executing the commons extension logic when they shouldn't ([#221](https://github.com/stac-utils/pystac/pull/221))
- Fixed issue where cloned assets did not have their owning Items set ([#228](https://github.com/stac-utils/pystac/pull/228))
- Fixed issue that caused make_asset_hrefs_relative to produce incorrect HREFs when asset HREFs were already relative ([#229](https://github.com/stac-utils/pystac/pull/229))
- Improve error handling when accidentally importing a Collection with Catalog ([#186](https://github.com/stac-utils/pystac/issues/186))
- Fixed spacenet tutorial bbox issue ([#201](https://github.com/stac-utils/pystac/pull/201))
- Fix formatting of error message in stac_validator ([#190](https://github.com/stac-utils/pystac/pull/204))
- Fixed typos ([#192](https://github.com/stac-utils/pystac/pull/192), [#195](https://github.com/stac-utils/pystac/pull/195))

### Changed

- Refactor caching to utilize HREFs and parent IDs. STAC objects now no longer need unique IDs to work with PySTAC ([#214](https://github.com/stac-utils/pystac/pull/214), [#160](https://github.com/stac-utils/pystac/issues/160))
- Allow a user to pass a single list as bbox and interval for `SpatialExtent` and `TemporalExtent` ([#201](https://github.com/stac-utils/pystac/pull/201), fixes [#198](https://github.com/stac-utils/pystac/issues/198))

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
- Added support for prerelease versions in version comparisons for the `pystac.serialization.identify` package ([#138](https://github.com/azavea/pystac/pull/138))
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
- Refactor the extensions API to accommodate items that implement multiple extensions (e.g. `eo` and `view`)

See the [stac-spec 0.9.0 changelog](https://github.com/radiantearth/stac-spec/blob/v0.9.0/CHANGELOG.md) and issue [#65](https://github.com/azavea/pystac/issues/65) for more information.

### API Changes

These are the major API changes that will have to be accounted for when upgrading PySTAC:

#### Extensions are wrappers around Catalogs, Collection and Items, and no longer inherit.

This change affects the two extensions that were implemented for Item - `EOItem` and `LabelItem`
have become `EOItemExt` and `LabelItemExt`, and no longer inherit from Item.

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

- Allow for backwards compatibility for reading STAC [#77](https://github.com/azavea/pystac/pull/70)

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

[Unreleased]: <https://github.com/stac-utils/pystac/compare/v0.5.6...main>
[v0.5.6]: <https://github.com/stac-utils/pystac/compare/v0.5.5..v0.5.6>
[v0.5.5]: <https://github.com/stac-utils/pystac/compare/v0.5.4..v0.5.5>
[v0.5.4]: <https://github.com/stac-utils/pystac/compare/v0.5.3..v0.5.4>
[v0.5.3]: <https://github.com/stac-utils/pystac/compare/v0.5.2...v0.5.3>
[v0.5.2]: <https://github.com/stac-utils/pystac/compare/v0.5.1...v0.5.2>
[v0.5.1]: <https://github.com/stac-utils/pystac/compare/v0.5.0...v0.5.1>
[v0.5.0]: <https://github.com/stac-utils/pystac/compare/v0.4.0...v0.5.0>
[v0.4.0]: <https://github.com/stac-utils/pystac/compare/v0.3.4...v0.4.0>
[v0.3.4]: <https://github.com/stac-utils/pystac/compare/v0.3.3...v0.3.4>
[v0.3.3]: <https://github.com/stac-utils/pystac/compare/v0.3.2...v0.3.3>
[v0.3.2]: <https://github.com/stac-utils/pystac/compare/v0.3.1...v0.3.2>
[v0.3.1]: <https://github.com/stac-utils/pystac/compare/v0.3.0...v0.3.1>
[v0.3.0]: <https://github.com/stac-utils/pystac/tree/v0.3.0>

