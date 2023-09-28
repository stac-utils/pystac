from dataclasses import dataclass
from typing import Any, Dict, Literal, cast

import pystac
from pystac.extensions.eo import EOExtension
from pystac.extensions.projection import ProjectionExtension

EXTENSION_NAMES = Literal["eo", "proj"]

EXTENSION_NAME_MAPPING: Dict[EXTENSION_NAMES, Any] = {
    EOExtension.name: EOExtension,
    ProjectionExtension.name: ProjectionExtension,
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
class ItemExt:
    stac_object: pystac.Item

    def add(self, name: EXTENSION_NAMES) -> None:
        _get_class_by_name(name).add_to(self.stac_object)

    def remove(self, name: EXTENSION_NAMES) -> None:
        _get_class_by_name(name).remove_from(self.stac_object)

    @property
    def proj(self) -> ProjectionExtension[pystac.Item]:
        return ProjectionExtension.ext(self.stac_object)

    @property
    def eo(self) -> EOExtension[pystac.Item]:
        return EOExtension.ext(self.stac_object)


@dataclass
class AssetExt:
    stac_object: pystac.Asset

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
    def proj(self) -> ProjectionExtension[pystac.Asset]:
        return ProjectionExtension.ext(self.stac_object)

    @property
    def eo(self) -> EOExtension[pystac.Asset]:
        return EOExtension.ext(self.stac_object)
