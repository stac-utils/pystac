# Changelog

## [Unreleased]

### Added

- Adds custom `header` support to `DefaultStacIO` ([#889](https://github.com/stac-utils/pystac/pull/889))
- Python 3.11 checks in CI ([#908](https://github.com/stac-utils/pystac/pull/908))

### Removed

### Changed

### Fixed

- Dependency resolution when installing `requirements-dev.txt` ([#897](https://github.com/stac-utils/pystac/pull/897))

## [v1.6.1]

### Fixed

- Pins `jsonschema` to >=4.0.1 to avoid a `RefResolutionError` when validating some extensions ([#857](https://github.com/stac-utils/pystac/pull/857))
- Fixed bug in custom StacIO example in documentation ([#879](https://github.com/stac-utils/pystac/pull/879))

## [v1.6.0]

### Removed

- Support for Python 3.7 ([#853](https://github.com/stac-utils/pystac/pull/853))

## [v1.5.0]

### Added

- Enum MediaType entry for PDF documents ([#758](https://github.com/stac-utils/pystac/pull/758))
- Enum MediaType entry for HTML documents ([#816](https://github.com/stac-utils/pystac/pull/816))
- Updated Link to obtain stac_io from owner root ([#762](https://github.com/stac-utils/pystac/pull/762))
- Replace test.com with special-use domain name. ([#769](https://github.com/stac-utils/pystac/pull/769))
- Updated AssetDefinition to have create, apply methods ([#768](https://github.com/stac-utils/pystac/pull/768))
- Add Grid Extension support ([#799](https://github.com/stac-utils/pystac/pull/799))
- Rich HTML representations for Jupyter Notebook display ([#743](https://github.com/stac-utils/pystac/pull/743))
- Add `assets` argument to `Item` and `Collection` init methods to allow adding Assets during object initialization ([#834](https://github.com/stac-utils/pystac/pull/834))

### Changed

- Updated Raster Extension from v1.0.0 to v1.1.0 ([#809](https://github.com/stac-utils/pystac/pull/809))

### Fixed

- Mutating `Asset.extra_fields` on a cloned `Asset` also mutated the original asset ([#826](https://github.com/stac-utils/pystac/pull/826))
- "How to create STAC catalogs" tutorial ([#775](https://github.com/stac-utils/pystac/pull/775))
- Add a `variables` argument, to accompany `dimensions`, for the `apply` method of stac objects extended with datacube ([#782](https://github.com/stac-utils/pystac/pull/782))
- Deepcopy collection properties on clone. Implement `clone` method for `Summaries` ([#794](https://github.com/stac-utils/pystac/pull/794))
- Collection assets are now preserved when using `Collection.clone` ([#834](https://github.com/stac-utils/pystac/pull/834))
- Docstrings for `StacIO.read_text` and `StacIO.write_text` now match the type annotations for the `source` argument. ([#835](https://github.com/stac-utils/pystac/pull/835))
- UTC timestamps now always have `tzutc` timezone even when system timezone is set to UTC. ([#848](https://github.com/stac-utils/pystac/pull/848))

## [v1.4.0]

### Added

- Experimental support for Python 3.11 ([#731](https://github.com/stac-utils/pystac/pull/731))
- Accept PathLike objects in `StacIO` I/O methods, `pystac.read_file` and `pystac.write_file` ([#728](https://github.com/stac-utils/pystac/pull/728))
- Support for Storage Extension ([#745](https://github.com/stac-utils/pystac/pull/745))
- Optional `StacIO` instance as argument to `Catalog.save`/`Catalog.normalize_and_save` ([#751](https://github.com/stac-utils/pystac/pull/751))
- More thorough docstrings for `pystac.utils` functions and classes ([#735](https://github.com/stac-utils/pystac/pull/735))

### Changed

- Label Extension version updated to `v1.0.1` ([#726](https://github.com/stac-utils/pystac/pull/726))
- Option to filter by `media_type` in `STACObject.get_links` and `STACObject.get_single_link`
  ([#704](https://github.com/stac-utils/pystac/pull/704))

### Fixed

- Self links no longer included in Items for "relative published" catalogs ([#725](https://github.com/stac-utils/pystac/pull/725))
- Adding New and Custom Extensions tutorial now up-to-date with new extensions API ([#724](https://github.com/stac-utils/pystac/pull/724))
- Clarify error message when using `PropertyExtension.ext(..., add_if_missing=True)` on an `Asset`
  with no owner ([#746](https://github.com/stac-utils/pystac/pull/746))
- Type errors when initializing `TemporalExtent` using a list of `datetime` objects ([#744](https://github.com/stac-utils/pystac/pull/744))

## [v1.3.0]

### Added

- Type annotations for instance attributes on all classes ([#705](https://github.com/stac-utils/pystac/pull/705))
- `extensions.datacube.Variable.to_dict` method ([#699](https://github.com/stac-utils/pystac/pull/699)])
- Clarification of possible errors when using `.ext` to extend an object ([#701](https://github.com/stac-utils/pystac/pull/701))
- Downloadable documentation as zipped HTML ([#715](https://github.com/stac-utils/pystac/pull/715))

### Removed

- Downloadable documentation in ePub format ([#715](https://github.com/stac-utils/pystac/pull/715))

### Changed

- Reorganize docs and switch to PyData theme ([#687](https://github.com/stac-utils/pystac/pull/687))

### Fixed

- Quickstart tutorial is now up-to-date with all package changes ([#674](https://github.com/stac-utils/pystac/pull/674))
- Creating absolute URLs from absolute URLs ([#697](https://github.com/stac-utils/pystac/pull/697)])
- Serialization error when using `pystac.extensions.file.MappingObject` ([#700](https://github.com/stac-utils/pystac/pull/700))
- Use `PropertiesExtension._get_property` to properly set return type in `TableExtension` ([#712](https://github.com/stac-utils/pystac/pull/712))
- `DatacubeExtension.variables` now has a setter ([#699](https://github.com/stac-utils/pystac/pull/699)])
- Landsat STAC tutorial is now up-to-date with all package changes ([#692](https://github.com/stac-utils/pystac/pull/674))
- Paths to sub-catalog files when using `Catalog.save` ([#714](https://github.com/stac-utils/pystac/pull/714))
- Link to PySTAC Introduction tutorial in tutorials index page ([#719](https://github.com/stac-utils/pystac/pull/719))

## [v1.2.0]

### Added

- Added Table-extension ([#646](https://github.com/stac-utils/pystac/pull/646))
- Stable support for Python 3.10 ([#656](https://github.com/stac-utils/pystac/pull/656))
- `.python-version` files are now ignored by Git ([#647](https://github.com/stac-utils/pystac/pull/647))
- Added a flag to allow users to skip transforming hierarchical link HREFs based on root catalog type ([#663](https://github.com/stac-utils/pystac/pull/663))

### Removed

- Exclude `tests` from package distribution. This should make the package lighter ([#604](https://github.com/stac-utils/pystac/pull/604))

### Changed

- Enable [strict
  mode](https://mypy.readthedocs.io/en/latest/command_line.html?highlight=strict%20mode#cmdoption-mypy-strict)
  for `mypy` ([#591](https://github.com/stac-utils/pystac/pull/591))
- Links will get their `title` from their target if no `title` is provided ([#607](https://github.com/stac-utils/pystac/pull/607))
- Relax typing on `LabelClasses` from `List` to `Sequence` ([#627](https://github.com/stac-utils/pystac/pull/627))
- Upgraded datacube-extension to version 2.0.0 ([#645](https://github.com/stac-utils/pystac/pull/645))
- By default, ItemCollections will not modify Item HREFs based on root catalog type to avoid performance costs of root link reads ([#663](https://github.com/stac-utils/pystac/pull/663))

### Fixed

- `generate_subcatalogs` can include multiple template values in a single subfolder layer
  ([#595](https://github.com/stac-utils/pystac/pull/595))
- Avoid implicit re-exports ([#591](https://github.com/stac-utils/pystac/pull/591))
- Fix issue that caused incorrect root links when constructing multi-leveled catalogs ([#658](https://github.com/stac-utils/pystac/pull/658))
- Regression where string `Enum` values were not serialized properly in methods like `Link.to_dict` ([#654](https://github.com/stac-utils/pystac/pull/654))

## [v1.1.0]

### Added

- Include type information during packaging for use with e.g. `mypy` ([#579](https://github.com/stac-utils/pystac/pull/579))
- Optional `dest_href` argument to `Catalog.save` to allow saving `Catalog` instances to
  locations other than their `self` href ([#565](https://github.com/stac-utils/pystac/pull/565))

### Changed

- Pin the rustc version in Continuous Integration to work around <https://github.com/rust-lang/cargo/pull/9727> ([#581](https://github.com/stac-utils/pystac/pull/581))

## [v1.0.1]

### Changed

- HREFs in `Link` objects with `rel == "self"` are converted to absolute HREFs ([#574](https://github.com/stac-utils/pystac/pull/574))

## [v1.0.0]

### Added

- `ProjectionExtension.crs_string` to provide a single string to describe the coordinate reference system (CRS).
  Useful because projections can be defined by EPSG code, WKT, or projjson.
  ([#548](https://github.com/stac-utils/pystac/pull/548))
- SAR Extension summaries([#556](https://github.com/stac-utils/pystac/pull/556))
- Migration for `sar:type` -> `sar:product_type` and `sar:polarization` ->
  `sar:polarizations` for pre-0.9 catalogs
  ([#556](https://github.com/stac-utils/pystac/pull/556))
- Migration from `eo:epsg` -> `proj:epsg` for pre-0.9 catalogs ([#557](https://github.com/stac-utils/pystac/pull/557))
- Collection summaries for Point Cloud Extension ([#558](https://github.com/stac-utils/pystac/pull/558))
- `PhenomenologyType` enum for recommended values of `pc:type` & `SchemaType` enum for
  valid values of `type` in [Point Cloud Schema
  Objects](https://github.com/stac-extensions/pointcloud#schema-object)
  ([#548](https://github.com/stac-utils/pystac/pull/548))
- `to_dict` and equality definition for `extensions.item_asset.AssetDefinition` ([#564](https://github.com/stac-utils/pystac/pull/564))
- `Asset.common_metadata` property ([#563](https://github.com/stac-utils/pystac/pull/563))

### Changed

- The `from_dict` method on STACObjects will set the object's root link when a `root` parameter is present. An ItemCollection `from_dict` with a root parameter will set the root on each of it's Items. ([#549](https://github.com/stac-utils/pystac/pull/549))
- Calling `ExtensionManagementMixin.validate_has_extension` with `add_if_missing = True`
  on an ownerless `Asset` will raise a `STACError` ([#554](https://github.com/stac-utils/pystac/pull/554))
- `PointcloudSchema` -> `Schema`, `PointcloudStatistic` -> `Statistic` for consistency
  with naming convention in other extensions
  ([#548](https://github.com/stac-utils/pystac/pull/548))
- `RequiredPropertyMissing` always raised when trying to get a required property that is
  `None` (`STACError` or `KeyError` was previously being raised in some cases)
  ([#561](https://github.com/stac-utils/pystac/pull/561))

### Fixed

- Added `Collections` as a type that can be extended for extensions whose fields can appear in collection summaries ([#547](https://github.com/stac-utils/pystac/pull/547))
- Allow resolved self links when getting an object's self href ([#555](https://github.com/stac-utils/pystac/pull/555))
- Fixed type annotation on SummariesLabelExtension.label_properties setter ([#562](https://github.com/stac-utils/pystac/pull/562))
- Allow comparable types with alternate parameter naming of __lt__ method to pass structural type linting for RangeSummary ([#562](https://github.com/stac-utils/pystac/pull/562))

## [v1.0.0-rc.3]

### Added

- (Experimental) support for Python 3.10 ([#473](https://github.com/stac-utils/pystac/pull/473))
- `LabelTask` enum in `pystac.extensions.label` with recommended values for
  `"label:tasks"` field ([#484](https://github.com/stac-utils/pystac/pull/484))
- `LabelMethod` enum in `pystac.extensions.label` with recommended values for
  `"label:methods"` field ([#484](https://github.com/stac-utils/pystac/pull/484))
- Label Extension summaries ([#484](https://github.com/stac-utils/pystac/pull/484))
- Timestamps Extension summaries ([#513](https://github.com/stac-utils/pystac/pull/513))
- Define equality and `__repr__` of `RangeSummary` instances based on `to_dict`
  representation ([#513](https://github.com/stac-utils/pystac/pull/513))
- Sat Extension summaries ([#509](https://github.com/stac-utils/pystac/pull/509))
- `Catalog.get_collections` for getting all child
  `Collections` for a catalog, and `Catalog.get_all_collections` for recursively getting
  all child `Collections` for a catalog and its children ([#511](https://github.com/stac-utils/pystac/pull/))

### Changed

- Renamed `Asset.properties` -> `Asset.extra_fields` and `Link.properties` ->
  `Link.extra_fields` for consistency with other STAC objects
  ([#510](https://github.com/stac-utils/pystac/pull/510))

### Fixed

- Bug in `pystac.serialization.identify_stac_object_type` where invalid objects with
  `stac_version == 1.0.0` were incorrectly identified as Catalogs
  ([#487](https://github.com/stac-utils/pystac/pull/487))
- `Link` constructor classes (e.g. `Link.from_dict`, `Link.canonical`, etc.) now return
  the calling class instead of always returning the `Link` class
  ([#512](https://github.com/stac-utils/pystac/pull/512))
- Sat extension now includes all fields defined in v1.0.0
  ([#509](https://github.com/stac-utils/pystac/pull/509))

### Removed

- `STAC_IO` class in favor of `StacIO`. This was deprecated in v1.0.0-beta.1 and has
  been removed in this release. ([#490](https://github.com/stac-utils/pystac/pull/490))
- Support for Python 3.6 ([#500](https://github.com/stac-utils/pystac/pull/500))

## [v1.0.0-rc.2]

### Added

- Add a `preserve_dict` parameter to `ItemCollection.from_dict` and set it to False when
  using `ItemCollection.from_file`.
  ([#468](https://github.com/stac-utils/pystac/pull/468))
- `StacIO.json_dumps` and `StacIO.json_loads` methods for JSON
  serialization/deserialization. These were "private" methods, but are now "public" and
  documented ([#471](https://github.com/stac-utils/pystac/pull/471))

### Changed

- `pystac.stac_io.DuplicateObjectKeyError` moved to `pystac.DuplicateObjectKeyError`
  ([#471](https://github.com/stac-utils/pystac/pull/471))

## [v1.0.0-rc.1]

### Added

- License file included in distribution ([#409](https://github.com/stac-utils/pystac/pull/409))
- Links to Issues, Discussions, and documentation sites ([#409](https://github.com/stac-utils/pystac/pull/409))
- Python minimum version set to `>=3.6` ([#409](https://github.com/stac-utils/pystac/pull/409))
- Code of Conduct ([#399](https://github.com/stac-utils/pystac/pull/399))
- `ItemCollection` class for working with GeoJSON FeatureCollections containing only
  STAC Items ([#430](https://github.com/stac-utils/pystac/pull/430))
- Support for Python 3.9 ([#420](https://github.com/stac-utils/pystac/pull/420))
- Migration for pre-1.0.0-rc.1 Stats Objects (renamed to Range Objects in 1.0.0-rc.3) ([#447](https://github.com/stac-utils/pystac/pull/447))
- Attempting to extend a `STACObject` that does not contain the extension's schema URI in
  `stac_extensions` raises new `ExtensionNotImplementedError` ([#450](https://github.com/stac-utils/pystac/pull/450))
- `STACObject.from_dict` now takes a `preserve_dict` parameter, which if False will avoid a call to deepcopy on the passed in dict and can result in performance gains (defaults to True. Reading from a file will use preserve_dict=False resulting in better performance. ([#454](https://github.com/stac-utils/pystac/pull/454))

### Changed

- Package author to `stac-utils`, email to `stac@radiant.earth`, url to this repo ([#409](https://github.com/stac-utils/pystac/pull/409))
- `StacIO.read_json` passes arbitrary positional and keyword arguments to
  `StacIO.read_text` ([#433](https://github.com/stac-utils/pystac/pull/433))
- `FileExtension` updated to work with File Info Extension v2.0.0 ([#442](https://github.com/stac-utils/pystac/pull/442))
- `FileExtension` only operates on `pystac.Asset` instances ([#442](https://github.com/stac-utils/pystac/pull/442))
- `*Extension.ext` methods now have an optional `add_if_missing` argument, which will
  add the extension schema URI to the object's `stac_extensions` list if it is not
  present ([#450](https://github.com/stac-utils/pystac/pull/450))
- `from_file` and `from_dict` methods on `STACObject` sub-classes always return instance
  of calling class ([#451](https://github.com/stac-utils/pystac/pull/451))

### Fixed

- `EOExtension.get_bands` returns `None` for asset without EO bands ([#406](https://github.com/stac-utils/pystac/pull/406))
- `identify_stac_object_type` returns `None` and `identify_stac_object` raises `STACTypeError` for non-STAC objects
  ([#402](https://github.com/stac-utils/pystac/pull/402))
- `ExtensionManagementMixin.add_to` is now idempotent (only adds schema URI to
  `stac_extensions` once per `Item` regardless of the number of calls) ([#419](https://github.com/stac-utils/pystac/pull/419))
- Version check for when extensions changed from short links to schema URIs
  ([#455](https://github.com/stac-utils/pystac/pull/455))
- Schema URI base for STAC 1.0.0-beta.1 ([#455](https://github.com/stac-utils/pystac/pull/455))

## [v1.0.0-beta.3]

### Added

- Summaries for View Geometry, Projection, and Scientific extensions ([#372](https://github.com/stac-utils/pystac/pull/372))
- Raster extension support ([#364](https://github.com/stac-utils/pystac/issues/364))
- solar_illumination field in eo extension ([#356](https://github.com/stac-utils/pystac/issues/356))
- Added `Link.canonical` static method for creating links with "canonical" rel type ([#351](https://github.com/stac-utils/pystac/pull/351))
- Added `RelType` enum containing common `rel` values ([#351](https://github.com/stac-utils/pystac/pull/351))
- Added support for summaries ([#264](https://github.com/stac-utils/pystac/pull/264))

### Fixed

- Links to STAC Spec point to latest supported version ([#368](https://github.com/stac-utils/pystac/pull/368))
- Links to STAC Extension pages point to repos in `stac-extensions` GitHub org ([#368](https://github.com/stac-utils/pystac/pull/368))
- Collection assets ([#373](https://github.com/stac-utils/pystac/pull/373))

### Removed

- Two v0.6.0 examples from the test suite ([#373](https://github.com/stac-utils/pystac/pull/373))

## [v1.0.0-beta.2]

### Changed

- Split `DefaultStacIO`'s reading and writing into two methods to allow subclasses to use the default link resolution behavior ([#354](https://github.com/stac-utils/pystac/pull/354))
- Increased test coverage for the pointcloud extension ([#352](https://github.com/stac-utils/pystac/pull/352))

### Fixed

- Reading json without orjson ([#348](https://github.com/stac-utils/pystac/pull/348))

### Removed

- Removed type information from docstrings, since it is redundant with function type
  annotations ([#342](https://github.com/stac-utils/pystac/pull/342))

## [v1.0.0-beta.1]

### Added

- Added type annotations across the library ([#309](https://github.com/stac-utils/pystac/pull/309))
- Added assets to collections ([#309](https://github.com/stac-utils/pystac/pull/309))
- `item_assets` extension ([#309](https://github.com/stac-utils/pystac/pull/309))
- `datacube` extension ([#309](https://github.com/stac-utils/pystac/pull/309))
- Added specific errors: `ExtensionAlreadyExistsError`, `ExtensionTypeError`, and `RequiredPropertyMissing`; moved custom exceptions to `pystac.errors` ([#309](https://github.com/stac-utils/pystac/pull/309))

### Fixed

- Validation checks in a few tests ([#346](https://github.com/stac-utils/pystac/pull/346))

### Changed

- API change: The extension API changed significantly. See ([#309](https://github.com/stac-utils/pystac/pull/309)) for more details.
- API change: Refactored the global STAC_IO object to an instance-specific `StacIO` implementation. ([#309](https://github.com/stac-utils/pystac/pull/309))
- Asset.get_absolute_href returns None if no absolute href can be inferred (previously the relative href that was passed in was returned) ([#309](https://github.com/stac-utils/pystac/pull/309))

### Removed

- Removed `properties` from Collections ([#309](https://github.com/stac-utils/pystac/pull/309))
- Removed `LinkMixin`, and implemented those methods on `STACObject` directly. STACObject was the only class using LinkMixin and this should not effect users ([#309](https://github.com/stac-utils/pystac/pull/309)
- Removed `single-file-stac` extension; this extension is being removed in favor of ItemCollection usage ([#309](https://github.com/stac-utils/pystac/pull/309)

### Deprecated

- Deprecated `STAC_IO` in favor of new `StacIO` class. `STAC_IO` will be removed in
  v1.0.0. ([#309](https://github.com/stac-utils/pystac/pull/309))

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

#### Extensions are wrappers around Catalogs, Collection and Items, and no longer inherit

This change affects the two extensions that were implemented for Item - `EOItem` and `LabelItem`
have become `EOItemExt` and `LabelItemExt`, and no longer inherit from Item.

This change was motivated by the 0.9 change that split some properties out from `eo` into
the `view` extension. If we kept an inheritance-based extension architecture, we would not
be able to account well for these new items that implemented both the `eo` and `view` extensions.

See the [Extensions section](https://pystac.readthedocs.io/en/0.4/concepts.html#extensions) in the
documentation for more information on the new way to use extensions.

#### Extensions have moved to their own package

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

[Unreleased]: <https://github.com/stac-utils/pystac/compare/v1.6.1..main>
[v1.6.1]: <https://github.com/stac-utils/pystac/compare/v1.6.0..v1.6.1>
[v1.6.0]: <https://github.com/stac-utils/pystac/compare/v1.5.0..v1.6.0>
[v1.5.0]: <https://github.com/stac-utils/pystac/compare/v1.4.0..v1.5.0>
[v1.4.0]: <https://github.com/stac-utils/pystac/compare/v1.3.0..v1.4.0>
[v1.3.0]: <https://github.com/stac-utils/pystac/compare/v1.2.0..v1.3.0>
[v1.2.0]: <https://github.com/stac-utils/pystac/compare/v1.1.0..v1.2.0>
[v1.1.0]: <https://github.com/stac-utils/pystac/compare/v1.0.1..v1.1.0>
[v1.0.1]: <https://github.com/stac-utils/pystac/compare/v1.0.0..v1.0.1>
[v1.0.0]: <https://github.com/stac-utils/pystac/compare/v1.0.0-rc.3..v1.0.0>
[v1.0.0-rc.3]: <https://github.com/stac-utils/pystac/compare/v1.0.0-rc.2..v1.0.0-rc.3>
[v1.0.0-rc.2]: <https://github.com/stac-utils/pystac/compare/v1.0.0-rc.1..v1.0.0-rc.2>
[v1.0.0-rc.1]: <https://github.com/stac-utils/pystac/compare/v1.0.0-beta.3..v1.0.0-rc.1>
[v1.0.0-beta.3]: <https://github.com/stac-utils/pystac/compare/v1.0.0-beta.2..v1.0.0-beta.3>
[v1.0.0-beta.2]: <https://github.com/stac-utils/pystac/compare/v1.0.0-beta.1..v1.0.0-beta.2>
[v1.0.0-beta.1]: <https://github.com/stac-utils/pystac/compare/v0.5.6..v1.0.0-beta.1>
[v0.5.6]: <https://github.com/stac-utils/pystac/compare/v0.5.5..v0.5.6>
[v0.5.5]: <https://github.com/stac-utils/pystac/compare/v0.5.4..v0.5.5>
[v0.5.4]: <https://github.com/stac-utils/pystac/compare/v0.5.3..v0.5.4>
[v0.5.3]: <https://github.com/stac-utils/pystac/compare/v0.5.2..v0.5.3>
[v0.5.2]: <https://github.com/stac-utils/pystac/compare/v0.5.1..v0.5.2>
[v0.5.1]: <https://github.com/stac-utils/pystac/compare/v0.5.0..v0.5.1>
[v0.5.0]: <https://github.com/stac-utils/pystac/compare/v0.4.0..v0.5.0>
[v0.4.0]: <https://github.com/stac-utils/pystac/compare/v0.3.4..v0.4.0>
[v0.3.4]: <https://github.com/stac-utils/pystac/compare/v0.3.3..v0.3.4>
[v0.3.3]: <https://github.com/stac-utils/pystac/compare/v0.3.2..v0.3.3>
[v0.3.2]: <https://github.com/stac-utils/pystac/compare/v0.3.1..v0.3.2>
[v0.3.1]: <https://github.com/stac-utils/pystac/compare/v0.3.0..v0.3.1>
[v0.3.0]: <https://github.com/stac-utils/pystac/tree/v0.3.0>
