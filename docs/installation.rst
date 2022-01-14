Installation
############

Install from PyPi (recommended)
===============================

.. code-block:: bash

    pip install pystac

Install from conda-forge
========================

.. code-block:: bash
    
    conda install -c conda-forge pystac

Install from source
===================

.. code-block:: bash

    pip install git+https://github.com/stac-utils/pystac.git

Dependencies
=============

As a foundational component of the Python STAC ecosystem used in a number of downstream libraries, PySTAC aims to
minimize its dependencies. As a result, the only dependency for the basic PySTAC library is 
`python-dateutil <https://dateutil.readthedocs.io/en/stable/>`__. 

PySTAC also has the following extras, which can be optionally installed to provide additional functionality:

* ``validation``

  Installs the additional `jsonschema <https://python-jsonschema.readthedocs.io/en/latest/>`__ dependency. When this
  dependency is installed, the :ref:`validation methods <validation_concepts>` may be used to validate STAC objects
  against the appropriate JSON schemas.

  To install:

  .. code-block:: bash
  
      pip install pystac[validation]

* ``orjson``

  Installs the additional `orjson <https://github.com/ijl/orjson>`__ dependency. When this dependency is installed,
  `orjson` will be used as the default JSON serialization/deserialization for all operations in PySTAC.

  To install:

  .. code-block:: bash
      
      pip install pystac[orjson]