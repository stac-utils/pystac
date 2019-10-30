Concepts
########

This page will give an overview of some important concepts to understand when working with PySTAC.

Reading STACs
=============

.. code-block:: python

   from pystac import Catalog

   catalog = Catalog.from_file('/some/example/catalog.json')

To see how to hook into PySTAC for reading from alternate URIs such as cloud object storage,
see :ref:`using stac_io`

Writing STACs
=============

.. code-block:: python

   from pystac import (Catalog, CatalogType)

   catalog = Catalog.from_file('/some/example/catalog.json')
   catalog.normalize_hrefs('/some/copy/')
   catalog.save(catalog_type=CatalogType.SELF_CONTAINED)

   copycat = Catalog.from_file('/some/copy/catalog.json')


Setting HREFs from a root
-------------------------

TKTK

Catalog Types
-------------

TKTK

Relative vs Absolute Link HREFs
-------------------------------

TKTK

Including a ``self`` link
-------------------------

TKTK

.. _using stac_io:

Using STAC_IO
-------------

TKTK

Manipulating STACs
==================

TKTK

Walking the STAC
----------------

TKTK

Mapping over Items
------------------

TKTK

Copying STACs in-memory
=======================

TKTK

Lazy resolution of STAC items
=============================

TKTK
