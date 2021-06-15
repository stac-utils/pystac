API Reference
=============

This API reference is auto-generated for the Python docstrings,
and organized by the section of the :stac-spec:`STAC Spec <>` they relate to, if related
to a specific spec item.

pystac
------

.. automodule:: pystac
   :members: read_file, write_file, read_dict, set_stac_version, get_stac_version

STACObject
----------

STACObject is the base class for :class:`Catalog <pystac.Catalog>`, :class:`Collection
<pystac.Collection>` and :class:`Item <pystac.Item>`, and contains a variety of useful
methods for dealing with links, copying objects, accessing extensions, and reading and
writing files. You shouldn't use STACObject directly, but instead access this
functionality through the implementing classes.

.. autoclass:: pystac.STACObject
   :members:
   :inherited-members:
   :undoc-members:

.. autoclass:: pystac.STACObjectType
   :members:
   :undoc-members:


Catalog Spec
------------

These classes are representations of the :stac-spec:`Catalog Spec <catalog-spec>`.

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

These classes are representations of the :stac-spec:`Collection Spec <collection-spec>`.

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

Summaries
~~~~~~~~~

.. autoclass:: pystac.Summaries
   :members:
   :undoc-members:

Item Spec
---------

These classes are representations of the :stac-spec:`Item Spec <item-spec>`.

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

ItemCollection
--------------
Represents a GeoJSON FeatureCollection in which all Features are STAC Items

.. autoclass:: pystac.ItemCollection
   :members:
   :show-inheritance:

Links
-----

Catalogs, Collections and Items have links, which allow users to crawl catalogs.

Link
~~~~

.. autoclass:: pystac.Link
   :members:
   :undoc-members:

MediaType
~~~~~~~~~

.. autoclass:: pystac.MediaType
   :members:
   :undoc-members:

RelType
~~~~~~~

.. autoclass:: pystac.RelType
   :members:
   :undoc-members:

IO
--

STAC_IO
~~~~~~~

STAC_IO is the utility mechanism that PySTAC uses for reading and writing. Users of
PySTAC can hook into PySTAC by overriding members to utilize their own IO methods.

.. autoclass:: pystac.stac_io.STAC_IO
   :members:
   :undoc-members:

Layout
------

These classes are used to set the HREFs of a STAC according to some layout.
The templating functionality is also used when generating subcatalogs based on
a template.

Templating
~~~~~~~~~~

.. autoclass:: pystac.layout.LayoutTemplate
   :members:

.. autoclass:: pystac.layout.TemplateError

HREF Layout Strategies
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.layout.BestPracticesLayoutStrategy

.. autoclass:: pystac.layout.TemplateLayoutStrategy

.. autoclass:: pystac.layout.CustomLayoutStrategy

Errors
------

STACError
~~~~~~~~~

.. autoclass:: pystac.STACError

ExtensionTypeError
~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.ExtensionTypeError

Extensions
----------

Base Classes
------------

Abstract base classes that should be inherited to implement specific extensions.

SummariesExtension
~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.base.SummariesExtension
   :members:

PropertiesExtension
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.base.PropertiesExtension
   :members:
   :show-inheritance:

ExtensionManagementMixin
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.base.ExtensionManagementMixin
   :members:
   :show-inheritance:

Electro-Optical Extension
-------------------------

These classes are representations of the :stac-ext:`EO Extension Spec <eo>`.

Band
~~~~

.. autoclass:: pystac.extensions.eo.Band
   :members:
   :undoc-members:

EOExtension
~~~~~~~~~~~

.. autoclass:: pystac.extensions.eo.EOExtension
   :members:
   :undoc-members:
   :show-inheritance:

ItemEOExtension
~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.eo.ItemEOExtension
   :members:
   :undoc-members:
   :show-inheritance:

AssetEOExtension
~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.eo.AssetEOExtension
   :members:
   :undoc-members:
   :show-inheritance:

SummariesEOExtension
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.eo.SummariesEOExtension
   :members:
   :undoc-members:
   :show-inheritance:

Label Extension
---------------

These classes are representations of the :stac-ext:`Label Extension Spec <label>`.

LabelItemExt
~~~~~~~~~~~~

**TEMPORARILY REMOVED**

.. .. autoclass:: pystac.extensions.label.LabelItemExt
..    :members:
..    :undoc-members:
..    :show-inheritance:

LabelRelType
~~~~~~~~~~~~

.. autoclass:: pystac.extensions.label.LabelRelType
   :members:
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

Implements the :stac-ext:`Point Cloud Extension <pointcloud>`.

PointcloudItemExt
~~~~~~~~~~~~~~~~~

**TEMPORARILY REMOVED**

.. .. autoclass:: pystac.extensions.pointcloud.PointcloudItemExt
..    :members:
..    :undoc-members:
..    :show-inheritance:

Projection Extension
--------------------

These classes are representations of the :stac-ext:`Projection Extension Spec
<projection>`.

ProjectionExtension
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.projection.ProjectionExtension
   :members:
   :show-inheritance:

ItemProjectionExtension
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.projection.ItemProjectionExtension
   :members:
   :show-inheritance:

AssetProjectionExtension
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.projection.AssetProjectionExtension
   :members:
   :show-inheritance:

Scientific Extension
--------------------

These classes are representations of the :stac-ext:`Scientific Extension Spec
<scientific>`.

Publication
~~~~~~~~~~~

.. autoclass:: pystac.extensions.scientific.Publication
   :members:
   :show-inheritance:

ScientificExtension
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.scientific.ScientificExtension
   :members:
   :show-inheritance:

CollectionScientificExtension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.scientific.CollectionScientificExtension
   :members:
   :show-inheritance:

ItemScientificExtension
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.scientific.ItemScientificExtension
   :members:
   :show-inheritance:

Timestamps Extension
--------------------

Implements the :stac-ext:`Timestamps Extension <timestamps>`.

TimestampsItemExt
~~~~~~~~~~~~~~~~~

**TEMPORARILY REMOVED**

.. .. autoclass:: pystac.extensions.timestamps.TimestampsItemExt
..    :members:
..    :undoc-members:
..    :show-inheritance:

SAR Extension
-------------

Implements the :stac-ext:`SAR Extension <sar>`.

SarItemExt
~~~~~~~~~~~~~~~~~~~~~~~~

**TEMPORARILY REMOVED**

.. .. autoclass:: pystac.extensions.sar.SarItemExt
..    :members:
..    :undoc-members:
..    :show-inheritance:

SAT Extension
-------------

Implements the :stac-ext:`SAT Extension <sat>`.

SatItemExt
~~~~~~~~~~~~~~~~~~~~~~~~

**TEMPORARILY REMOVED**

.. .. autoclass:: pystac.extensions.sar.SatItemExt
..    :members:
..    :undoc-members:
..    :show-inheritance:

Single File STAC Extension
--------------------------

These classes are representations of the :stac-ext:`Single File STAC Extension
<single-file-stac>`.

**TEMPORARILY REMOVED**

.. .. automodule:: pystac.extensions.single_file_stac
..    :members: create_single_file_stac

SingleFileSTACCatalogExt
~~~~~~~~~~~~~~~~~~~~~~~~

**TEMPORARILY REMOVED**

.. .. autoclass:: pystac.extensions.single_file_stac.SingleFileSTACCatalogExt
..    :members:
..    :undoc-members:

Version Extension
-----------------

Implements the :stac-ext:`Versioning Indicators Extension <version>`.

VersionRelType
~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.version.VersionRelType
   :members:
   :show-inheritance:

VersionExtension
~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.version.VersionExtension
   :members:
   :show-inheritance:

CollectionVersionExtension
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.version.CollectionVersionExtension
   :members:
   :show-inheritance:

ItemVersionExtension
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.version.ItemVersionExtension
   :members:
   :show-inheritance:

View Geometry Extension
-----------------------

These classes are representations of the :stac-ext:`View Geometry Extension Spec
<view>`.

ViewExtension
~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.view.ViewExtension
   :members:
   :show-inheritance:

ItemViewExtension
~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.view.ItemViewExtension
   :members:
   :show-inheritance:

AssetViewExtension
~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.view.AssetViewExtension
   :members:
   :show-inheritance:

Serialization
-------------

PySTAC includes a ``pystac.serialization`` package for serialization concerns that
are used internally, but may also be useful to external tools.

Identification
~~~~~~~~~~~~~~

.. automodule:: pystac.serialization
   :members: identify_stac_object

.. .. autoclass:: pystac.serialization.STACJSONDescription
..    :members:
..    :undoc-members:

.. autoclass:: pystac.serialization.STACVersionRange
   :members:
   :undoc-members:

.. .. autoclass:: pystac.serialization.STACVersionID
..    :members:
..    :undoc-members:


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
   :members: validate, validate_dict, validate_all, set_validator

STACValidator
~~~~~~~~~~~~~

.. autoclass:: pystac.validation.STACValidator
   :members:

.. autoclass:: pystac.validation.JsonSchemaSTACValidator
   :members:

SchemaUriMap
~~~~~~~~~~~~

A ``SchemaMapUri`` defines methods for mapping STAC versions, object types and extension
ids to schema URIs. A default implementation is included that uses known locations;
however users can provide their own schema URI maps in a
:class:`~pystac.validation.JsonSchemaSTACValidator` to modify the URIs used.

.. .. autoclass:: pystac.validation.SchemaUriMap
..    :members:

.. autoclass:: pystac.validation.schema_uri_map.DefaultSchemaUriMap
   :members:


PySTAC Internal Classes
-----------------------

ResolvedObjectCache
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.cache.ResolvedObjectCache
   :members:
   :undoc-members:
