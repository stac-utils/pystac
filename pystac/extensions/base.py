from abc import (ABC, abstractmethod)

from pystac.catalog import Catalog
from pystac.collection import Collection
from pystac.item import Item
from pystac.extensions import ExtensionError


class ExtendedObject:
    """ExtendedObject maps STACObject classes (Catalog, Collecition and Item) to
    extension classes (classes that implement one of CatalogExtension, CollectionExtesion,
    or ItemCollection). When an extension is registered with PySTAC it uses the registered
    list of ExtendedObject to determine how to handle extending objects, e.g. when item.ext.label
    is called, it searches for the ExtendedObject associated with the label extension that
    maps Item to LabelItemExt.

    Args:
        stac_object_class: The STAC object class that is being extended.
        extension_class: The class of the extension, e.g. LabelItemExt
    """
    def __init__(self, stac_object_class, extension_class):
        if stac_object_class is Catalog:
            if not issubclass(extension_class, CatalogExtension):
                raise ExtensionError(
                    "Classes extending catalogs must inherit from CatalogExtension")
        if stac_object_class is Collection:
            if not issubclass(extension_class, CollectionExtension):
                raise ExtensionError(
                    "Classes extending collections must inherit from CollectionExtension")
        if stac_object_class is Item:
            if not issubclass(extension_class, ItemExtension):
                raise ExtensionError("Classes extending item must inherit from ItemExtension")

        self.stac_object_class = stac_object_class
        self.extension_class = extension_class


class ExtensionDefinition:
    """Defines an extension that can be registered with PySTAC.

    Args:
        extension_id: The ID for the extension. This is the same idea that will appear in
            the ``stac_extensions`` property of implementing objects, and will be used to refer
            to the extension in PySTAC.
        extended_objects (List[ExtendedObject]): The list of ExtendedObjects which map STACObject
            types to their extension. Should only contain one entry per stac object type.
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
        raise NotImplementedError("from_catalog")

    @classmethod
    @abstractmethod
    def _object_links(cls):
        raise NotImplementedError("_object_links")

    @classmethod
    def enable_extension(cls, stac_object):
        """Enables the extension for the given stac_object.
        Child classes can choose to override this method in order to
        modify the stac_object when an extension is enabled.
        """
        pass


class CollectionExtension(ABC):
    @classmethod
    def _from_object(cls, stac_object):
        return cls.from_collection(stac_object)

    @classmethod
    @abstractmethod
    def from_collection(cls, catalog):
        raise NotImplementedError("from_collection")

    @classmethod
    @abstractmethod
    def _object_links(cls):
        raise NotImplementedError("_object_links")

    @classmethod
    def enable_extension(cls, stac_object):
        """Enables the extension for the given stac_object.
        Child classes can choose to override this method in order to
        modify the stac_object when an extension is enabled.
        """
        pass


class ItemExtension(ABC):
    @classmethod
    def _from_object(cls, stac_object):
        return cls.from_item(stac_object)

    @classmethod
    @abstractmethod
    def from_item(cls, item):
        raise NotImplementedError("from_item")

    @classmethod
    @abstractmethod
    def _object_links(cls):
        raise NotImplementedError("_object_links")

    @classmethod
    def enable_extension(cls, stac_object):
        """Enables the extension for the given stac_object.
        Child classes can choose to override this method in order to
        modify the stac_object when an extension is enabled.
        """
        pass


class RegisteredSTACExtensions:
    def __init__(self, extension_definitions):
        self.extensions = dict([(e.extension_id, e) for e in extension_definitions])

    def is_registered_extension(self, extension_id):
        """Determines whether or not the given extension ID has been registered."""
        return extension_id in self.extensions

    def get_registered_extensions(self):
        """Returns the list of registered extension IDs."""
        return list(self.extensions.keys())

    def add_extension(self, extension_definition):
        e_id = extension_definition.extension_id
        if e_id in self.extensions:
            raise ExtensionError("ExtensionDefinition with id '{}' already exists.".format(e_id))

        self.extensions[e_id] = extension_definition

    def remove_extension(self, extension_id):
        """Remove an extension from PySTAC."""
        if extension_id not in self.extensions:
            raise ExtensionError(
                "ExtensionDefinition with id '{}' is not registered.".format(extension_id))
        del self.extensions[extension_id]

    def get_extension_class(self, extension_id, stac_object_class):
        """Gets the extension class for a given stac object class if one exists, otherwise
        returns None
        """
        ext = self.extensions.get(extension_id)
        if ext is None:
            raise ExtensionError("No ExtensionDefinition registered with id '{}'. "
                                 "Is the extension ID correct, or are you forgetting to call "
                                 "'add_extension' for a custom extension?".format(extension_id))

        ext_classes = [
            e.extension_class for e in ext.extended_objects
            if issubclass(stac_object_class, e.stac_object_class)
        ]

        ext_class = None
        if len(ext_classes) == 0:
            return None
        elif len(ext_classes) == 1:
            ext_class = ext_classes[0]
        else:
            # Need to check collection extensions before catalogs.
            sort_key = {}
            for c in ext_classes:
                for i, base_cl in enumerate([ItemExtension, CollectionExtension, CatalogExtension]):
                    if issubclass(c, base_cl):
                        sort_key[c] = i
                        break
                if c not in sort_key:
                    sort_key[c] = -1

            ext_class = sorted(ext_classes, key=lambda c: sort_key[c])[0]

        return ext_class

    def extend_object(self, extension_id, stac_object):
        """Returns the extension object for the given STACObject and the given
        extension_id
        """
        ext_class = self.get_extension_class(extension_id, type(stac_object))

        if ext_class is None:
            raise ExtensionError("Extension '{}' does not extend objects of type {}".format(
                extension_id, type(stac_object)))

        return ext_class._from_object(stac_object)

    def get_extended_object_links(self, stac_object):
        if stac_object.stac_extensions is None:
            return []
        return [
            link_rel for e_id in stac_object.stac_extensions if e_id in self.extensions
            for e_obj in self.extensions[e_id].extended_objects
            if issubclass(type(stac_object), e_obj.stac_object_class)
            for link_rel in e_obj.extension_class._object_links()
        ]

    def can_extend(self, extension_id, stac_object_class):
        """Returns True if the extension can extend the given object type.

        Args:
            extension_id (str): The extension ID to check.
            stac_object_class: the class of the object to check. Will check against subclasses,
                so will return the correct result even if the object is a subclass of Catalog,
                Collection or Item.

        Returns:
            bool
        """
        ext = self.extensions.get(extension_id)

        # Check to make sure this is a registered extension.
        if ext is None:
            raise ExtensionError("'{}' is not a registered extension".format(extension_id))

        return any([
            e.extension_class for e in ext.extended_objects
            if issubclass(stac_object_class, e.stac_object_class)
        ])

    def enable_extension(self, extension_id, stac_object):
        """Enables the extension for the given object.

        This will at least ensure the extension ID is in the object's "stac_extensions"
        property. Some extensions may make additional modifications to the object.
        """
        # Check to make sure this is a registered extension.
        if not self.is_registered_extension(extension_id):
            raise ExtensionError("'{}' is not an extension "
                                 "registered with PySTAC".format(extension_id))

        ext_class = self.get_extension_class(extension_id, type(stac_object))

        if ext_class is None:
            raise ExtensionError("Extension '{}' does not extend objects of type {}".format(
                extension_id, type(stac_object)))

        if stac_object.stac_extensions is None:
            stac_object.stac_extensions = [extension_id]
        elif extension_id not in stac_object.stac_extensions:
            stac_object.stac_extensions.append(extension_id)

        ext_class.enable_extension(stac_object)
