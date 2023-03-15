# Releasing

This is a checklist to use when releasing a new PySTAC version.

1. Determine the next version. We do not currently have a versioning guide, but <https://github.com/radiantearth/stac-spec/discussions/1184> has some discussion around the topic.
2. Create a release branch with the name `release/vX.Y.Z`, where `X.Y.Z` is the next version (e.g. `1.7.0`).
3. Pull fields-normalized.json from cdn: run `scripts/pull-static`. Note you will need to have [jq](https://stedolan.github.io/jq/) installed.
4. Update the `__version__` attribute in `pystac/version.py` with the new version.
5. Update the CHANGELOG.
    - Create a new header below `## [Unreleased]` with the new version.
    - Remove any unused header sections.
    - Update the links at the bottom of the page for the new header.
    - Audit the CHANGELOG for correctness and readability.
6. Audit the changes.
   Use the CHANGELOG, your favorite diff tool, and the merged Github pull requests to ensure that:
    - All notable changes are captured in the CHANGELOG.
    - The type of release is appropriate for the new version number, i.e. if there are breaking changes, the MAJOR version number must be increased.
    - All deprecated items that were marked for removal in this version are removed.
7. Craft draft release notes (<https://github.com/stac-utils/pystac/releases/new>).
   These should be short, readable, and call out any significant changes, especially changes in default behavior or significant new features.
   These should also include a link back to the Github milestone for this release, if there is one.
   These should _not_ be a complete listing of changes -- those will be auto-generated later, after the tag is pushed.
8. Commit your changes, push your branch to Github, and request a review.
9. Once approved, merge the PR.
10. Once the PR is merged, create a tag with the version name, e.g. `vX.Y.Z`.
   Prefer a signed tag, if possible.
   Push the tag to Github.
11. Use the tag to finish your release notes, and publish those.
    The "auto generate" feature is your friend, here.
    When the release is published, this will trigger the build and release on PyPI.
12. Announced the release in [Gitter](https://matrix.to/#/#SpatioTemporal-Asset-Catalog_python:gitter.im) and on any relevant social media.
