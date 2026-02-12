from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar, cast

from pystac import (
    Asset,
    Catalog,
    Collection,
    Item,
    ItemAssetDefinition,
    Link,
    STACError,
)

if TYPE_CHECKING:
    from pystac.extensions.classification import ClassificationExtension
    from pystac.extensions.datacube import DatacubeExtension
    from pystac.extensions.eo import EOExtension
    from pystac.extensions.file import FileExtension
    from pystac.extensions.grid import GridExtension
    from pystac.extensions.mgrs import MgrsExtension
    from pystac.extensions.mlm import (
        AssetDetailedMLMExtension,
        AssetGeneralMLMExtension,
        MLMExtension,
    )
    from pystac.extensions.pointcloud import PointcloudExtension
    from pystac.extensions.projection import ProjectionExtension
    from pystac.extensions.raster import RasterExtension
    from pystac.extensions.render import Render, RenderExtension
    from pystac.extensions.sar import SarExtension
    from pystac.extensions.sat import SatExtension
    from pystac.extensions.scientific import ScientificExtension
    from pystac.extensions.storage import StorageExtension
    from pystac.extensions.table import TableExtension
    from pystac.extensions.timestamps import TimestampsExtension
    from pystac.extensions.version import BaseVersionExtension, VersionExtension
    from pystac.extensions.view import ViewExtension
    from pystac.extensions.xarray_assets import XarrayAssetsExtension

#: Generalized version of :class:`~pystac.Asset`,
#: :class:`~pystac.ItemAssetDefinition`, or :class:`~pystac.Link`
T = TypeVar("T", Asset, ItemAssetDefinition, Link)
#: Generalized version of :class:`~pystac.Asset` or
#: :class:`~pystac.ItemAssetDefinition`
U = TypeVar("U", Asset, ItemAssetDefinition)

EXTENSION_NAMES = Literal[
    "classification",
    "cube",
    "eo",
    "file",
    "grid",
    "item_assets",
    "mgrs",
    "mlm",
    "pc",
    "proj",
    "raster",
    "render",
    "sar",
    "sat",
    "sci",
    "storage",
    "table",
    "timestamps",
    "version",
    "view",
    "xarray",
]

_EXTENSION_CLASSES = [
    ("pystac.extensions.classification", "ClassificationExtension"),
    ("pystac.extensions.datacube", "DatacubeExtension"),
    ("pystac.extensions.eo", "EOExtension"),
    ("pystac.extensions.file", "FileExtension"),
    ("pystac.extensions.grid", "GridExtension"),
    ("pystac.extensions.item_assets", "ItemAssetsExtension"),
    ("pystac.extensions.mgrs", "MgrsExtension"),
    ("pystac.extensions.mlm", "MLMExtension"),
    ("pystac.extensions.pointcloud", "PointcloudExtension"),
    ("pystac.extensions.projection", "ProjectionExtension"),
    ("pystac.extensions.raster", "RasterExtension"),
    ("pystac.extensions.render", "RenderExtension"),
    ("pystac.extensions.sar", "SarExtension"),
    ("pystac.extensions.sat", "SatExtension"),
    ("pystac.extensions.scientific", "ScientificExtension"),
    ("pystac.extensions.storage", "StorageExtension"),
    ("pystac.extensions.table", "TableExtension"),
    ("pystac.extensions.timestamps", "TimestampsExtension"),
    ("pystac.extensions.version", "VersionExtension"),
    ("pystac.extensions.view", "ViewExtension"),
    ("pystac.extensions.xarray_assets", "XarrayAssetsExtension"),
]

EXTENSION_NAME_MAPPING: dict[str, Any] = {}
for _mod_name, _cls_name in _EXTENSION_CLASSES:
    try:
        _mod = importlib.import_module(_mod_name)
        _cls = getattr(_mod, _cls_name)
        EXTENSION_NAME_MAPPING[_cls.name] = _cls
    except ImportError:
        pass
del _EXTENSION_CLASSES


def _get_class_by_name(name: str) -> Any:
    try:
        return EXTENSION_NAME_MAPPING[cast(EXTENSION_NAMES, name)]
    except KeyError as e:
        raise KeyError(
            f"Extension '{name}' is not a valid extension. "
            f"Options are {list(EXTENSION_NAME_MAPPING)}"
        ) from e


@dataclass
class CatalogExt:
    """Supporting the :attr:`~pystac.Catalog.ext` accessor for interacting
    with extension classes
    """

    stac_object: Catalog

    def has(self, name: EXTENSION_NAMES) -> bool:
        """Whether the given extension is enabled on this STAC object

        Args:
            name : Extension identifier (eg: 'eo')

        Returns:
            bool: ``True`` if extension is enabled, otherwise ``False``
        """
        return cast(bool, _get_class_by_name(name).has_extension(self.stac_object))

    def add(self, name: EXTENSION_NAMES) -> None:
        """Add the given extension to this STAC object

        Args:
            name : Extension identifier (eg: 'eo')
        """
        _get_class_by_name(name).add_to(self.stac_object)

    def remove(self, name: EXTENSION_NAMES) -> None:
        """Remove the given extension from this STAC object

        Args:
            name : Extension identifier (eg: 'eo')
        """
        _get_class_by_name(name).remove_from(self.stac_object)

    @property
    def version(self) -> VersionExtension[Catalog]:
        from pystac.extensions.version import VersionExtension

        return VersionExtension.ext(self.stac_object)


@dataclass
class CollectionExt(CatalogExt):
    """Supporting the :attr:`~pystac.Collection.ext` accessor for interacting
    with extension classes
    """

    stac_object: Collection

    @property
    def cube(self) -> DatacubeExtension[Collection]:
        from pystac.extensions.datacube import DatacubeExtension

        return DatacubeExtension.ext(self.stac_object)

    @property
    def item_assets(self) -> dict[str, ItemAssetDefinition]:
        from pystac.extensions.item_assets import ItemAssetsExtension

        return ItemAssetsExtension.ext(self.stac_object).item_assets

    @property
    def mlm(self) -> MLMExtension[Collection]:
        from pystac.extensions.mlm import MLMExtension

        return MLMExtension.ext(self.stac_object)

    @property
    def render(self) -> dict[str, Render]:
        from pystac.extensions.render import RenderExtension

        return RenderExtension.ext(self.stac_object).renders

    @property
    def sci(self) -> ScientificExtension[Collection]:
        from pystac.extensions.scientific import ScientificExtension

        return ScientificExtension.ext(self.stac_object)

    @property
    def table(self) -> TableExtension[Collection]:
        from pystac.extensions.table import TableExtension

        return TableExtension.ext(self.stac_object)

    @property
    def xarray(self) -> XarrayAssetsExtension[Collection]:
        from pystac.extensions.xarray_assets import XarrayAssetsExtension

        return XarrayAssetsExtension.ext(self.stac_object)


@dataclass
class ItemExt:
    """Supporting the :attr:`~pystac.Item.ext` accessor for interacting
    with extension classes
    """

    stac_object: Item

    def has(self, name: EXTENSION_NAMES) -> bool:
        """Whether the given extension is enabled on this STAC object

        Args:
            name : Extension identifier (eg: 'eo')

        Returns:
            bool: ``True`` if extension is enabled, otherwise ``False``
        """
        return cast(bool, _get_class_by_name(name).has_extension(self.stac_object))

    def add(self, name: EXTENSION_NAMES) -> None:
        """Add the given extension to this STAC object

        Args:
            name : Extension identifier (eg: 'eo')
        """
        _get_class_by_name(name).add_to(self.stac_object)

    def remove(self, name: EXTENSION_NAMES) -> None:
        """Remove the given extension from this STAC object

        Args:
            name : Extension identifier (eg: 'eo')
        """
        _get_class_by_name(name).remove_from(self.stac_object)

    @property
    def classification(self) -> ClassificationExtension[Item]:
        from pystac.extensions.classification import ClassificationExtension

        return ClassificationExtension.ext(self.stac_object)

    @property
    def cube(self) -> DatacubeExtension[Item]:
        from pystac.extensions.datacube import DatacubeExtension

        return DatacubeExtension.ext(self.stac_object)

    @property
    def eo(self) -> EOExtension[Item]:
        from pystac.extensions.eo import EOExtension

        return EOExtension.ext(self.stac_object)

    @property
    def grid(self) -> GridExtension:
        from pystac.extensions.grid import GridExtension

        return GridExtension.ext(self.stac_object)

    @property
    def mgrs(self) -> MgrsExtension:
        from pystac.extensions.mgrs import MgrsExtension

        return MgrsExtension.ext(self.stac_object)

    @property
    def mlm(self) -> MLMExtension[Item]:
        from pystac.extensions.mlm import MLMExtension

        return MLMExtension.ext(self.stac_object)

    @property
    def pc(self) -> PointcloudExtension[Item]:
        from pystac.extensions.pointcloud import PointcloudExtension

        return PointcloudExtension.ext(self.stac_object)

    @property
    def proj(self) -> ProjectionExtension[Item]:
        from pystac.extensions.projection import ProjectionExtension

        return ProjectionExtension.ext(self.stac_object)

    @property
    def render(self) -> RenderExtension[Item]:
        from pystac.extensions.render import RenderExtension

        return RenderExtension.ext(self.stac_object)

    @property
    def sar(self) -> SarExtension[Item]:
        from pystac.extensions.sar import SarExtension

        return SarExtension.ext(self.stac_object)

    @property
    def sat(self) -> SatExtension[Item]:
        from pystac.extensions.sat import SatExtension

        return SatExtension.ext(self.stac_object)

    @property
    def sci(self) -> ScientificExtension[Item]:
        from pystac.extensions.scientific import ScientificExtension

        return ScientificExtension.ext(self.stac_object)

    @property
    def storage(self) -> StorageExtension[Item]:
        from pystac.extensions.storage import StorageExtension

        return StorageExtension.ext(self.stac_object)

    @property
    def table(self) -> TableExtension[Item]:
        from pystac.extensions.table import TableExtension

        return TableExtension.ext(self.stac_object)

    @property
    def timestamps(self) -> TimestampsExtension[Item]:
        from pystac.extensions.timestamps import TimestampsExtension

        return TimestampsExtension.ext(self.stac_object)

    @property
    def version(self) -> VersionExtension[Item]:
        from pystac.extensions.version import VersionExtension

        return VersionExtension.ext(self.stac_object)

    @property
    def view(self) -> ViewExtension[Item]:
        from pystac.extensions.view import ViewExtension

        return ViewExtension.ext(self.stac_object)

    @property
    def xarray(self) -> XarrayAssetsExtension[Item]:
        from pystac.extensions.xarray_assets import XarrayAssetsExtension

        return XarrayAssetsExtension.ext(self.stac_object)


class _AssetsExt(Generic[T]):
    stac_object: T

    def has(self, name: EXTENSION_NAMES) -> bool:
        """Whether the given extension is enabled on the owner

        Args:
            name : Extension identifier (eg: 'eo')

        Returns:
            bool: ``True`` if extension is enabled, otherwise ``False``
        """
        if self.stac_object.owner is None:
            raise STACError(
                f"Attempted to use `.ext.has('{name}') for an object with no owner. "
                "Use `.set_owner` and then try to check the extension again."
            )
        else:
            return cast(
                bool, _get_class_by_name(name).has_extension(self.stac_object.owner)
            )

    def add(self, name: EXTENSION_NAMES) -> None:
        """Add the given extension to the owner

        Args:
            name : Extension identifier (eg: 'eo')
        """
        if self.stac_object.owner is None:
            raise STACError(
                f"Attempted to add extension='{name}' for an object with no owner. "
                "Use `.set_owner` and then try to add the extension again."
            )
        else:
            _get_class_by_name(name).add_to(self.stac_object.owner)

    def remove(self, name: EXTENSION_NAMES) -> None:
        """Remove the given extension from the owner

        Args:
            name : Extension identifier (eg: 'eo')
        """
        if self.stac_object.owner is None:
            raise STACError(
                f"Attempted to remove extension='{name}' for an object with no owner. "
                "Use `.set_owner` and then try to remove the extension again."
            )
        else:
            _get_class_by_name(name).remove_from(self.stac_object.owner)


class _AssetExt(_AssetsExt[U]):
    stac_object: U

    @property
    def classification(self) -> ClassificationExtension[U]:
        from pystac.extensions.classification import ClassificationExtension

        return ClassificationExtension.ext(self.stac_object)

    @property
    def cube(self) -> DatacubeExtension[U]:
        from pystac.extensions.datacube import DatacubeExtension

        return DatacubeExtension.ext(self.stac_object)

    @property
    def eo(self) -> EOExtension[U]:
        from pystac.extensions.eo import EOExtension

        return EOExtension.ext(self.stac_object)

    @property
    def pc(self) -> PointcloudExtension[U]:
        from pystac.extensions.pointcloud import PointcloudExtension

        return PointcloudExtension.ext(self.stac_object)

    @property
    def proj(self) -> ProjectionExtension[U]:
        from pystac.extensions.projection import ProjectionExtension

        return ProjectionExtension.ext(self.stac_object)

    @property
    def raster(self) -> RasterExtension[U]:
        from pystac.extensions.raster import RasterExtension

        return RasterExtension.ext(self.stac_object)

    @property
    def sar(self) -> SarExtension[U]:
        from pystac.extensions.sar import SarExtension

        return SarExtension.ext(self.stac_object)

    @property
    def sat(self) -> SatExtension[U]:
        from pystac.extensions.sat import SatExtension

        return SatExtension.ext(self.stac_object)

    @property
    def storage(self) -> StorageExtension[U]:
        from pystac.extensions.storage import StorageExtension

        return StorageExtension.ext(self.stac_object)

    @property
    def table(self) -> TableExtension[U]:
        from pystac.extensions.table import TableExtension

        return TableExtension.ext(self.stac_object)

    @property
    def version(self) -> BaseVersionExtension[U]:
        from pystac.extensions.version import BaseVersionExtension

        return BaseVersionExtension.ext(self.stac_object)

    @property
    def view(self) -> ViewExtension[U]:
        from pystac.extensions.view import ViewExtension

        return ViewExtension.ext(self.stac_object)


@dataclass
class AssetExt(_AssetExt[Asset]):
    """Supporting the :attr:`~pystac.Asset.ext` accessor for interacting
    with extension classes
    """

    stac_object: Asset

    @property
    def file(self) -> FileExtension[Asset]:
        from pystac.extensions.file import FileExtension

        return FileExtension.ext(self.stac_object)

    @property
    def mlm(self) -> AssetGeneralMLMExtension[Asset] | AssetDetailedMLMExtension:
        from pystac.extensions.mlm import (
            AssetDetailedMLMExtension,
            AssetGeneralMLMExtension,
        )

        if "mlm:name" in self.stac_object.extra_fields:
            return AssetDetailedMLMExtension.ext(self.stac_object)
        else:
            return AssetGeneralMLMExtension.ext(self.stac_object)

    @property
    def timestamps(self) -> TimestampsExtension[Asset]:
        from pystac.extensions.timestamps import TimestampsExtension

        return TimestampsExtension.ext(self.stac_object)

    @property
    def xarray(self) -> XarrayAssetsExtension[Asset]:
        from pystac.extensions.xarray_assets import XarrayAssetsExtension

        return XarrayAssetsExtension.ext(self.stac_object)


@dataclass
class ItemAssetExt(_AssetExt[ItemAssetDefinition]):
    """Supporting the :attr:`~pystac.ItemAssetDefinition.ext` accessor for interacting
    with extension classes
    """

    stac_object: ItemAssetDefinition

    @property
    def mlm(self) -> MLMExtension[ItemAssetDefinition]:
        from pystac.extensions.mlm import MLMExtension

        return MLMExtension.ext(self.stac_object)


@dataclass
class LinkExt(_AssetsExt[Link]):
    """Supporting the :attr:`~pystac.Link.ext` accessor for interacting
    with extension classes
    """

    stac_object: Link

    @property
    def file(self) -> FileExtension[Link]:
        from pystac.extensions.file import FileExtension

        return FileExtension.ext(self.stac_object)
