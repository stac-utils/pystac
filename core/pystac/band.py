from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pystac.extensions.ext import BandExt


class Band:
    """The Band object is used to describe an available band in a STAC entity or asset.
    This field describes the general construct of a band or layer, which doesn't
    necessarily need to be a spectral band. By adding fields from extensions you can
    indicate that a band, for example, is

    - a spectral band (EO extension),
    - a band with classification results (classification extension),
    - a band with quality information such as cloud cover probabilities,
    - etc...

    Bands evolved from their V1 counterpart where they can be now used as an array
    in combination with property inheritance to provide users with more flexibility.

    This object can exploit the properties from the `eo` and `raster` extensions.

    Bands can be a part of `pystac.Asset`, `pystac.ItemAsset` or `pystac.Summaries`.

    Args:
        name : The name of the band (e.g., "B01", "B8", "band2", "red"), which
            should be unique across all bands defined in the list of bands.
            This is typically the name the data provider uses for the band.
        description : Description to fully explain the band. CommonMark 0.29
            syntax MAY be used for rich text representation.
        extra_fields : Optional dictionary containing additional top-level fields
            defined on the Provider object.
    """

    name: str
    """The name of the band (e.g., "B01", "B8", "band2", "red"), which should be unique 
    across all bands defined in the list of bands. This is typically the name the data 
    provider uses for the band."""

    description: str | None
    """Description to fully explain the band. CommonMark 0.29 syntax MAY be used 
    for rich text representation."""

    extra_fields: dict[str, Any]
    """Dictionary containing additional top-level fields defined on the Band
    object. Optional, additional fields for this asset. This is used by extensions, 
    like `raster` or `eo`, as a way to serialize and deserialize properties on asset 
    object JSON."""

    def __init__(
        self,
        name: str,
        description: str | None = None,
        extra_fields: dict[str, Any] | None = None,
    ):
        self.name = name
        self.description = description
        self.extra_fields = extra_fields or {}

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Band):
            return NotImplemented
        return self.to_dict() == o.to_dict()

    def _repr_html_(self) -> str:
        from html import escape

        from pystac.html.jinja_env import get_jinja_env

        jinja_env = get_jinja_env()
        if jinja_env:
            template = jinja_env.get_template("JSON.jinja2")
            return str(template.render(dict=self.to_dict(), plain=escape(repr(self))))
        else:
            return escape(repr(self))

    def to_dict(self) -> dict[str, Any]:
        """Returns this band as a dictionary.

        Returns:
            dict: A serialization of the Band.
        """
        d: dict[str, Any] = {"name": self.name}
        if self.description is not None:
            d["description"] = self.description

        d.update(self.extra_fields)

        return d

    @staticmethod
    def from_dict(d: dict[str, Any]) -> Band:
        """Constructs a Band from a dict.

        Returns:
            Band: The Band deserialized from the JSON dict.
        """
        return Band(
            name=d["name"],
            description=d.get("description"),
            extra_fields={
                k: v for k, v in d.items() if k not in {"name", "description"}
            },
        )

    @property
    def ext(self) -> BandExt:
        """Accessor for extension classes on this asset

        Example::

            band.ext.eo.solar_illumination = 1823.24
        """
        from pystac.extensions.ext import BandExt

        return BandExt(stac_object=self)

    def __repr__(self) -> str:
        return f"<Band name={self.name}>"
