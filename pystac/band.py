from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Band:
    """A name and some properties that apply to a band (aka subasset)."""

    name: str
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
        """Creates a new band object from a dictionary."""
        try:
            name = d.pop("name")
        except KeyError:
            raise ValueError("missing required field on band: name")
        description = d.pop("description", None)
        return Band(name=name, description=description, extra_fields=d)

    def to_dict(self) -> dict[str, Any]:
        """Creates a dictionary from this band object."""
        d = {
            "name": self.name,
        }
        if self.description is not None:
            d["description"] = self.description
        d.update(self.extra_fields)
        return d
