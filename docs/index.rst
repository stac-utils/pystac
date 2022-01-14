PySTAC Documentation
####################

PySTAC is a library for working with `SpatioTemporal Asset Catalogs (STAC) <https://stacspec.org/>`_ in `Python 3 <https://www.python.org/>`_. Some nice features of PySTAC are:

* Reading and writing STAC version 1.0. Future versions will read older versions of STAC, but always write the latest
  supported version. See :ref:`stac_version_support` for details.
* In-memory manipulations of STAC catalogs.
* Extend the I/O of STAC metadata to provide support for other platforms (e.g. cloud providers).
* Easy, efficient crawling of STAC catalogs. STAC objects are only read in when needed.
* Easily write "absolute published", "relative published" and "self-contained" catalogs as :stac-spec:`described 
  in the best practices documentation <best-practices.md#use-of-links>`.

.. panels::
    
    Get Started
    ^^^^^^^^^^^

    * :doc:`installation`: Instructions for installing the basic package as well as extras.
    * :doc:`quickstart`: Jupyter notebook tutorial on using PySTAC for reading & writing STAC catalogs.

    ---

    Go Deeper
    ^^^^^^^^^

    * :doc:`concepts`: Overview of how various concepts and structures from the STAC Specification are implemented within PySTAC.
    * :doc:`tutorials`: In-depth tutorials on using PySTAC for a number of different applications.
    * :doc:`api`: Detailed API documentation of PySTAC classes, methods, and functions.

Acknowledgments
================

This library builds on the code and concepts of `sat-stac <https://github.com/sat-utils/sat-stac>`_.

.. toctree::
   :maxdepth: 2
   :hidden:

   installation
   quickstart
   concepts
   api
   tutorials
   contributing
