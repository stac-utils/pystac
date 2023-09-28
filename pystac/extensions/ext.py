from dataclasses import dataclass
from typing import Any, Dict, Literal, cast

import pystac
from pystac.extensions.classification import ClassificationExtension
from pystac.extensions.datacube import DatacubeExtension
from pystac.extensions.eo import EOExtension
from pystac.extensions.file import FileExtension
from pystac.extensions.grid import GridExtension
from pystac.extensions.label import LabelExtension
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
from pystac.extensions.version import VersionExtension
from pystac.extensions.view import ViewExtension
from pystac.extensions.xarray_assets import XarrayAssetsExtension

EXTENSION_NAMES = Literal[
    "classification",
    "cube",
    "eo",
    "file",
    "grid",
    "label",
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

EXTENSION_NAME_MAPPING: Dict[EXTENSION_NAMES, Any] = {
    ClassificationExtension.name: ClassificationExtension,
    DatacubeExtension.name: DatacubeExtension,
    EOExtension.name: EOExtension,
    FileExtension.name: FileExtension,
    GridExtension.name: GridExtension,
    LabelExtension.name: LabelExtension,
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
class CollectionExt:
    stac_object: pystac.Collection

    def has(self, name: EXTENSION_NAMES) -> bool:
        return cast(bool, _get_class_by_name(name).has_extension(self.stac_object))

    def add(self, name: EXTENSION_NAMES) -> None:
        _get_class_by_name(name).add_to(self.stac_object)

    def remove(self, name: EXTENSION_NAMES) -> None:
        _get_class_by_name(name).remove_from(self.stac_object)

    @property
    def cube(self) -> DatacubeExtension[pystac.Collection]:
        return DatacubeExtension.ext(self.stac_object)

    @property
    def sci(self) -> ScientificExtension[pystac.Collection]:
        return ScientificExtension.ext(self.stac_object)

    @property
    def table(self) -> TableExtension[pystac.Collection]:
        return TableExtension.ext(self.stac_object)

    @property
    def version(self) -> VersionExtension[pystac.Collection]:
        return VersionExtension.ext(self.stac_object)

    @property
    def xarray(self) -> XarrayAssetsExtension[pystac.Collection]:
        return XarrayAssetsExtension.ext(self.stac_object)


@dataclass
class ItemExt:
    stac_object: pystac.Item

    def has(self, name: EXTENSION_NAMES) -> bool:
        return cast(bool, _get_class_by_name(name).has_extension(self.stac_object))

    def add(self, name: EXTENSION_NAMES) -> None:
        _get_class_by_name(name).add_to(self.stac_object)

    def remove(self, name: EXTENSION_NAMES) -> None:
        _get_class_by_name(name).remove_from(self.stac_object)

    @property
    def classification(self) -> ClassificationExtension[pystac.Item]:
        return ClassificationExtension.ext(self.stac_object)

    @property
    def cube(self) -> DatacubeExtension[pystac.Item]:
        return DatacubeExtension.ext(self.stac_object)

    @property
    def eo(self) -> EOExtension[pystac.Item]:
        return EOExtension.ext(self.stac_object)

    @property
    def grid(self) -> GridExtension:
        return GridExtension.ext(self.stac_object)

    @property
    def label(self) -> LabelExtension:
        return LabelExtension.ext(self.stac_object)

    @property
    def mgrs(self) -> MgrsExtension:
        return MgrsExtension.ext(self.stac_object)

    @property
    def pc(self) -> PointcloudExtension[pystac.Item]:
        return PointcloudExtension.ext(self.stac_object)

    @property
    def proj(self) -> ProjectionExtension[pystac.Item]:
        return ProjectionExtension.ext(self.stac_object)

    @property
    def sar(self) -> SarExtension[pystac.Item]:
        return SarExtension.ext(self.stac_object)

    @property
    def sat(self) -> SatExtension[pystac.Item]:
        return SatExtension.ext(self.stac_object)

    @property
    def storage(self) -> StorageExtension[pystac.Item]:
        return StorageExtension.ext(self.stac_object)

    @property
    def table(self) -> TableExtension[pystac.Item]:
        return TableExtension.ext(self.stac_object)

    @property
    def timestamps(self) -> TimestampsExtension[pystac.Item]:
        return TimestampsExtension.ext(self.stac_object)

    @property
    def version(self) -> VersionExtension[pystac.Item]:
        return VersionExtension.ext(self.stac_object)

    @property
    def view(self) -> ViewExtension[pystac.Item]:
        return ViewExtension.ext(self.stac_object)

    @property
    def xarray(self) -> XarrayAssetsExtension[pystac.Item]:
        return XarrayAssetsExtension.ext(self.stac_object)


@dataclass
class AssetExt:
    stac_object: pystac.Asset

    def has(self, name: EXTENSION_NAMES) -> bool:
        if self.stac_object.owner is None:
            raise pystac.STACError(
                f"Attempted to add extension='{name}' for an Asset with no owner. "
                "Use Asset.set_owner and then try to add the extension again."
            )
        else:
            return cast(
                bool, _get_class_by_name(name).has_extension(self.stac_object.owner)
            )

    def add(self, name: EXTENSION_NAMES) -> None:
        if self.stac_object.owner is None:
            raise pystac.STACError(
                f"Attempted to add extension='{name}' for an Asset with no owner. "
                "Use Asset.set_owner and then try to add the extension again."
            )
        else:
            _get_class_by_name(name).add_to(self.stac_object.owner)

    def remove(self, name: EXTENSION_NAMES) -> None:
        if self.stac_object.owner is None:
            raise pystac.STACError(
                f"Attempted to remove extension='{name}' for an Asset with no owner. "
                "Use Asset.set_owner and then try to remove the extension again."
            )
        else:
            _get_class_by_name(name).remove_from(self.stac_object.owner)

    @property
    def classification(self) -> ClassificationExtension[pystac.Asset]:
        return ClassificationExtension.ext(self.stac_object)

    @property
    def cube(self) -> DatacubeExtension[pystac.Asset]:
        return DatacubeExtension.ext(self.stac_object)

    @property
    def eo(self) -> EOExtension[pystac.Asset]:
        return EOExtension.ext(self.stac_object)

    @property
    def file(self) -> FileExtension:
        return FileExtension.ext(self.stac_object)

    @property
    def pc(self) -> PointcloudExtension[pystac.Asset]:
        return PointcloudExtension.ext(self.stac_object)

    @property
    def proj(self) -> ProjectionExtension[pystac.Asset]:
        return ProjectionExtension.ext(self.stac_object)

    @property
    def raster(self) -> RasterExtension[pystac.Asset]:
        return RasterExtension.ext(self.stac_object)

    @property
    def sar(self) -> SarExtension[pystac.Asset]:
        return SarExtension.ext(self.stac_object)

    @property
    def sat(self) -> SatExtension[pystac.Asset]:
        return SatExtension.ext(self.stac_object)

    @property
    def storage(self) -> StorageExtension[pystac.Asset]:
        return StorageExtension.ext(self.stac_object)

    @property
    def table(self) -> TableExtension[pystac.Asset]:
        return TableExtension.ext(self.stac_object)

    @property
    def timestamps(self) -> TimestampsExtension[pystac.Asset]:
        return TimestampsExtension.ext(self.stac_object)

    @property
    def view(self) -> ViewExtension[pystac.Asset]:
        return ViewExtension.ext(self.stac_object)

    @property
    def xarray(self) -> XarrayAssetsExtension[pystac.Asset]:
        return XarrayAssetsExtension.ext(self.stac_object)
