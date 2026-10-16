from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Band:
    """A name and some properties that apply to a band (aka subasset)."""

    name: str | None = None
    """The name of the band (e.g., "B01", "B8", "band2", "red").

    This should be unique across all bands defined in the list of bands. This is
    typically the name the data provider uses for the band.
    """

    description: str | None = None
    """Description to fully explain the band.

    CommonMark 0.29 syntax MAY be used for rich text representation.
    """

    extra_fields: dict[str, Any] = field(default_factory=dict)
    """Other fields on the band."""

    def __repr__(self) -> str:
        return f"Band(name={self.name!r})"

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Band:
        """Creates a new band object from a dictionary. Does not modify ``d``."""
        d = deepcopy(d)
        name = d.pop("name", None)
        description = d.pop("description", None)
        return cls(name=name, description=description, extra_fields=d)

    def to_dict(self) -> dict[str, Any]:
        """Creates a dictionary from this band object."""
        d: dict[str, Any] = {}
        if self.name is not None:
            d["name"] = self.name
        if self.description is not None:
            d["description"] = self.description
        d.update(deepcopy(self.extra_fields))
        return d


def _read_bands(d: dict[str, Any]) -> list[Band] | None:
    bands = d.get("bands")
    if bands is None:
        return None
    return [Band.from_dict(band) for band in bands]


def _write_bands(d: dict[str, Any], bands: list[Band] | None) -> None:
    if bands is None:
        d.pop("bands", None)
    else:
        d["bands"] = [band.to_dict() for band in bands]
