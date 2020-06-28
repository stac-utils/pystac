from abc import (ABC, abstractmethod)

import pystac
from pystac.catalog import Catalog
from pystac.collection import Collection
from pystac.item import Item

class ExtensionError(Exception):
    """An error related to the construction of extensions.
    """
    pass

class ExtendedObject:
    """TODO
    """
    def __init__(self, stac_object_class, extension_class):
        if stac_object_class is Catalog:
            if not issubclass(extension_class, CatalogExtension):
                raise ExtensionError("Classes extending catalogs must inheret from CatalogExtension")
        if stac_object_class is Collection:
            if not issubclass(extension_class, CollectionExtension):
                raise ExtensionError("Classes extending collections must inheret from CollectionExtension")
        if stac_object_class is Item:
            if not issubclass(extension_class, ItemExtension):
                raise ExtensionError("Classes extending item must inheret from ItemExtension")

        self.stac_object_class = stac_object_class
        self.extension_class = extension_class

class ExtensionDefinition:
    """TODO

    Note about if an extension extends both Collection and Catalog, list the Collection
    extension first.
    """
    def __init__(self, extension_id, extended_objects):
        self.extension_id = extension_id
        self.extended_objects = extended_objects

class CatalogExtension(ABC):
    @classmethod
    def _from_object(cls, stac_object):
        return cls.from_catalog(stac_object)

    @classmethod
    @abstractmethod
    def from_catalog(cls, catalog):
        pass

    @classmethod
    @abstractmethod
    def _object_links(cls):
        pass

class CollectionExtension(ABC):
    @classmethod
    def _from_object(cls, stac_object):
        return cls.from_collection(stac_object)

    @classmethod
    @abstractmethod
    def from_catalog(cls, catalog):
        pass

    @classmethod
    @abstractmethod
    def _object_links(cls):
        pass

class ItemExtension(ABC):
    @classmethod
    def _from_object(cls, stac_object):
        return cls.from_item(stac_object)

    @classmethod
    @abstractmethod
    def from_item(cls, item):
        pass

    @classmethod
    @abstractmethod
    def _object_links(cls):
        pass

class EnabledSTACExtensions:
    def __init__(self, extension_definitions):
        self.extensions = dict([(e.extension_id, e) for e in extension_definitions])

    def add_extension(self, extension_definition):
        if extension_definition.extension_id in self.extensions:
            raise ExtensionError("ExtensionDefinition with id '{}' already exists.".format(extension_id))

        self.extensions[extension_definition.extension_id] = extension_definition

    def extend_object(self, stac_object, extension_id):
        ext = self.extensions.get(extension_id)
        if ext is None:
            raise ExtensionError("No ExtensionDefinition registered with id '{}'. Is the extension ID correct, or are you forgetting to call 'add_extension' for a custom extension?".format(extension_id))

        stac_object_class = type(stac_object)

        ext_class = next(iter([e.extension_class
                          for e in ext.extended_objects
                          if issubclass(stac_object_class, e.stac_object_class)]), None)

        if ext_class is None:
            raise ExtensionError("Extension '{}' does not extend objects of type {}".format(
                extension_id, ext_class
            ))

        return ext_class._from_object(stac_object)

    def get_extended_object_links(self, stac_object):
        if stac_object.stac_extensions is None:
            return []
        return [
            link_rel
            for e_id in stac_object.stac_extensions
            if e_id in self.extensions
            for e_obj in self.extensions[e_id].extended_objects
            if issubclass(type(stac_object), e_obj.stac_object_class)
            for link_rel in e_obj.extension_class._object_links()
        ]
