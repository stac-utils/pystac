PySTAC Documentation
####################

PySTAC is a library for working with `SpatioTemporal Asset Catalogs (STAC) <https://stacspec.org/>`_.

Requirements
============
* `Python 3 <https://www.python.org/>`_

STAC Versions
=============

* 0.5 -> STAC Version 1.0
* 0.4 -> STAC Version 0.9
* 0.3 -> STAC Version 0.8

Standard pip install
====================

.. code-block:: bash

   pip install pystac

PySTAC Features
===============

* Reads and writes STAC version 0.8. Future versions will read older versions of STAC, but always write one version.
* Allows in-memory manipulations of STAC catalogs.
* Allows users to extend the IO of STAC metadata to provide support e.g. cloud providers.
* Allows easy iteration over STAC objects. STAC objects are only read in when needed.
* Allows users to easily write "absolute published", "relative published" and "self-contained" catalogs as `described in the best practices documentation <https://github.com/radiantearth/stac-spec/blob/v0.8.1/best-practices.md#use-of-links>`_.

Acknowledgments
================

This library builds on the code and concepts of `sat-stac <https://github.com/sat-utils/sat-stac>`_.

Table of Contents
=================

.. toctree::
   :maxdepth: 2

   quickstart
   concepts
   api
   tutorials
   contributing
