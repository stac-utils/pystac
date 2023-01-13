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

.. _installation_dependencies:

Dependencies
============

PySTAC requires Python >= 3.8. This project follows the recommendations of
`NEP-29 <https://numpy.org/neps/nep-0029-deprecation_policy.html>`__ in deprecating support
for Python versions. This means that users can expect support for Python 3.8 to be
removed from the ``main`` branch after Apr 14, 2023 and therefore from the next release
after that date.

As a foundational component of the Python STAC ecosystem used in a number of downstream
libraries, PySTAC aims to minimize its dependencies. As a result, the only dependency
for the basic PySTAC library is `python-dateutil
<https://dateutil.readthedocs.io/en/stable/>`__.

PySTAC also has the following extras, which can be optionally installed to provide
additional functionality:

* ``validation``

  Installs the additional `jsonschema
  <https://python-jsonschema.readthedocs.io/en/latest/>`__ dependency. When this
  dependency is installed, the :ref:`validation methods <validation_concepts>` may be
  used to validate STAC objects against the appropriate JSON schemas.

  To install:

  .. code-block:: bash

      pip install pystac[validation]

* ``orjson``

  Installs the additional `orjson <https://github.com/ijl/orjson>`__ dependency. When
  this dependency is installed, `orjson` will be used as the default JSON
  serialization/deserialization for all operations in PySTAC.

  To install:

  .. code-block:: bash

      pip install pystac[orjson]

Versions
========

To install a version of PySTAC that works with a specific versions of the STAC
specification, install the matching version of PySTAC from the following table.

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - PySTAC
     - STAC
   * - 1.x
     - 1.0.x
   * - 0.5.x
     - 1.0.0-beta.*
   * - 0.4.x
     - 0.9.x
   * - 0.3.x
     - 0.8.x

For instance, to work with STAC v0.9.x:

   .. code-block:: bash

      pip install pystac==0.4.0


STAC spec versions below 0.8 are not supported by PySTAC.
