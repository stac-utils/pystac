API Reference
=============

This API reference is auto-generated for the Python docstrings,
and organized by the section of the `STAC Spec <https://github.com/radiantearth/stac-spec/tree/v1.0.0-beta.2>`_ they relate to, if related to a specific spec item.

pystac
------

.. automodule:: pystac
   :members: read_file, write_file, read_dict, set_stac_version, get_stac_version

STACObject
----------

STACObject is the base class for :class:`Catalog <pystac.Catalog>`, :class:`Collection <pystac.Collection>` and :class:`Item <pystac.Item>`, and contains a variety of useful methods for dealing with links, copying objects, accessing extensions, and reading and writing files. You shouldn't use STACObject directly, but instead access this functionality through the implementing classes.

.. autoclass:: pystac.STACObject
   :members:
   :inherited-members:
   :undoc-members:

.. autoclass:: pystac.STACObjectType
   :members:
   :undoc-members:


Catalog Spec
------------

These classes are representations of the `Catalog Spec <https://github.com/radiantearth/stac-spec/tree/v1.0.0-beta.2/catalog-spec>`_.

Catalog
~~~~~~~

.. autoclass:: pystac.Catalog
   :members:
   :undoc-members:
   :show-inheritance:

CatalogType
~~~~~~~~~~~

.. autoclass:: pystac.CatalogType
   :members:
   :inherited-members:
   :undoc-members:


Collection Spec
---------------

These classes are representations of the `Collection Spec <https://github.com/radiantearth/stac-spec/tree/v1.0.0-beta.2/collection-spec>`_.

Collection
~~~~~~~~~~

.. autoclass:: pystac.Collection
   :members:
   :undoc-members:
   :show-inheritance:

Extent
~~~~~~

.. autoclass:: pystac.Extent
   :members:
   :undoc-members:

SpatialExtent
~~~~~~~~~~~~~

.. autoclass:: pystac.SpatialExtent
   :members:
   :undoc-members:

TemporalExtent
~~~~~~~~~~~~~~

.. autoclass:: pystac.TemporalExtent
   :members:
   :undoc-members:

Provider
~~~~~~~~

.. autoclass:: pystac.Provider
   :members:
   :undoc-members:

Item Spec
---------

These classes are representations of the `Item Spec <https://github.com/radiantearth/stac-spec/tree/v1.0.0-beta.2/item-spec>`_.

Item
~~~~

.. autoclass:: pystac.Item
   :members:
   :undoc-members:
   :show-inheritance:

Asset
~~~~~

.. autoclass:: pystac.Asset
   :members:
   :undoc-members:

CommonMetadata
~~~~~~~~~~~~~~

.. autoclass:: pystac.CommonMetadata
   :members:
   :undoc-members:

Links
-----

Catalogs, Collections and Items have links, which allow users to crawl catalogs.

Link
~~~~

.. autoclass:: pystac.Link
   :members:
   :undoc-members:

LinkType
~~~~~~~~

.. autoclass:: pystac.LinkType
   :members:
   :undoc-members:

MediaType
~~~~~~~~~

.. autoclass:: pystac.MediaType
   :members:
   :undoc-members:

IO
--

STAC_IO
~~~~~~~

STAC_IO is the utility mechanism that PySTAC uses for reading and writing. Users of PySTAC can hook into PySTAC by overriding members to utilize their own IO methods.

.. autoclass:: pystac.STAC_IO
   :members:
   :undoc-members:

Errors
------

STACError
~~~~~~~~~

.. autoclass:: pystac.STACError

ExtensionError
~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.ExtensionError

Extensions
----------

.. autoclass:: pystac.extensions.Extensions
   :members:
   :undoc-members:

ExtensionIndex
~~~~~~~~~~~~~~

An ExtensionIndex is accessed through the :attr:`STACObject.ext <pystac.STACObject.ext>` property and is the primary way to access information and functionality around STAC extensions.

.. autoclass:: pystac.stac_object.ExtensionIndex
   :members: __getitem__, __getattr__, enable, implements


EO Extension
------------

These classes are representations of the `EO Extension Spec <https://github.com/radiantearth/stac-spec/tree/v1.0.0-beta.2/extensions/eo>`_.

EOItemExt
~~~~~~~~~

.. autoclass:: pystac.extensions.eo.EOItemExt
   :members:
   :undoc-members:
   :show-inheritance:

Band
~~~~

.. autoclass:: pystac.extensions.eo.Band
   :members:
   :undoc-members:


Label Extension
---------------

These classes are representations of the `Label Extension Spec <https://github.com/radiantearth/stac-spec/tree/v1.0.0-beta.2/extensions/label>`_.

LabelItemExt
~~~~~~~~~~~~

.. autoclass:: pystac.extensions.label.LabelItemExt
   :members:
   :undoc-members:
   :show-inheritance:

LabelType
~~~~~~~~~

.. autoclass:: pystac.extensions.label.LabelType
   :members:
   :undoc-members:

LabelClasses
~~~~~~~~~~~~

.. autoclass:: pystac.extensions.label.LabelClasses
   :members:
   :undoc-members:

LabelOverview
~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.label.LabelOverview
   :members:
   :undoc-members:

LabelCount
~~~~~~~~~~

.. autoclass:: pystac.extensions.label.LabelCount
   :members:
   :undoc-members:

LabelStatistics
~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.label.LabelStatistics
   :members:
   :undoc-members:

Pointcloud Extension
--------------------

Implements the `Projection Extension <https://github.com/radiantearth/stac-spec/tree/v1.0.0-beta.2/extensions/pointcloud>`_.

PointcloudItemExt
~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.projection.PointcloudItemExt
   :members:
   :undoc-members:
   :show-inheritance:


Projection Extension
--------------------

Implements the `Projection Extension <https://github.com/radiantearth/stac-spec/tree/v1.0.0-beta.2/extensions/projection>`_.

ProjectionItemExt
~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.projection.ProjectionItemExt
   :members:
   :undoc-members:
   :show-inheritance:

Timestamps Extension
--------------------

Implements the `Timestamps Extension <https://github.com/radiantearth/stac-spec/tree/v1.0.0-beta.2/extensions/timestamps>`_.

TimestampsItemExt
~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.timestamps.TimestampsItemExt
   :members:
   :undoc-members:
   :show-inheritance:

Single File STAC Extension
--------------------------

These classes are representations of the `Single File STAC Extension <https://github.com/radiantearth/stac-spec/tree/v1.0.0-beta.2/extensions/single-file-stac>`_.

.. automodule:: pystac.extensions.single_file_stac
   :members: create_single_file_stac

SingleFileSTACCatalogExt
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.single_file_stac.SingleFileSTACCatalogExt
   :members:
   :undoc-members:

View Geometry Extension
-----------------------

Implements the `View Geometry Extension <https://github.com/radiantearth/stac-spec/tree/v1.0.0-beta.2/extensions/view>`_.

ViewItemExt
~~~~~~~~~~~

.. autoclass:: pystac.extensions.view.ViewItemExt
   :members:
   :undoc-members:
   :show-inheritance:

Serialization
-------------

PySTAC includes a ``pystac.serialization`` package for serialization concerns that
are used internally, but may also be useful to external tools.

Identification
~~~~~~~~~~~~~~

.. automodule:: pystac.serialization
   :members: identify_stac_object

.. autoclass:: pystac.serialization.STACJSONDescription
   :members:
   :undoc-members:

.. autoclass:: pystac.serialization.STACVersionRange
   :members:
   :undoc-members:

.. autoclass:: pystac.serialization.STACVersionID
   :members:
   :undoc-members:


Migration
~~~~~~~~~

.. automodule:: pystac.serialization.migrate
   :members: migrate_to_latest

Common Properties
~~~~~~~~~~~~~~~~~

.. automodule:: pystac.serialization
   :members: merge_common_properties


Validation
----------

pystac.validation
~~~~~~~~~~~~~~~~~

PySTAC includes a ``pystac.validation`` package for validating STAC objects, including
from PySTAC objects and directly from JSON.

.. automodule:: pystac.validation
   :members: validate, validate_dict, validate_all, set_validator, STACValidationError

STACValidator
~~~~~~~~~~~~~

.. autoclass:: pystac.validation.STACValidator
   :members:

.. autoclass:: pystac.validation.JsonSchemaSTACValidator
   :members:

SchemaUriMap
~~~~~~~~~~~~

A ``SchemaMapUri`` defines methods for mapping STAC versions, object types and extension ids to
schema URIs. A default implementation is included that uses known locations; however users
can provide their own schema URI maps in a :class:`~pystac.validation.JsonSchemaSTACValidator`
to modify the URIs used.

.. autoclass:: pystac.validation.SchemaUriMap
   :members:

.. autoclass:: pystac.validation.schema_uri_map.DefaultSchemaUriMap
   :members:


PySTAC Internal Classes
-----------------------

ResolvedObjectCache
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.cache.ResolvedObjectCache
   :members:
   :undoc-members:
