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

ProviderRole
~~~~~~~~~~~~

.. autoclass:: pystac.ProviderRole
   :members:
   :undoc-members:
   :show-inheritance:

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

StacIO
~~~~~~

.. autoclass:: pystac.StacIO
   :members:
   :undoc-members:

DefaultStacIO
~~~~~~~~~~~~~

.. autoclass:: pystac.stac_io.DefaultStacIO
   :members:
   :show-inheritance:

DuplicateKeyReportingMixin
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.stac_io.DuplicateKeyReportingMixin
   :members:
   :show-inheritance:

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

STACTypeError
~~~~~~~~~~~~~

.. autoclass:: pystac.STACTypeError

DuplicateObjectKeyError
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.DuplicateObjectKeyError

ExtensionAlreadyExistsError
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.ExtensionAlreadyExistsError

ExtensionTypeError
~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.ExtensionTypeError

ExtensionNotImplemented
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.ExtensionNotImplemented

ExtensionTypeError
~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.ExtensionTypeError

RequiredPropertyMissing
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.RequiredPropertyMissing

STACValidationError
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.STACValidationError


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

Datacube Extension
------------------

These classes are representations of the :stac-ext:`EO Extension Spec <eo>`.

DimensionType
~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.datacube.DimensionType
   :members:
   :undoc-members:
   :show-inheritance:

HorizontalSpatialDimensionAxis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.datacube.HorizontalSpatialDimensionAxis
   :members:
   :undoc-members:
   :show-inheritance:

VerticalSpatialDimensionAxis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.datacube.VerticalSpatialDimensionAxis
   :members:
   :undoc-members:
   :show-inheritance:

Dimension
~~~~~~~~~

.. autoclass:: pystac.extensions.datacube.Dimension
   :members:
   :show-inheritance:

HorizontalSpatialDimension
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.datacube.HorizontalSpatialDimension
   :members:
   :show-inheritance:
   :inherited-members:

VerticalSpatialDimension
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.datacube.VerticalSpatialDimension
   :members:
   :show-inheritance:
   :inherited-members:

TemporalSpatialDimension
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.datacube.TemporalSpatialDimension
   :members:
   :show-inheritance:
   :inherited-members:

AdditionalDimension
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.datacube.AdditionalDimension
   :members:
   :show-inheritance:
   :inherited-members:

DatacubeExtension
~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.datacube.DatacubeExtension
   :members:
   :show-inheritance:
   :inherited-members:

CollectionDatacubeExtension
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.datacube.CollectionDatacubeExtension
   :members:
   :show-inheritance:
   :inherited-members:

ItemDatacubeExtension
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.datacube.ItemDatacubeExtension
   :members:
   :show-inheritance:
   :inherited-members:

AssetDatacubeExtension
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.datacube.AssetDatacubeExtension
   :members:
   :show-inheritance:
   :inherited-members:

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

File Info Extension
-------------------

These classes are representations of the :stac-ext:`File Info Extension Spec <file>`.

ByteOrder
~~~~~~~~~

.. autoclass:: pystac.extensions.file.ByteOrder
   :members:
   :show-inheritance:
   :undoc-members:

MappingObject
~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.file.MappingObject
   :members:

FileExtension
~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.file.FileExtension
   :members:
   :show-inheritance:
   :undoc-members:

Item Assets Extension
---------------------

These classes are representations of the :stac-ext:`Item Assets Extension Spec
<item-assets>`.

AssetDefinition
~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.item_assets.AssetDefinition
   :members:
   :undoc-members:
   :show-inheritance:

ItemAssetsExtension
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.item_assets.ItemAssetsExtension
   :members:
   :show-inheritance:

Label Extension
---------------

These classes are representations of the :stac-ext:`Label Extension Spec <label>`.

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

LabelExtension
~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.label.LabelExtension
   :members:
   :undoc-members:
   :show-inheritance:

Pointcloud Extension
--------------------

These classes are representations of the :stac-ext:`Pointcloud Extension Spec
<pointcloud>`.

PhenomenologyType
~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.pointcloud.PhenomenologyType
   :members:
   :undoc-members:
   :show-inheritance:

SchemaType
~~~~~~~~~~

.. autoclass:: pystac.extensions.pointcloud.SchemaType
   :members:
   :undoc-members:
   :show-inheritance:

Schema
~~~~~~

.. autoclass:: pystac.extensions.pointcloud.Schema
   :members:
   :inherited-members:
   :show-inheritance:

Statistic
~~~~~~~~~

.. autoclass:: pystac.extensions.pointcloud.Statistic
   :members:
   :inherited-members:
   :show-inheritance:

PointcloudExtension
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.pointcloud.PointcloudExtension
   :members:
   :inherited-members:
   :show-inheritance:

ItemPointcloudExtension
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.pointcloud.ItemPointcloudExtension
   :members:
   :show-inheritance:

AssetPointcloudExtension
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.pointcloud.AssetPointcloudExtension
   :members:
   :show-inheritance:

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

Raster Extension
----------------

DataType
~~~~~~~~

.. autoclass:: pystac.extensions.raster.DataType
   :members:
   :undoc-members:
   :show-inheritance:

Statistics
~~~~~~~~~~

.. autoclass:: pystac.extensions.raster.Statistics
   :members:

Histogram
~~~~~~~~~

.. autoclass:: pystac.extensions.raster.Histogram
   :members:

RasterBand
~~~~~~~~~~

.. autoclass:: pystac.extensions.raster.RasterBand
   :members:

RasterExtension
~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.raster.RasterExtension
   :members:
   :show-inheritance:
   :inherited-members:

SAR Extension
-------------
These classes are representations of the :stac-ext:`SAR Extension Spec
<sar>`.

FrequencyBand
~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.sar.FrequencyBand
   :members:
   :undoc-members:
   :show-inheritance:

Polarization
~~~~~~~~~~~~

.. autoclass:: pystac.extensions.sar.Polarization
   :members:
   :undoc-members:
   :show-inheritance:

ObservationDirection
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.sar.ObservationDirection
   :members:
   :undoc-members:
   :show-inheritance:

SarExtension
~~~~~~~~~~~~

.. autoclass:: pystac.extensions.sar.SarExtension
   :members:
   :show-inheritance:
   :inherited-members:

ItemSarExtension
~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.sar.ItemSarExtension
   :members:
   :show-inheritance:
   :inherited-members:

AssetSarExtension
~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.sar.AssetSarExtension
   :members:
   :show-inheritance:
   :inherited-members:

Satellite Extension
-------------------
These classes are representations of the :stac-ext:`Satellite Extension Spec
<sat>`.

OrbitState
~~~~~~~~~~

.. autoclass:: pystac.extensions.sat.OrbitState
   :members:
   :show-inheritance:
   :undoc-members:

SatExtension
~~~~~~~~~~~~

.. autoclass:: pystac.extensions.sat.SatExtension
   :members:
   :show-inheritance:

ItemSatExtension
~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.sat.ItemSatExtension
   :members:
   :show-inheritance:

AssetSatExtension
~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.sat.AssetSatExtension
   :members:
   :show-inheritance:

SummariesSatExtension
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.sat.SummariesSatExtension
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

These classes are representations of the :stac-ext:`Timestamps Extension Spec
<timestamps>`.

TimestampsExtension
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.timestamps.TimestampsExtension
   :members:
   :show-inheritance:

ItemTimestampsExtension
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.timestamps.ItemTimestampsExtension
   :members:
   :show-inheritance:

AssetTimestampsExtension
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.extensions.timestamps.AssetTimestampsExtension
   :members:
   :show-inheritance:

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
