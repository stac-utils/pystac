from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, fields
from typing import Any

from pystac.common_metadata import DataType, NoDataStrings, Statistics


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

    data_type: DataType | str | None = None
    """The data type of the values in the band."""

    nodata: float | NoDataStrings | str | None = None
    """Value used to identify no-data."""

    statistics: Statistics | None = None
    """Statistics of all the values in the band."""

    unit: str | None = None
    """Unit of measurement of the values in the band, preferably compliant to
    `UCUM <https://ucum.org/ucum.html>`__ or
    `UDUNITS-2 <https://docs.unidata.ucar.edu/udunits/current/>`__."""

    extra_fields: dict[str, Any] = field(default_factory=dict)
    """Other fields on the band."""

    def __repr__(self) -> str:
        return f"Band(name={self.name!r})"

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Band:
        """Creates a new band object from a dictionary. Does not modify ``d``.

        ``data_type`` and string ``nodata`` values are converted to
        :class:`~pystac.common_metadata.DataType` and
        :class:`~pystac.common_metadata.NoDataStrings` when they match a known
        value, and kept as plain strings otherwise.
        """
        d = deepcopy(d)
        statistics = d.pop("statistics", None)
        return cls(
            name=d.pop("name", None),
            description=d.pop("description", None),
            data_type=DataType.coerce(d.pop("data_type", None)),
            nodata=NoDataStrings.coerce(d.pop("nodata", None)),
            statistics=None if statistics is None else Statistics.from_dict(statistics),
            unit=d.pop("unit", None),
            extra_fields=d,
        )

    def to_dict(self) -> dict[str, Any]:
        """Creates a dictionary from this band object."""
        d: dict[str, Any] = {}
        if self.name is not None:
            d["name"] = self.name
        if self.description is not None:
            d["description"] = self.description
        if self.data_type is not None:
            d["data_type"] = self.data_type
        if self.nodata is not None:
            d["nodata"] = self.nodata
        if self.statistics is not None:
            d["statistics"] = self.statistics.to_dict()
        if self.unit is not None:
            d["unit"] = self.unit
        d.update(deepcopy(self.extra_fields))
        return d


def _write_bands(d: dict[str, Any], bands: list[Band] | None) -> None:
    if bands is None:
        d.pop("bands", None)
    else:
        d["bands"] = [band.to_dict() for band in bands]


class _BandCache:
    """The :class:`Band` objects of the ``bands`` list in a dict.

    The dict is the source of truth. The bands are read again when ``bands`` in the
    dict was replaced or changed, and are only written back by :meth:`sync` when the
    bands themselves were changed. Existing band objects are updated in place as
    long as the number of bands stays the same.
    """

    def __init__(self) -> None:
        self._remember(None, None)

    def get(self, d: dict[str, Any]) -> list[Band] | None:
        raw = d.get("bands")
        if raw is not self._raw or raw != self._raw_copy:
            self._remember(raw, self._read(raw))
        return self._bands

    def set(self, d: dict[str, Any], bands: list[Band] | None) -> None:
        _write_bands(d, bands)
        self._remember(d.get("bands"), bands)

    def sync(self, d: dict[str, Any]) -> None:
        if self._bands is None or self._bands == self._bands_copy:
            return
        raw = d.get("bands")
        if raw is self._raw and raw == self._raw_copy:
            self.set(d, self._bands)

    def _read(self, raw: list[dict[str, Any]] | None) -> list[Band] | None:
        if raw is None:
            return None
        bands = [Band.from_dict(band) for band in raw]
        if self._bands is None or len(self._bands) != len(bands):
            return bands
        for band, new in zip(self._bands, bands):
            for f in fields(new):
                if f.name != "extra_fields":
                    setattr(band, f.name, getattr(new, f.name))
            band.extra_fields.clear()
            band.extra_fields.update(new.extra_fields)
        return self._bands

    def _remember(self, raw: Any, bands: list[Band] | None) -> None:
        self._raw = raw
        self._raw_copy = deepcopy(raw)
        self._bands = bands
        self._bands_copy = deepcopy(bands)
