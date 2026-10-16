from typing import Any

from pystac import Band


def test_from_dict_without_name() -> None:
    band = Band.from_dict({"description": "no name"})
    assert band.name is None
    assert band.description == "no name"


def test_from_dict_does_not_modify_input() -> None:
    d = {"name": "red", "description": "Red", "eo:common_name": "red"}
    Band.from_dict(d)
    assert d == {"name": "red", "description": "Red", "eo:common_name": "red"}


def test_from_dict_empty() -> None:
    band = Band.from_dict({})
    assert band == Band()
    assert band.to_dict() == {}


def test_to_dict_omits_unset_fields() -> None:
    assert Band(name="red").to_dict() == {"name": "red"}
    assert Band(description="Red").to_dict() == {"description": "Red"}


def test_roundtrip_with_extra_fields() -> None:
    d: dict[str, Any] = {
        "name": "B04",
        "description": "Red",
        "eo:center_wavelength": 0.665,
        "raster:scale": 0.0001,
    }
    band = Band.from_dict(d)
    assert band.extra_fields == {"eo:center_wavelength": 0.665, "raster:scale": 0.0001}
    assert band.to_dict() == d


def test_dicts_do_not_share_nested_values() -> None:
    d: dict[str, Any] = {"raster:histogram": {"buckets": [1, 2]}}
    band = Band.from_dict(d)
    d["raster:histogram"]["buckets"].append(3)
    band.to_dict()["raster:histogram"]["buckets"].append(4)
    assert band.extra_fields == {"raster:histogram": {"buckets": [1, 2]}}
