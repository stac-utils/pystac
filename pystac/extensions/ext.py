from dataclasses import dataclass
from typing import Any, Dict, Union

import pystac
from pystac.extensions.eo import EOExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.utils import StringEnum


class ExtensionName(StringEnum):
    EO = "eo"
    PROJ = "proj"

    @staticmethod
    def get_class(name: Union[str, "ExtensionName"]) -> Any:
        try:
            return EXTENSION_NAME_MAPPING[name]
        except KeyError as e:
            raise KeyError(
                f"Extension '{name}' is not a valid extension. "
                f"Options are {list(EXTENSION_NAME_MAPPING)}"
            ) from e


EXTENSION_NAME_MAPPING: Dict[Union[str, ExtensionName], Any] = {
    ExtensionName.EO: EOExtension,
    ExtensionName.PROJ: ProjectionExtension,
}


@dataclass
class ItemExt:
    stac_object: pystac.Item

    def add(self, name: Union[str, ExtensionName]) -> None:
        ExtensionName.get_class(name).add_to(self.stac_object)

    def remove(self, name: Union[str, ExtensionName]) -> None:
        ExtensionName.get_class(name).remove_from(self.stac_object)

    @property
    def proj(self) -> ProjectionExtension[pystac.Item]:
        return ProjectionExtension.ext(self.stac_object)

    @property
    def eo(self) -> EOExtension[pystac.Item]:
        return EOExtension.ext(self.stac_object)


@dataclass
class AssetExt:
    stac_object: pystac.Asset

    def add(self, name: Union[str, ExtensionName]) -> None:
        if self.stac_object.owner is None:
            raise pystac.STACError(
                f"Attempted to add extension='{name}' for an Asset with no owner. "
                "Use Asset.set_owner and then try to add the extension again."
            )
        else:
            ExtensionName.get_class(name).add_to(self.stac_object.owner)

    def remove(self, name: Union[str, ExtensionName]) -> None:
        if self.stac_object.owner is None:
            raise pystac.STACError(
                f"Attempted to remove extension='{name}' for an Asset with no owner. "
                "Use Asset.set_owner and then try to remove the extension again."
            )
        else:
            ExtensionName.get_class(name).remove_from(self.stac_object.owner)

    @property
    def proj(self) -> ProjectionExtension[pystac.Asset]:
        return ProjectionExtension.ext(self.stac_object)

    @property
    def eo(self) -> EOExtension[pystac.Asset]:
        return EOExtension.ext(self.stac_object)
