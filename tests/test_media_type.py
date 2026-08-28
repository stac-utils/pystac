"""Tests for :class:`pystac.MediaType`."""

import pystac


def test_media_type_values() -> None:
    # Not geospatial-specific, but common enough in STAC metadata to belong
    # here: https://github.com/stac-utils/pystac/issues/1555
    assert pystac.MediaType.OCTET_STREAM == "application/octet-stream"
    assert pystac.MediaType.ZIP == "application/zip"


def test_media_type_is_a_str() -> None:
    asset = pystac.Asset(href="data.zip", media_type=pystac.MediaType.ZIP)
    assert asset.to_dict()["type"] == "application/zip"
