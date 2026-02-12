"""Implements the :stac-ext:`Render Extension <render>`."""

from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar

import pystac
from pystac.extensions.base import ExtensionManagementMixin, PropertiesExtension
from pystac.extensions.hooks import ExtensionHooks
from pystac.utils import get_required, map_opt

#: Generalized version of :class:`~pystac.Collection` or :class:`~pystac.Item`
T = TypeVar("T", pystac.Collection, pystac.Item)

SCHEMA_URI_PATTERN: str = (
    "https://stac-extensions.github.io/render/v{version}/schema.json"
)
DEFAULT_VERSION: str = "2.0.0"

SUPPORTED_VERSIONS = [DEFAULT_VERSION]

RENDERS_PROP = "renders"


class Render:
    """Parameters for creating a rendered view of assets."""

    properties: dict[str, Any]

    def __init__(self, properties: dict[str, Any]) -> None:
        self.properties = properties

    @property
    def assets(self) -> list[str]:
        """
        List of asset keys referencing the assets that are
        used to make the rendering.
        """
        return get_required(self.properties.get("assets"), self, "assets")

    @assets.setter
    def assets(self, v: list[str]) -> None:
        self.properties["assets"] = v

    @property
    def title(self) -> str | None:
        """Title of the rendering"""
        return self.properties.get("title")

    @title.setter
    def title(self, v: str | None) -> None:
        if v is not None:
            self.properties["title"] = v
        else:
            self.properties.pop("title", None)

    @property
    def rescale(self) -> list[list[float]] | None:
        """A list of min/max value pairs to rescale each asset by, e.g.
        ``[[0, 5000], [0, 7000], [0, 9000]]``. If not provided, the
        assets will not be rescaled.
        """
        return self.properties.get("rescale")

    @rescale.setter
    def rescale(self, v: list[list[float]] | None) -> None:
        if v is not None:
            self.properties["rescale"] = v
        else:
            self.properties.pop("rescale", None)

    @property
    def nodata(self) -> float | str | None:
        """Nodata value."""
        return self.properties.get("nodata")

    @nodata.setter
    def nodata(self, v: float | str | None) -> None:
        if v is not None:
            self.properties["nodata"] = v
        else:
            self.properties.pop("nodata", None)

    @property
    def colormap_name(self) -> str | None:
        """Name of color map to apply to the render.
        See: https://matplotlib.org/stable/gallery/color/colormap_reference.html
        """
        return self.properties.get("colormap_name")

    @colormap_name.setter
    def colormap_name(self, v: str | None) -> None:
        if v is not None:
            self.properties["colormap_name"] = v
        else:
            self.properties.pop("colormap_name", None)

    @property
    def colormap(self) -> dict[str, Any] | None:
        """A dictionary containing a custom colormap definition.
        See: https://developmentseed.org/titiler/advanced/rendering/#custom-colormaps
        """
        return self.properties.get("colormap")

    @colormap.setter
    def colormap(self, v: dict[str, Any] | None) -> None:
        if v is not None:
            self.properties["colormap"] = v
        else:
            self.properties.pop("colormap", None)

    @property
    def color_formula(self) -> str | None:
        """A string containing a color formula to apply
        color corrections to images. Useful for reducing
        artefacts like atmospheric haze, dark shadows, or
        muted colors.
        See: https://developmentseed.org/titiler/advanced/rendering/#color-formula
        """
        return self.properties.get("color_formula")

    @color_formula.setter
    def color_formula(self, v: str | None) -> None:
        if v is not None:
            self.properties["color_formula"] = v
        else:
            self.properties.pop("color_formula", None)

    @property
    def resampling(self) -> str | None:
        """Resampling algorithm to apply to the referenced assets. See GDAL
        resampling algorithm for some examples.
        See: https://gdal.org/en/latest/programs/gdalwarp.html#cmdoption-gdalwarp-r
        """
        return self.properties.get("resampling")

    @resampling.setter
    def resampling(self, v: str | None) -> None:
        if v is not None:
            self.properties["resampling"] = v
        else:
            self.properties.pop("resampling", None)

    @property
    def expression(self) -> str | None:
        """Band arithmetic formula to apply to the referenced assets."""
        return self.properties.get("expression")

    @expression.setter
    def expression(self, v: str | None) -> None:
        if v is not None:
            self.properties["expression"] = v
        else:
            self.properties.pop("expression", None)

    @property
    def minmax_zoom(self) -> list[int] | None:
        """Zoom level range applicable for the visualization, e.g. ``[2, 18]``."""
        return self.properties.get("minmax_zoom")

    @minmax_zoom.setter
    def minmax_zoom(self, v: list[int] | None) -> None:
        if v is not None:
            self.properties["minmax_zoom"] = v
        else:
            self.properties.pop("minmax_zoom", None)

    def apply(
        self,
        assets: list[str],
        title: str | None = None,
        rescale: list[list[float]] | None = None,
        nodata: float | str | None = None,
        colormap_name: str | None = None,
        colormap: dict[str, Any] | None = None,
        color_formula: str | None = None,
        resampling: str | None = None,
        expression: str | None = None,
        minmax_zoom: list[int] | None = None,
    ) -> None:
        """Set the properties for a new Render.

        Args:
            assets : List of asset keys referencing the assets that are
                used to make the rendering.
            title : Title of the rendering.
            rescale : A list of min/max value pairs to rescale each asset by, e.g.
                ``[[0, 5000], [0, 7000], [0, 9000]]``. If not provided, the
                assets will not be rescaled.
            nodata : Nodata value.
            colormap_name : Name of color map to apply to the render.
                https://matplotlib.org/stable/gallery/color/colormap_reference.html
            colormap : A dictionary containing a custom colormap definition.
                https://developmentseed.org/titiler/advanced/rendering/#custom-colormaps
            color_formula : A string containing a color formula to apply
                color corrections to images. Useful for reducing
                artifacts like atmospheric haze, dark shadows, or
                muted colors.
                https://developmentseed.org/titiler/advanced/rendering/#color-formula
            resampling : Resampling algorithm to apply to the referenced assets. See
                GDAL resampling algorithm for some examples.
                https://gdal.org/en/latest/programs/gdalwarp.html#cmdoption-gdalwarp-r
            expression : Band arithmetic formula to apply to the referenced assets.
            minmax_zoom : Zoom level range applicable for the visualization,
                e.g. ``[2, 18]``.
        """
        self.assets = assets
        self.title = title
        self.rescale = rescale
        self.nodata = nodata
        self.colormap_name = colormap_name
        self.colormap = colormap
        self.color_formula = color_formula
        self.resampling = resampling
        self.expression = expression
        self.minmax_zoom = minmax_zoom

    @classmethod
    def create(
        cls,
        assets: list[str],
        title: str | None = None,
        rescale: list[list[float]] | None = None,
        nodata: float | str | None = None,
        colormap_name: str | None = None,
        colormap: dict[str, Any] | None = None,
        color_formula: str | None = None,
        resampling: str | None = None,
        expression: str | None = None,
        minmax_zoom: list[int] | None = None,
    ) -> Render:
        """Create a new Render.

        Args:
            assets: List of asset keys referencing the assets that are
                used to make the rendering.
            title: Title of the rendering.
            rescale: A list of min/max value pairs to rescale each asset by, e.g.
                ``[[0, 5000], [0, 7000], [0, 9000]]``. If not provided, the
                assets will not be rescaled.
            nodata: Nodata value.
            colormap_name: Name of color map to apply to the render.
                https://matplotlib.org/stable/gallery/color/colormap_reference.html
            colormap: A dictionary containing a custom colormap definition.
                https://developmentseed.org/titiler/advanced/rendering/#custom-colormaps
            color_formula: A string containing a color formula to apply
                color corrections to images. Useful for reducing
                artifacts like atmospheric haze, dark shadows, or
                muted colors.
                https://developmentseed.org/titiler/advanced/rendering/#color-formula
            resampling: Resampling algorithm to apply to the referenced assets. See
                GDAL resampling algorithm for some examples.
                https://gdal.org/en/latest/programs/gdalwarp.html#cmdoption-gdalwarp-r
            expression: Band arithmetic formula to apply to the referenced assets.
            minmax_zoom: Zoom level range applicable for the visualization,
                e.g. ``[2, 18]``.
        """
        c = cls({})
        c.apply(
            assets=assets,
            title=title,
            rescale=rescale,
            nodata=nodata,
            colormap_name=colormap_name,
            colormap=colormap,
            color_formula=color_formula,
            resampling=resampling,
            expression=expression,
            minmax_zoom=minmax_zoom,
        )
        return c

    def to_dict(self) -> dict[str, Any]:
        return self.properties

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Render):
            raise NotImplementedError
        return self.properties == other.properties

    def __repr__(self) -> str:
        props = " ".join(
            [
                f"{key}={value}"
                for key, value in self.properties.items()
                if value is not None
            ]
        )
        return f"<Render {props}>"


class RenderExtension(
    Generic[T],
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection],
):
    """An abstract class that can be used to extend the properties of a
    :class:`~pystac.Collection` or :class:`~pystac.Item` with
    properties from the :stac-ext:`Render Extension <render>`. This class is
    generic over the type of STAC Object to be extended (e.g. :class:`~pystac.Item`,
    :class:`~pystac.Collection`).

    To create a concrete instance of :class:`RenderExtension`, use the
    :meth:`RenderExtension.ext` method. For example:

    .. code-block:: python

        >>> item: pystac.Item = ...
        >>> xr_ext = RenderExtension.ext(item)

    """

    name: Literal["render"] = "render"

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI_PATTERN.format(version=DEFAULT_VERSION)

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> RenderExtension[T]:
        """Extend the given STAC Object with properties from the
        :stac-ext:`Render Extension <render>`.

        This extension can be applied to instances of :class:`~pystac.Collection`
        or :class:`~pystac.Item`.

        Raises:
            pystac.ExtensionTypeError : If an invalid object type is passed.
        """
        if isinstance(obj, pystac.Collection):
            cls.ensure_has_extension(obj, add_if_missing)
            return CollectionRenderExtension(obj)
        elif isinstance(obj, pystac.Item):
            cls.ensure_has_extension(obj, add_if_missing)
            return ItemRenderExtension(obj)
        else:
            raise pystac.ExtensionTypeError(
                f"RenderExtension does not apply to type '{type(obj).__name__}'"
            )

    def apply(
        self,
        renders: dict[str, Render],
    ) -> None:
        """Applies the render extension fields to the extended
        object.

        Args:
            renders: a dictionary mapping render names to
                :class: `~pystac.extensions.render.Render` objects.
        """
        self.renders = renders

    @property
    def renders(self) -> dict[str, Render]:
        """A dictionary where each key is the name of a render and each
        value is a :class:`~Render` object.
        """
        renders: dict[str, dict[str, Any]] = get_required(
            self._get_property(RENDERS_PROP, dict[str, dict[str, Any]]),
            self,
            RENDERS_PROP,
        )
        return {k: Render(v) for k, v in renders.items()}

    @renders.setter
    def renders(self, v: dict[str, Render]) -> None:
        self._set_property(
            RENDERS_PROP,
            map_opt(lambda renders: {k: r.to_dict() for k, r in renders.items()}, v),
            pop_if_none=False,
        )


class CollectionRenderExtension(RenderExtension[pystac.Collection]):
    """A concrete implementation of :class:`RenderExtension` on a
    :class:`~pystac.Collection` that extends the properties of the Collection to include
    properties defined in the :stac-ext:`Render Extension <render>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`RenderExtension.ext` on an :class:`~pystac.Collection` to extend it.
    """

    def __init__(self, collection: pystac.Collection):
        self.collection = collection
        self.properties = collection.extra_fields

    def __repr__(self) -> str:
        return f"<CollectionRenderExtension Collection id={self.collection.id}>"


class ItemRenderExtension(RenderExtension[pystac.Item]):
    """A concrete implementation of :class:`RenderExtension` on a
    :class:`~pystac.Item` that extends the properties of the Item to include
    properties defined in the :stac-ext:`Render Extension <render>`.

    This class should generally not be instantiated directly. Instead, call
    :meth:`RenderExtension.ext` on an :class:`~pystac.Item` to extend it.
    """

    def __init__(self, item: pystac.Item):
        self.item = item
        self.properties = item.properties

    def __repr__(self) -> str:
        return f"<ItemRenderExtension Item id={self.item.id}>"


class RenderExtensionHooks(ExtensionHooks):
    schema_uri: str = SCHEMA_URI_PATTERN.format(version=DEFAULT_VERSION)
    stac_object_types = {pystac.STACObjectType.COLLECTION, pystac.STACObjectType.ITEM}
