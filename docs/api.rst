API Reference
=============

.. toctree::
   :hidden:
   :maxdepth: 2
   :glob:

   api/pystac
   api/*

This API reference is auto-generated from the Python docstrings. The table of contents
on the left is organized by module. The sections below are organized based on concepts
and sections within the :stac-spec:`STAC Spec <>` and PySTAC itself.

Primitive Structures
--------------------

These are the core Python classes representing entities within the STAC Spec. These
classes provide convenient methods for serializing and deserializing from JSON,
extracting properties, and creating relationships between entities.

* :class:`pystac.Link`: Represents a :stac-spec:`Link Object
  <item-spec/item-spec.md#link-object>`.
* :class:`pystac.MediaType`: Provides common values used in the Link and Asset
  ``"type"`` fields.
* :class:`pystac.RelType`: Provides common values used in the Link ``"rel"`` field.
* :class:`pystac.STACObject`: Base class implementing functionality common to
  :class:`Catalog <pystac.Catalog>`, :class:`Collection <pystac.Collection>` and
  :class:`Item <pystac.Item>`.

Items
-----

Representations of :stac-spec:`Items <item-spec/item-spec.md>` and related structures
like :stac-spec:`Asset Objects<item-spec/item-spec.md#asset-object>`.

* :class:`pystac.Asset`: Represents an :stac-spec:`Asset Object
  <item-spec/item-spec.md#asset-object>`
* :class:`pystac.Item`: Represents an :stac-spec:`Item <item-spec/item-spec.md>`
* :class:`pystac.CommonMetadata`: A container for fields defined in the
  :stac-spec:`Common Metadata <item-spec/common-metadata.md>` section of the spec.
  These fields are commonly found in STAC Item properties, but may be found elsewhere.

Collections
-----------

These are representations of :stac-spec:`Collections
<collection-spec/collectino-spec.md>` and related structures.

* :class:`pystac.Collection`: Represents a :stac-spec:`Collection
  <collection-spec/collection-spec.md>`.
* :class:`pystac.Extent`: Represents an
  :stac-spec:`Extent Object <collection-spec/collection-spec.md#extent-object>`, which
  is composed of :class:`pystac.SpatialExtent` and :class:`pystac.TemporalExtent`
  instances.
* :class:`pystac.Provider`: Represents a :stac-spec:`Provider Object
  <collection-spec/collection-spec.md#provider-object>`. The
  :class:`pystac.ProviderRole` enum provides common values used in the ``"roles"``
  field.
* :class:`pystac.Summaries`: Class for working with various types of
  :stac-spec:`CollectionSummaries <collection-spec/collection-spec.md#summaries>`
* :class:`pystac.ItemCollection`: Represents a GeoJSON FeatureCollection in which all
  Features are STAC Items.

Catalogs
--------

Representations of :stac-spec:`Catalogs <catalog-spec/catalog-spec.md>` and related
structures.

* :class:`pystac.Catalog`: Represents a :stac-spec:`Catalog
  <catalog-spec/catalog-spec.md>`.
* :class:`pystac.CatalogType`: Enum representing the common types of Catalogs described
  in the :stac-spec:`STAC Best Practices
  <https://github.com/radiantearth/stac-spec/blob/master/best-practices.md#use-of-links>`


I/O
---

These classes are used to read and write files from disk or over the network, as well
as to serialize and deserialize STAC object to and from JSON.

* :class:`pystac.StacIO`: Base class that can be inherited to provide custom I/O
* :class:`pystac.stac_io.DefaultStacIO`: The default :class:`pystac.StacIO`
  implementation used throughout the library.

Extensions
----------

PySTAC provides support for the following STAC Extensions:

* :mod:`Datacube <pystac.extensions.datacube>`
* :mod:`Electro-Optical <pystac.extensions.eo>`
* :mod:`File Info <pystac.extensions.file>`
* :mod:`Item Assets <pystac.extensions.item_assets>`
* :mod:`Label <pystac.extensions.label>`
* :mod:`Point Cloud <pystac.extensions.pointcloud>`
* :mod:`Projection <pystac.extensions.projection>`
* :mod:`Raster <pystac.extensions.raster>`
* :mod:`SAR <pystac.extensions.sar>`
* :mod:`Satellite <pystac.extensions.sat>`
* :mod:`Scientific Citation <pystac.extensions.scientific>`
* :mod:`Table <pystac.extensions.table>`
* :mod:`Timestamps <pystac.extensions.timestamps>`
* :mod:`Versioning Indicators <pystac.extensions.version>`
* :mod:`View Geometry <pystac.extensions.view>`

The following classes are used internally to implement these extensions and may be used
to create custom implementations of STAC Extensions not supported by the library (see
:tutorial:`Adding New and Custom Extensions <adding-new-and-custom-extensions.ipynb>`
for details):

* :class:`pystac.extensions.base.SummariesExtension`: Base class for extending the
  properties in :attr:`pystac.Collection.summaries` to include properties defined by a
  STAC Extension.
* :class:`pystac.extensions.base.PropertiesExtension`: Abstract base class for
  extending the properties of an :class:`~pystac.Item` to include properties defined
  by a STAC Extension.
* :class:`pystac.extensions.base.ExtensionManagementMixin`: Abstract base class with
  methods for adding and removing extensions from STAC Objects.
* :class:`pystac.extensions.hooks.ExtensionHooks`: Used to implement hooks when
  extending a STAC Object. Primarily used to implement migrations from one extension
  version to another.
* :class:`pystac.extensions.hooks.RegisteredExtensionHooks`: Used to register hooks
  defined in :class:`~pystac.extensions.hooks.ExtensionHooks` instances to ensure they
  are used in object deserialization.


Catalog Layout
--------------

These classes are used to set the HREFs of a STAC according to some layout.
The templating functionality is also used when generating subcatalogs based on
a template.

* :class:`pystac.layout.LayoutTemplate`: Represents a template that can be used for
  deriving paths or other information based on properties of STAC objects supplied as a
  template string.
* :class:`pystac.layout.BestPracticesLayoutStrategy`: Layout strategy that represents
  the catalog layout described in the :stac-spec:`STAC Best Practices documentation
  <best-practices.md>`.
* :class:`pystac.layout.TemplateLayoutStrategy`: Layout strategy that can take strings
  to be supplied to a :class:`~pystac.layout.LayoutTemplate` to derive paths.
* :class:`pystac.layout.CustomLayoutStrategy`: Layout strategy that allows users to
  supply functions to dictate stac object paths.

Errors
------

The following exceptions may be raised internally by the library.

* :class:`pystac.STACError`: Generic STAC-related error
* :class:`pystac.STACTypeError`: Raised when a representation of a STAC entity is
  encountered that is not correct for the context
* :class:`pystac.DuplicateObjectKeyError`: Raised when deserializing a JSON object
  containing a duplicate key.
* :class:`pystac.ExtensionAlreadyExistsError`: Raised when deserializing a JSON object
  containing a duplicate key.
* :class:`pystac.ExtensionTypeError`: Raised when an extension is used against an
  object to which that the extension does not apply to.
* :class:`pystac.ExtensionNotImplemented`: Raised on an attempt to extend a STAC object
  that does not implement the given extension.
* :class:`pystac.RequiredPropertyMissing`: Raised when a required value is expected to
  be present but is missing or ``None``.
* :class:`pystac.STACValidationError`: Raised by validation calls if the STAC JSON is
  invalid.
* :class:`pystac.layout.TemplateError`: Raised when an error occurs while converting a
  template string into data for :class:`~pystac.layout.LayoutTemplate`.

Serialization
-------------

The ``pystac.serialization`` sub-package contains tools used internally by PySTAC to
identify, serialize, and migrate STAC objects:

* :mod:`pystac.serialization.identify`: Tools for identifying STAC objects
* :mod:`pystac.serialization.migrate`: Tools for migrating STAC objects from a previous
  STAC Spec version.


Validation
----------

.. note::

    The tools described here require that you install PySTAC with the ``validation``
    extra (see the documentation on :ref:`installing dependencies
    <installation_dependencies>` for details).

PySTAC includes a ``pystac.validation`` package for validating STAC objects, including
from PySTAC objects and directly from JSON.

* :class:`pystac.validation.stac_validator.STACValidator`: Abstract base class defining
  methods for validating STAC JSON. Implementations define methods for validating core
  objects and extension.
* :class:`pystac.validation.stac_validator.JsonSchemaSTACValidator`: The default
  :class:`~pystac.validation.stac_validator.STACValidator` implementation used by
  PySTAC. Uses JSON schemas read from URIs provided by a
  :class:`~pystac.validation.schema_uri_map.SchemaUriMap`, to validate STAC objects.
* :class:`pystac.validation.schema_uri_map.SchemaUriMap`: Defines methods for mapping
  STAC versions, object types and extension ids to schema URIs. A default
  implementation is included that uses known locations; however users can provide their
  own schema URI maps in a
  :class:`~pystac.validation.stac_validator.JsonSchemaSTACValidator` to modify the URIs
  used.
* :class:`pystac.validation.schema_uri_map.DefaultSchemaUriMap`: The default
  :class:`~pystac.validation.schema_uri_map.SchemaUriMap` used by PySTAC.

Internal Classes
-----------------------

These classes are used internally by PySTAC for caching.

* :class:`pystac.cache.ResolvedObjectCache`
