__all__ = [
    "merge_common_properties",
    "migrate_to_latest",
    "STACVersionRange",
    "identify_stac_object",
    "identify_stac_object_type",
]
from pystac.serialization.identify import (
    STACVersionRange,
    identify_stac_object,
    identify_stac_object_type,
)
from pystac.serialization.common_properties import merge_common_properties
from pystac.serialization.migrate import migrate_to_latest
