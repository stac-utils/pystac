# from pystac.item import Item
# from typing import Dict, List, Optional, cast

# import pystac as ps
# from pystac.extensions.base import (CatalogExtension, ExtensionDefinition, ExtendedObject)

# def create_single_file_stac(catalog: ps.Catalog) -> ps.Catalog:
#     """Creates a Single File STAC from a STAC catalog.

#     This method will recursively collect any collections and items in the catalog
#     and return a new catalog with the same properties as the old one, with cleared
#     links and the 'collections' and 'features' property of the Single File STAC holding
#     each of the respective collected STAC objects.

#     Collections will be filtered to only those referenced by items via the collection_id.
#     All links in the items and collections will be cleared in the Single File STAC.

#     Args:
#         catalog (Catalog): Catalog to walk while constructing the Single File STAC
#     """
#     collections: Dict[str, ps.Collection] = {}
#     items: List[ps.Item] = []
#     for root, _, cat_items in catalog.walk():
#         if isinstance(root, ps.Collection):
#             new_collection = root.clone()
#             new_collection.clear_links()
#             collections[root.id] = new_collection
#         for item in cat_items:
#             new_item = item.clone()
#             new_item.clear_links()
#             items.append(new_item)

#     filtered_collections: List[ps.Collection] = []
#     for item in items:
#         if item.collection_id is not None and item.collection_id in collections:
#             filtered_collections.append(collections[item.collection_id])
#             collections.pop(item.collection_id)

#     result = catalog.clone()
#     result.clear_links()
#     result.ext.enable(ps.Extensions.SINGLE_FILE_STAC)
#     sfs_ext = cast("SingleFileSTACCatalogExt", result.ext[ps.Extensions.SINGLE_FILE_STAC])
#     sfs_ext.apply(features=items, collections=filtered_collections)

#     return result

# class SingleFileSTACCatalogExt(CatalogExtension):
#     """An extension of Catalog that provides a set of Collections and Items
#     as a single file catalog. A SingleFileSTAC
#     is a self contained catalog that contains everything that would normally be in a
#     linked set of STAC files.

#     Args:
#         catalog (Catalog): The catalog to be extended.

#     Attributes:
#         catalog (Catalog): The catalog that is being extended.

#     Note:
#         Using SingleFileSTACCatalogExt to directly wrap a Catalog will
#         add the 'proj' extension ID to the catalog's stac_extensions.
#     """
#     def __init__(self, catalog: ps.Catalog) -> None:
#         if catalog.stac_extensions is None:
#             catalog.stac_extensions = [str(ps.Extensions.SINGLE_FILE_STAC)]
#         elif str(ps.Extensions.SINGLE_FILE_STAC) not in catalog.stac_extensions:
#             catalog.stac_extensions.append(str(ps.Extensions.SINGLE_FILE_STAC))

#         self.catalog = catalog

#     def apply(self,
#               features: List[Item],
#               collections: Optional[List[ps.Collection]] = None) -> None:
#         """
#         Args:
#             features (List[Item]): List of items contained by
#                 this SingleFileSTAC.
#             collections (List[Collection]): Optional list of collections that are
#                 used by any of the Items in the catalog.
#         """
#         self.features = features
#         self.collections = collections

#     @classmethod
#     def enable_extension(cls, stac_object: ps.STACObject) -> None:
#         # Ensure the 'type' property is correct so that the Catalog is valid GeoJSON.
#         if isinstance(stac_object, ps.Catalog):
#             stac_object.extra_fields['type'] = 'FeatureCollection'

#     @property
#     def features(self) -> List[Item]:
#         """Get or sets a list of :class:`~pystac.Item` contained in this Single File STAC.

#         Returns:
#             List[Item]
#         """
#         features = self.catalog.extra_fields.get('features')
#         if features is None:
#             raise ps.STACError('Invalid Single File STAC: does not have "features" property.')

#         return [Item.from_dict(feature) for feature in features]

#     @features.setter
#     def features(self, v: List[Item]) -> None:
#         self.catalog.extra_fields['features'] = [item.to_dict() for item in v]

#     @property
#     def collections(self) -> Optional[List[ps.Collection]]:
#         """Get or sets a list of :class:`~pystac.Collection` objects contained
#         in this Single File STAC.
#         """
#         collections = self.catalog.extra_fields.get('collections')

#         if collections is None:
#             return None
#         else:
#             return [ps.Collection.from_dict(col) for col in collections]

#     @collections.setter
#     def collections(self, v: Optional[List[ps.Collection]]) -> None:
#         if v is not None:
#             self.catalog.extra_fields['collections'] = [col.to_dict() for col in v]
#         else:
#             self.catalog.extra_fields.pop('collections', None)

#     @classmethod
#     def _object_links(cls) -> List[str]:
#         return []

#     @classmethod
#     def from_catalog(cls, catalog: ps.Catalog) -> "SingleFileSTACCatalogExt":
#         return SingleFileSTACCatalogExt(catalog)

# SFS_EXTENSION_DEFINITION: ExtensionDefinition = ExtensionDefinition(
#     ps.Extensions.SINGLE_FILE_STAC, [ExtendedObject(ps.Catalog, SingleFileSTACCatalogExt)])
