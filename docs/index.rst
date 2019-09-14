PySTAC Documentation
#########################

PySTAC is a library for working with `SpatioTemporal Asset Catalogs (STAC) <https://stacspec.org/>`_.

Requirements
============
* `Python 3 <https://www.python.org/>`_

STAC Versions
=============

* 0.2 -> STAC Version 0.8

Standard pip install
====================

.. code-block:: bash

   pip install pystac

PySTAC Details
==============

TODO: Points to make:

* Reads and writes STAC version 0.8. Future versions will read older versions of STAC, but always write one version.
* Allows in-memory manipulations of STAC catalogs.
* Allows users to extend the IO of STAC metadata to provide support e.g. cloud providers.
* Allows easy iteration over STAC items.


Acknowledgements
================

This library builds on the concepts of `sat-stac <https://github.com/sat-utils/sat-stac>`_.

.. toctree::
   :hidden:
   :maxdepth: 2

   tutorials
   contributing
