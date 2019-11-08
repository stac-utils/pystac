API Reference
=============

This API reference is auto-generated for the Python docstrings,
and organized by the section of the `STAC Spec <https://github.com/radiantearth/stac-spec/tree/v0.8.1>`_ they relate to, if related to a specific spec item.

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

Catalog Spec
------------

These classes are representations of the `Catalog Spec <https://github.com/radiantearth/stac-spec/tree/v0.8.1/catalog-spec>`_.

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

These classes are representations of the `Collection Spec <https://github.com/radiantearth/stac-spec/tree/v0.8.1/collection-spec>`_.

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

These classes are representations of the `Item Spec <https://github.com/radiantearth/stac-spec/tree/v0.8.1/item-spec>`_.

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

ItemCollection
~~~~~~~~~~~~~~

.. autoclass:: pystac.ItemCollection
   :members:
   :undoc-members:

EO Extension
------------

These classes are representations of the `EO Extension Spec <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/eo>`_.

EOItem
~~~~~~

.. autoclass:: pystac.EOItem
   :members:
   :undoc-members:
   :show-inheritance:

EOAsset
~~~~~~~

.. autoclass:: pystac.EOAsset
   :members:
   :undoc-members:
   :show-inheritance:

Band
~~~~

.. autoclass:: pystac.Band
   :members:
   :undoc-members:


Label Extension
---------------

These classes are representations of the `Label Extension Spec <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/label>`_.

LabelItem
~~~~~~~~~

.. autoclass:: pystac.LabelItem
   :members:
   :undoc-members:
   :show-inheritance:

LabelType
~~~~~~~~~

.. autoclass:: pystac.LabelType
   :members:
   :undoc-members:

LabelClasses
~~~~~~~~~~~~

.. autoclass:: pystac.LabelClasses
   :members:
   :undoc-members:

LabelOverview
~~~~~~~~~~~~~

.. autoclass:: pystac.LabelOverview
   :members:
   :undoc-members:

LabelCount
~~~~~~~~~~

.. autoclass:: pystac.LabelCount
   :members:
   :undoc-members:

LabelStatistics
~~~~~~~~~~~~~~~

.. autoclass:: pystac.LabelStatistics
   :members:
   :undoc-members:

Single File STAC Extension
--------------------------

These classes are representations of the `Single File STAC Extension <https://github.com/radiantearth/stac-spec/tree/v0.8.1/extensions/single-file-stac>`_.

SingleFileSTAC
~~~~~~~~~~~~~~

.. autoclass:: pystac.SingleFileSTAC
   :members:
   :undoc-members:

Serialization
-------------

PySTAC includes a ``pystac.serialization`` package for serialization concerns that
are used internally, but may also be useful to external tools.

merge_common_properties
~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pystac.serialization
   :members: merge_common_properties

indentify_stac_object
~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pystac.serialization
   :members: identify_stac_object

indentify_stac_object_type
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pystac.serialization
   :members: identify_stac_object_type


STACJSONDescription
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.serialization.STACJSONDescription
   :members:
   :undoc-members:

STACVersionRange
~~~~~~~~~~~~~~~~

.. autoclass:: pystac.serialization.STACVersionRange
   :members:
   :undoc-members:

STACObjectType
~~~~~~~~~~~~~~

.. autoclass:: pystac.serialization.STACObjectType
   :members:
   :undoc-members:

PySTAC Internal Classes
-----------------------

STACObject
~~~~~~~~~~

.. autoclass:: pystac.STACObject
   :members:
   :undoc-members:

ResolvedObjectCache
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pystac.resolved_object_cache.ResolvedObjectCache
   :members:
   :undoc-members:
