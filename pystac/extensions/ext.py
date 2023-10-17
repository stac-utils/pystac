from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeVar, cast

from pystac import Asset, Catalog, Collection, Item, Link, STACError
from pystac.extensions.classification import ClassificationExtension
from pystac.extensions.datacube import DatacubeExtension
from pystac.extensions.eo import EOExtension
from pystac.extensions.file import FileExtension
from pystac.extensions.grid import GridExtension
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.mgrs import MgrsExtension
from pystac.extensions.pointcloud import PointcloudExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.raster import RasterExtension
from pystac.extensions.sar import SarExtension
from pystac.extensions.sat import SatExtension
from pystac.extensions.scientific import ScientificExtension
from pystac.extensions.storage import StorageExtension
from pystac.extensions.table import TableExtension
from pystac.extensions.timestamps import TimestampsExtension
from pystac.extensions.version import BaseVersionExtension, VersionExtension
from pystac.extensions.view import ViewExtension
from pystac.extensions.xarray_assets import XarrayAssetsExtension

T = TypeVar("T", Asset, AssetDefinition, Link)
U = TypeVar("U", Asset, AssetDefinition)

EXTENSION_NAMES = Literal[
    "classification",
    "cube",
    "eo",
    "file",
    "grid",
    "item_assets",
    "mgrs",
    "pc",
    "proj",
    "raster",
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

EXTENSION_NAME_MAPPING: dict[EXTENSION_NAMES, Any] = {
    ClassificationExtension.name: ClassificationExtension,
    DatacubeExtension.name: DatacubeExtension,
    EOExtension.name: EOExtension,
    FileExtension.name: FileExtension,
    GridExtension.name: GridExtension,
    ItemAssetsExtension.name: ItemAssetsExtension,
    MgrsExtension.name: MgrsExtension,
    PointcloudExtension.name: PointcloudExtension,
    ProjectionExtension.name: ProjectionExtension,
    RasterExtension.name: RasterExtension,
    SarExtension.name: SarExtension,
    SatExtension.name: SatExtension,
    ScientificExtension.name: ScientificExtension,
    StorageExtension.name: StorageExtension,
    TableExtension.name: TableExtension,
    TimestampsExtension.name: TimestampsExtension,
    VersionExtension.name: VersionExtension,
    ViewExtension.name: ViewExtension,
    XarrayAssetsExtension.name: XarrayAssetsExtension,
}


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
    stac_object: Catalog

    def has(self, name: EXTENSION_NAMES) -> bool:
        return cast(bool, _get_class_by_name(name).has_extension(self.stac_object))

    def add(self, name: EXTENSION_NAMES) -> None:
        _get_class_by_name(name).add_to(self.stac_object)

    def remove(self, name: EXTENSION_NAMES) -> None:
        _get_class_by_name(name).remove_from(self.stac_object)

    @property
    def version(self) -> VersionExtension[Catalog]:
        return VersionExtension.ext(self.stac_object)


@dataclass
class CollectionExt(CatalogExt):
    stac_object: Collection

    @property
    def cube(self) -> DatacubeExtension[Collection]:
        return DatacubeExtension.ext(self.stac_object)

    @property
    def item_assets(self) -> dict[str, AssetDefinition]:
        return ItemAssetsExtension.ext(self.stac_object).item_assets

    @property
    def sci(self) -> ScientificExtension[Collection]:
        return ScientificExtension.ext(self.stac_object)

    @property
    def table(self) -> TableExtension[Collection]:
        return TableExtension.ext(self.stac_object)

    @property
    def xarray(self) -> XarrayAssetsExtension[Collection]:
        return XarrayAssetsExtension.ext(self.stac_object)


@dataclass
class ItemExt:
    stac_object: Item

    def has(self, name: EXTENSION_NAMES) -> bool:
        return cast(bool, _get_class_by_name(name).has_extension(self.stac_object))

    def add(self, name: EXTENSION_NAMES) -> None:
        _get_class_by_name(name).add_to(self.stac_object)

    def remove(self, name: EXTENSION_NAMES) -> None:
        _get_class_by_name(name).remove_from(self.stac_object)

    @property
    def classification(self) -> ClassificationExtension[Item]:
        return ClassificationExtension.ext(self.stac_object)

    @property
    def cube(self) -> DatacubeExtension[Item]:
        return DatacubeExtension.ext(self.stac_object)

    @property
    def eo(self) -> EOExtension[Item]:
        return EOExtension.ext(self.stac_object)

    @property
    def grid(self) -> GridExtension:
        return GridExtension.ext(self.stac_object)

    @property
    def mgrs(self) -> MgrsExtension:
        return MgrsExtension.ext(self.stac_object)

    @property
    def pc(self) -> PointcloudExtension[Item]:
        return PointcloudExtension.ext(self.stac_object)

    @property
    def proj(self) -> ProjectionExtension[Item]:
        return ProjectionExtension.ext(self.stac_object)

    @property
    def sar(self) -> SarExtension[Item]:
        return SarExtension.ext(self.stac_object)

    @property
    def sat(self) -> SatExtension[Item]:
        return SatExtension.ext(self.stac_object)

    @property
    def storage(self) -> StorageExtension[Item]:
        return StorageExtension.ext(self.stac_object)

    @property
    def table(self) -> TableExtension[Item]:
        return TableExtension.ext(self.stac_object)

    @property
    def timestamps(self) -> TimestampsExtension[Item]:
        return TimestampsExtension.ext(self.stac_object)

    @property
    def version(self) -> VersionExtension[Item]:
        return VersionExtension.ext(self.stac_object)

    @property
    def view(self) -> ViewExtension[Item]:
        return ViewExtension.ext(self.stac_object)

    @property
    def xarray(self) -> XarrayAssetsExtension[Item]:
        return XarrayAssetsExtension.ext(self.stac_object)


class _AssetsExt(Generic[T]):
    stac_object: T

    def has(self, name: EXTENSION_NAMES) -> bool:
        if self.stac_object.owner is None:
            raise STACError(
                f"Attempted to add extension='{name}' for an object with no owner. "
                "Use `.set_owner` and then try to add the extension again."
            )
        else:
            return cast(
                bool, _get_class_by_name(name).has_extension(self.stac_object.owner)
            )

    def add(self, name: EXTENSION_NAMES) -> None:
        if self.stac_object.owner is None:
            raise STACError(
                f"Attempted to add extension='{name}' for an object with no owner. "
                "Use `.set_owner` and then try to add the extension again."
            )
        else:
            _get_class_by_name(name).add_to(self.stac_object.owner)

    def remove(self, name: EXTENSION_NAMES) -> None:
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
        return ClassificationExtension.ext(self.stac_object)

    @property
    def cube(self) -> DatacubeExtension[U]:
        return DatacubeExtension.ext(self.stac_object)

    @property
    def eo(self) -> EOExtension[U]:
        return EOExtension.ext(self.stac_object)

    @property
    def pc(self) -> PointcloudExtension[U]:
        return PointcloudExtension.ext(self.stac_object)

    @property
    def proj(self) -> ProjectionExtension[U]:
        return ProjectionExtension.ext(self.stac_object)

    @property
    def raster(self) -> RasterExtension[U]:
        return RasterExtension.ext(self.stac_object)

    @property
    def sar(self) -> SarExtension[U]:
        return SarExtension.ext(self.stac_object)

    @property
    def sat(self) -> SatExtension[U]:
        return SatExtension.ext(self.stac_object)

    @property
    def storage(self) -> StorageExtension[U]:
        return StorageExtension.ext(self.stac_object)

    @property
    def table(self) -> TableExtension[U]:
        return TableExtension.ext(self.stac_object)

    @property
    def version(self) -> BaseVersionExtension[U]:
        return BaseVersionExtension.ext(self.stac_object)

    @property
    def view(self) -> ViewExtension[U]:
        return ViewExtension.ext(self.stac_object)


@dataclass
class AssetExt(_AssetExt[Asset]):
    stac_object: Asset

    @property
    def file(self) -> FileExtension[Asset]:
        return FileExtension.ext(self.stac_object)

    @property
    def timestamps(self) -> TimestampsExtension[Asset]:
        return TimestampsExtension.ext(self.stac_object)

    @property
    def xarray(self) -> XarrayAssetsExtension[Asset]:
        return XarrayAssetsExtension.ext(self.stac_object)


@dataclass
class ItemAssetExt(_AssetExt[AssetDefinition]):
    stac_object: AssetDefinition


@dataclass
class LinkExt(_AssetsExt[Link]):
    stac_object: Link

    @property
    def file(self) -> FileExtension[Link]:
        return FileExtension.ext(self.stac_object)
