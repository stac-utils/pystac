# Changelog

## [Unreleased]

### Added

- Added to pystac.MediaType values VND_APACHE_PARQUET and VND_ZARR with the current standard
  media type value for these types and new media types COPC and VND_PMTILES
  ([#1554](https://github.com/stac-utils/pystac/pull/1554))

### Changed

- Updated storage extension to v2.0.0

### Fixed

- More permissive collection extent deserialization ([#1559](https://github.com/stac-utils/pystac/pull/1559))
- Type of `proj:code` setter ([#1560](https://github.com/stac-utils/pystac/pull/1560))

## [v1.13.0] - 2025-04-15

### Added

- Projection extension: migrate Assets and Item-Assets ([#1549](https://github.com/stac-utils/pystac/pull/1549))
- `Collection.from_items` for creating a `pystac.Collection` from an `ItemCollection` ([#1522](https://github.com/stac-utils/pystac/pull/1522))
- `extensions.mlm` for supporting the [MLM](https://github.com/stac-extensions/mlm) extension ([#1542](https://github.com/stac-utils/pystac/pull/1542))

### Fixed

- `proj:epsg` migration when `None` ([#1544](https://github.com/stac-utils/pystac/pull/1544))
- fixed missing parameter "title" in pystac.extensions.classification.Classification ([#1539](https://github.com/stac-utils/pystac/pull/1539))

## [v1.12.2] - 2025-02-19

### Fixed

- Make sure that `VersionRange` has `VersionID`s rather than strings ([#1512](https://github.com/stac-utils/pystac/pull/1512))

## [v1.12.1] - 2025-01-27

### Changed

- `migrate=True` is now the default in `from_dict` ([#1509](https://github.com/stac-utils/pystac/pull/1509))

### Fixed

- Fall back to `epsg` when `code` is not present in the Projection extension ([#1505](https://github.com/stac-utils/pystac/pull/1505), [#1510](https://github.com/stac-utils/pystac/pull/1510))

## [v1.12.0] - 2025-01-23

### Added

- Top-level `item_assets` dict on `Collection`s ([#1476](https://github.com/stac-utils/pystac/pull/1476))
- Render Extension ([#1465](https://github.com/stac-utils/pystac/pull/1465))
- Filter by links by list of media_types

### Changed

- Write STAC v1.1.0 ([#1427](https://github.com/stac-utils/pystac/pull/1427))
- Use [uv](https://github.com/astral-sh/uv) for development dependencies and docs ([#1439](https://github.com/stac-utils/pystac/pull/1439))
- Correctly detect absolute file path ref on windows, reflecting change in python 3.13 ([#1475](https://github.com/stac-utils/pystac/pull/14750)) (only effects python 3.13)
- Deprecated `ItemAssetExtension` ([#1476](https://github.com/stac-utils/pystac/pull/1476))
- Update Projection Extension to version 2 - proj:epsg -> proj:code ([#1287](https://github.com/stac-utils/pystac/pull/1287))
- Update migrate code to handle license changes in STAC spec 1.1.0 ([#1491](https://github.com/stac-utils/pystac/pull/1491))
- Allow links to have `file://` prefix - but don't write them that way by default ([#1489](https://github.com/stac-utils/pystac/pull/1489))
- For `get_root_link`, `get_child_links`, `get_item_links`: Ensure json media types ([#1497](https://github.com/stac-utils/pystac/pull/1497))
- Raise `STACError` with message when a link is expected to resolve to a STAC object but doesn't ([#1500](https://github.com/stac-utils/pystac/pull/1500))
- Raise an error on APILayoutStrategy when root_href is non-url ([#1498](https://github.com/stac-utils/pystac/pull/1498))

### Fixed

- Use `application/geo+json` for `item` links ([#1495](https://github.com/stac-utils/pystac/pull/1495))
- Includes the scientific extension in Item's ext interface ([#1496](https://github.com/stac-utils/pystac/pull/1496))
- Fixes all broken documentation links and adds check to CI ([#1499](https://github.com/stac-utils/pystac/pull/1499))

## [v1.11.0] - 2024-09-26

### Added

- Add netCDF to pystac.media_type ([#1386](https://github.com/stac-utils/pystac/pull/1386))
- Add convenience method for accessing pystac_client ([#1365](https://github.com/stac-utils/pystac/pull/1365))
- Fix field ordering when saving `Item`s ([#1423](https://github.com/stac-utils/pystac/pull/1423))
- Add keywords to common metadata ([#1443](https://github.com/stac-utils/pystac/pull/1443))
- Add roles to common metadata ([#1444](https://github.com/stac-utils/pystac/pull/1444/files))

### Changed

- Allow object ID as input for getting APILayoutStrategy hrefs and add `items`, `collections`, `search`, `conformance`, `service_desc` and `service_doc` href methods ([#1335](https://github.com/stac-utils/pystac/pull/1335))
- Updated classification extension to v2.0.0 ([#1359](https://github.com/stac-utils/pystac/pull/1359))
- Update docstring of `name` argument to `Classification.apply` and `Classification.create` to agree with extension specification ([#1356](https://github.com/stac-utils/pystac/pull/1356))
- Add example of custom `StacIO` for Azure Blob Storage to docs ([#1372](https://github.com/stac-utils/pystac/pull/1372))
- Noted that collection links can be used in non-item objects in STAC v1.1.0 ([#1393](https://github.com/stac-utils/pystac/pull/1393))
- Move test, docs, and bench requirements out of pyproject.toml ([#1407](https://github.com/stac-utils/pystac/pull/1407))
- Clarify inclusive datetime ranges, update default license, and ensure description is not empty ([#1445](https://github.com/stac-utils/pystac/pull/1445))

### Fixed

- Make `get_all_collections` properly recursive ([#1361](https://github.com/stac-utils/pystac/pull/1361))
- Set `Item::collection` to `None` when there is no collection ([#1400](https://github.com/stac-utils/pystac/pull/1400))
- Recursion error when `name` not set on `eo:bands` ([#1406](https://github.com/stac-utils/pystac/pull/1406))

### Removed

- Python 3.9 ([#1384](https://github.com/stac-utils/pystac/pull/1384), [#1388](https://github.com/stac-utils/pystac/pull/1388))

## [v1.10.1] - 2024-05-03

### Fixed

- Don't transform hrefs in `Item.__getstate__` ([#1337](https://github.com/stac-utils/pystac/pull/1337))

## [v1.10.0] - 2024-03-28

### Added

- Add `validator` input to `STACObject.validate` for inline reference of the validator to use ([#1320](https://github.com/stac-utils/pystac/pull/1320))
- Add APILayoutStrategy ([#1294](https://github.com/stac-utils/pystac/pull/1294))
- Allow setting a default layout strategy for Catalog ([#1295](https://github.com/stac-utils/pystac/pull/1295))

### Changed

- Update css for HTML display ([#1311](https://github.com/stac-utils/pystac/pull/1311))
- Made item pickles smaller by changing how nested links are stored([#1285](https://github.com/stac-utils/pystac/pull/1285))
- Updated documentation code examples that use AWS S3 for file storage ([#1308](https://github.com/stac-utils/pystac/pull/1308))

### Fixed

- No longer use the `datetime.utcnow` method that has been deprecated in Python 3.12 ([#1283](https://github.com/stac-utils/pystac/pull/1283))

## [v1.9.0] - 2023-10-23

### Added

- Simpler extension interface ([#1243](https://github.com/stac-utils/pystac/pull/1243))
- More permissive schema_uri matching to allow future versions of extension schemas ([#1231](https://github.com/stac-utils/pystac/pull/1231))
- Better error messages from jsonschema validation ([#1233](https://github.com/stac-utils/pystac/pull/1233))
- `validate_all_dict` replaces the previous implementation of `validate_all` (i.e., `validate_all` was renamed to `validate_all_dict`, and `validate_all` was changed as described below) ([#1246](https://github.com/stac-utils/pystac/pull/1246))
- Python 3.12 ([#1260](https://github.com/stac-utils/pystac/pull/1260))

### Changed

- `validate_all` now accepts a `STACObject` (in addition to accepting a dict, which is now deprecated), but prohibits supplying a value for `href`, which must be supplied _only_ when supplying an object as a dict.  Once `validate_all` removes support for an object as a dict, the `href` parameter will also be removed. ([#1246](https://github.com/stac-utils/pystac/pull/1246))
- Report `href` when schema url resolution fails ([#1263](https://github.com/stac-utils/pystac/pull/1263))
- Version extension updated to v1.2.0 ([#1262](https://github.com/stac-utils/pystac/pull/1262))
- Datacube extension updated to v2.2.0 ([#1269](https://github.com/stac-utils/pystac/pull/1269))

### Fixed

- Typing of `href` arguments ([#1234](https://github.com/stac-utils/pystac/pull/1234))
- Interactions between **pytest-recording** and the validator schema cache ([#1242](https://github.com/stac-utils/pystac/pull/1242))
- Call `registry` when instantiating `Draft7Validator` ([#1240](https://github.com/stac-utils/pystac/pull/1240))
- Migration for the classification, datacube, table, and timestamps extensions ([#1258](https://github.com/stac-utils/pystac/pull/1258))
- Handling of `bboxes` and `intervals` arguments to `SpatialExtent` and `TemporalExtent`, respectively ([#1268](https://github.com/stac-utils/pystac/pull/1268))

### Removed

- Python 3.8 support ([#1236](https://github.com/stac-utils/pystac/pull/1236))

### Deprecated

- `ExtensionManagementMixin.validate_has_extension` is replaced with `ExtensionManagementMixin.ensure_has_extension`. Calling `ExtensionManagementMixin.validate_has_extension` will raise a `DeprecationWarning` and call `ExtensionManagementMixin.ensure_has_extension` ([#1248](https://github.com/stac-utils/pystac/pull/1248))
- `validate_all` for dicts; use `validate_all_dict` instead ([#1246](https://github.com/stac-utils/pystac/pull/1246))
- `Label` extension ([#1270](https://github.com/stac-utils/pystac/pull/1270))

## [v1.8.4] - 2023-09-22

### Added

- Permissive deserialization of Collection temporal extents ([#1222](https://github.com/stac-utils/pystac/pull/1222))

### Fixed

- Update usage of jsonschema ([#1215](https://github.com/stac-utils/pystac/pull/1215))

### Deprecated

- `pystac.validation.local_validator.LocalValidator` ([#1215](https://github.com/stac-utils/pystac/pull/1215))

## [v1.8.3] - 2023-07-12

### Added

- Allow to pass a Dict with field names and summary strategies to the `fields` parameter in the `Summarizer` constructor ([#1195](https://github.com/stac-utils/pystac/pull/1195))

### Changed

- Pin jsonschema version to <4.18 until regresssions are fixed

### Fixed

- Fix the documentation rendering of the `fields` parameter in the `Summarizer` constructor ([#1195](https://github.com/stac-utils/pystac/pull/1195))

## [v1.8.2] - 2023-07-12

### Fixed

- Explicitly re-export HREF from `link` ([#1182](https://github.com/stac-utils/pystac/pull/1182))
- Include `fields-normalized.json` in build ([#1188](https://github.com/stac-utils/pystac/pull/1188))

## [v1.8.1] - 2023-06-30

### Fixed

- Include jsonschemas in package ([#1181](https://github.com/stac-utils/pystac/pull/1181))

## [v1.8.0] - 2023-06-27

### Added

- `sort_links_by_id` to Catalog `get_child()` and `modify_links` to `get_stac_objects()` ([#1064](https://github.com/stac-utils/pystac/pull/1064))
- `*ids` to Catalog and Collection `get_items()` for only including the provided ids in the iterator ([#1075](https://github.com/stac-utils/pystac/pull/1075))
- `recursive` to Catalog and Collection `get_items()` to walk the sub-catalogs and sub-collections ([#1075](https://github.com/stac-utils/pystac/pull/1075))
- MGRS Extension ([#1088](https://github.com/stac-utils/pystac/pull/1088))
- All HTTP requests are logged when level is set to `logging.DEBUG` ([#1096](https://github.com/stac-utils/pystac/pull/1096))
- `set_parent` to Catalog `add_item` and `add_child` to avoid overriding existing parents ([#1117](https://github.com/stac-utils/pystac/pull/1117), [#1155](https://github.com/stac-utils/pystac/pull/1155))
- `owner` attribute to `AssetDefinition` in the item-assets extension ([#1110](https://github.com/stac-utils/pystac/pull/1110))
- Windows `\\` path delimiters are converted to POSIX style `/` delimiters ([#1125](https://github.com/stac-utils/pystac/pull/1125))
- Updated raster extension to work with the item_assets extension's AssetDefinition objects ([#1110](https://github.com/stac-utils/pystac/pull/1110))
- Classification extension ([#1093](https://github.com/stac-utils/pystac/pull/1093)), with support for adding classification information to item_assets' `AssetDefinition`s and raster's `RasterBand` objects.
- `get_derived_from`, `add_derived_from` and `remove_derived_from` to Items ([#1136](https://github.com/stac-utils/pystac/pull/1136))
- `ItemEOExtension.get_assets` for getting assets filtered on band `name` or `common_name` ([#1140](https://github.com/stac-utils/pystac/pull/1140))
- `max_items` and `recursive` to `Catalog.validate_all` ([#1141](https://github.com/stac-utils/pystac/pull/1141))
- `KML` as a built in media type ([#1127](https://github.com/stac-utils/pystac/issues/1127))
- `move/copy/delete` operations for local Assets ([#1158](https://github.com/stac-utils/pystac/issues/1158))
- Latest core STAC spec jsonshemas are included in pytstac and used for validation ([#1165](https://github.com/stac-utils/pystac/pull/1165))
- Xarray Assets Extension class ([#1161](https://github.com/stac-utils/pystac/pull/1161))

### Changed

- Include a copy of the `fields.json` file (for summaries) with each distribution of PySTAC ([#1045](https://github.com/stac-utils/pystac/pull/1045))
- Make Catalog, Collection `.get_assets()` return a deepcopy ([#1087](https://github.com/stac-utils/pystac/pull/1087))
- Removed documentation references to `to_dict` methods returning JSON ([#1074](https://github.com/stac-utils/pystac/pull/1074))
- Expand support for previous extension schema URIs ([#1091](https://github.com/stac-utils/pystac/pull/1091))
- Use `pyproject.toml` instead of `setup.py` ([#1100](https://github.com/stac-utils/pystac/pull/1100))
- `DefaultStacIO` now raises an error if it tries to write to a non-local url ([#1107](https://github.com/stac-utils/pystac/pull/1107))
- Allow instantiation of pystac objects even with `"stac_extensions": null` ([#1109](https://github.com/stac-utils/pystac/pull/1109))
- Make `Link.to_dict()` only contain strings ([#1114](https://github.com/stac-utils/pystac/pull/1114))
- Updated raster extension to work with the item_assets extension's AssetDefinition objects ([#1110](https://github.com/stac-utils/pystac/pull/1110))
- Return all validation errors from validation methods of `JsonSchemaSTACValidator` ([#1120](https://github.com/stac-utils/pystac/pull/1120))
- EO extension updated to v1.1.0 ([#1131](https://github.com/stac-utils/pystac/pull/1131))
- Use `id` in STACTypeError instead of entire dict ([#1126](https://github.com/stac-utils/pystac/pull/1126))
- Make sure that `get_items` is backwards compatible ([#1139](https://github.com/stac-utils/pystac/pull/1139))
- Make `_repr_html_` look like `_repr_json_` output ([#1142](https://github.com/stac-utils/pystac/pull/1142))
- Improved error message when `.ext` is called on a Collection ([#1157](https://github.com/stac-utils/pystac/pull/1157))
- `add_child` and `add_item` return a Link object instead of None ([#1160](https://github.com/stac-utils/pystac/pull/1160))
- `add_children` and `add_items` return a list of Link objects instead of None ([#1160](https://github.com/stac-utils/pystac/pull/1160))
- Include collection assets in `make_all_asset_hrefs_relative/absolute` ([#1168](https://github.com/stac-utils/pystac/pull/1168))
- Use cassettes for all tests that pull files from remote ([#1162](https://github.com/stac-utils/pystac/pull/1162))
- Landsat tutorial notebook updated to collection 2 sources ([#1152](https://github.com/stac-utils/pystac/pull/1152))

### Fixed

- Include the item's root when resolving its collection link ([#1171](https://github.com/stac-utils/pystac/pull/1171))

### Deprecated

- `pystac.summaries.FIELDS_JSON_URL` ([#1045](https://github.com/stac-utils/pystac/pull/1045))
- Catalog `get_item()`. Use `get_items(id)` instead ([#1075](https://github.com/stac-utils/pystac/pull/1075))
- Catalog and Collection `get_all_items`. Use `get_items(recursive=True)` instead ([#1075](https://github.com/stac-utils/pystac/pull/1075))

## [v1.7.3]

### Fixed

- Duplicate `self` links in Items ([#1103](https://github.com/stac-utils/pystac/pull/1103))

## [v1.7.2]

### Fixed

- Projection extension v1.0.0 support ([#1081](https://github.com/stac-utils/pystac/pull/1081))

## [v1.7.1]

### Changed

- Use [ruff](https://github.com/charliermarsh/ruff) instead of **isort** and **flake8** ([#1034](https://github.com/stac-utils/pystac/pull/1034))
- Update links in doc notebooks to not point to specific versions ([#1039](https://github.com/stac-utils/pystac/pull/1039))

### Fixed

- Item `__geo_interface__` now correctly returns a Feature, rather than only the Geometry ([#1049](https://github.com/stac-utils/pystac/pull/1049))

## [v1.7.0]

### Added

- Additional util methods `now_in_utc` and `now_to_rfc3339_str` ([#760](https://github.com/stac-utils/pystac/pull/760))
- `media_type` and `role` filtering to Item and Collection `get_assets()` method ([#936](https://github.com/stac-utils/pystac/pull/936))
- `Asset.has_role` ([#936](https://github.com/stac-utils/pystac/pull/936))
- Enum MediaType entry for flatgeobuf ([discussion](https://github.com/flatgeobuf/flatgeobuf/discussions/112#discussioncomment-4606721)) ([#938](https://github.com/stac-utils/pystac/pull/938))
- Custom `header` support to `DefaultStacIO` ([#889](https://github.com/stac-utils/pystac/pull/889))
- Python 3.11 checks in CI ([#908](https://github.com/stac-utils/pystac/pull/908))
- Ability to only update resolved links when using `Catalog.normalize_hrefs` and `Catalog.normalize_and_save`, via a new `skip_unresolved` argument ([#900](https://github.com/stac-utils/pystac/pull/900))
- Optional argument `timespec` to `utils.datetime_to_str` ([#929](https://github.com/stac-utils/pystac/pull/929))
- `isort` ([#961](https://github.com/stac-utils/pystac/pull/961))
- `AsIsLayoutStrategy` ([#919](https://github.com/stac-utils/pystac/pull/919))
- `__geo_interface__` for items ([#885](https://github.com/stac-utils/pystac/pull/885))
- Optional `strategy` parameter to `catalog.add_items()` ([#967](https://github.com/stac-utils/pystac/pull/967))
- `start_datetime` and `end_datetime` arguments to the `Item` constructor ([#918](https://github.com/stac-utils/pystac/pull/918))
- `RetryStacIO` ([#986](https://github.com/stac-utils/pystac/pull/986))
- `STACObject.remove_hierarchical_links` and `Link.is_hierarchical` ([#999](https://github.com/stac-utils/pystac/pull/999))
- `extra_fields` to `AssetDefinition` in the item assets extension ([#1003](https://github.com/stac-utils/pystac/pull/1003))
- `Catalog.fully_resolve` ([#1001](https://github.com/stac-utils/pystac/pull/1001))
- A `DeprecatedWarning` when deserializing an Item or Collection to a STAC object via the `from_dict()` method ([1006](https://github.com/stac-utils/pystac/pull/1006))
- Support for relative stac extension paths via `make_absolute_href` ([#884](https://github.com/stac-utils/pystac/pull/884))

### Changed

- Projection extension updated to use v1.1.0 ([#989](https://github.com/stac-utils/pystac/pull/989)).
- Update Grid Extension support to v1.1.0 and fix issue with grid:code prefix validation ([#925](https://github.com/stac-utils/pystac/pull/925))
- Switch to pytest ([#939](https://github.com/stac-utils/pystac/pull/939))
- Use `from __future__ import annotations` for type signatures ([#962](https://github.com/stac-utils/pystac/pull/962))
- Use `TypeVar` for alternate constructors ([#983](https://github.com/stac-utils/pystac/pull/983))
- Behavior when required fields are missing in `Item.from_dict` ([#994](https://github.com/stac-utils/pystac/pull/994))
- By default, `ItemCollection` now clones items in iterator (`clone_items=True`) ([#1016](https://github.com/stac-utils/pystac/pull/1016))

### Deprecated

- `TemplateError` in `layout.py` deprecated in favor of duplicate in `errors.py` ([#1018](https://github.com/stac-utils/pystac/pull/1018))

### Fixed

- Creating dictionaries from Catalogs and Collections without root hrefs now creates valid STAC ([#896](https://github.com/stac-utils/pystac/pull/896))
- Dependency resolution when installing `requirements-dev.txt` ([#897](https://github.com/stac-utils/pystac/pull/897))
- Serializing optional Collection attributes ([#916](https://github.com/stac-utils/pystac/pull/916))
- A couple non-running tests ([#912](https://github.com/stac-utils/pystac/pull/912))
- Filtering on `media_type` in `get_links()` and `get_single_link()` ([#966](https://github.com/stac-utils/pystac/pull/966))
- Missing hrefs and duplicate Item fields in html generated by `_repr_html_()` ([#975](https://github.com/stac-utils/pystac/pull/975))
- Allow subclasses in a few more `clone` methods ([#983](https://github.com/stac-utils/pystac/pull/983))
- Pass `href` from `Item.from_dict` to constructor ([#984](https://github.com/stac-utils/pystac/pull/984))
- Serializing the table extension ([#992](https://github.com/stac-utils/pystac/pull/992))

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
- Allow comparable types with alternate parameter naming of **lt** method to pass structural type linting for RangeSummary ([#562](https://github.com/stac-utils/pystac/pull/562))

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
- Fixed issue that caused geometries and bboxes produced by Shapely to fail PySTAC's validator ([#201](https://github.com/stac-utils/pystac/pull/201))
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
- the eo and label extensions changed from being a subclass of Item to wrapping items. **Note**: This is a major change in the API for dealing with extensions. See the note below for more information.
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
- Fixed catalog and collection clone logic to avoid duplication of root link [#72](https://github.com/azavea/pystac/pull/72)

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

[Unreleased]: <https://github.com/stac-utils/pystac/compare/v1.13.0..main>
[v1.13.0]: <https://github.com/stac-utils/pystac/compare/v1.12.2..v1.13.0>
[v1.12.2]: <https://github.com/stac-utils/pystac/compare/v1.12.1..v1.12.2>
[v1.12.1]: <https://github.com/stac-utils/pystac/compare/v1.12.0..v1.12.1>
[v1.12.0]: <https://github.com/stac-utils/pystac/compare/v1.11.0..v1.12.0>
[v1.11.0]: <https://github.com/stac-utils/pystac/compare/v1.10.1..v1.11.0>
[v1.10.1]: <https://github.com/stac-utils/pystac/compare/v1.10.0..v1.10.1>
[v1.10.0]: <https://github.com/stac-utils/pystac/compare/v1.9.0..v1.10.0>
[v1.9.0]: <https://github.com/stac-utils/pystac/compare/v1.8.4..v1.9.0>
[v1.8.4]: <https://github.com/stac-utils/pystac/compare/v1.8.3..v1.8.4>
[v1.8.3]: <https://github.com/stac-utils/pystac/compare/v1.8.2..v1.8.3>
[v1.8.2]: <https://github.com/stac-utils/pystac/compare/v1.8.1..v1.8.2>
[v1.8.1]: <https://github.com/stac-utils/pystac/compare/v1.8.0..v1.8.1>
[v1.8.0]: <https://github.com/stac-utils/pystac/compare/v1.7.3..v1.8.0>
[v1.7.3]: <https://github.com/stac-utils/pystac/compare/v1.7.2..v1.7.3>
[v1.7.2]: <https://github.com/stac-utils/pystac/compare/v1.7.1..v1.7.2>
[v1.7.1]: <https://github.com/stac-utils/pystac/compare/v1.7.0..v1.7.1>
[v1.7.0]: <https://github.com/stac-utils/pystac/compare/v1.6.1..v1.7.0>
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

<!-- markdownlint-disable-file MD024 -->
