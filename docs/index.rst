PySTAC Documentation
####################

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

PySTAC Features
===============

* Reads and writes STAC version 0.8. Future versions will read older versions of STAC, but always write one version.
* Allows in-memory manipulations of STAC catalogs.
* Allows users to extend the IO of STAC metadata to provide support e.g. cloud providers.
* Allows easy iteration over STAC objects. Stac objects are only read in when needed.
* Allows users to easily write "absolute published", "relative published" and "self-contained" catalogs as `described in the best practices documentation <https://github.com/radiantearth/stac-spec/blob/v0.8.0/best-practices.md#use-of-links>`_.


Acknowledgements
================

This library builds on the code and concepts of `sat-stac <https://github.com/sat-utils/sat-stac>`_.

.. toctree::
   :hidden:
   :maxdepth: 2

   concepts
   api
   tutorials
   contributing
