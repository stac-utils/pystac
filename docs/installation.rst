Installation
############

Install from PyPi (recommended)
===============================

.. code-block:: bash

    pip install pystac

.. note::
    It is **highly recommended** that you install the ``aiofiles`` and ``httpx`` extras as well.

    .. code-block:: bash

        pip install pystac[aiofiles,httpx]

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
=============

As a foundational component of the Python STAC ecosystem used in a number of downstream
libraries, PySTAC aims to minimize its dependencies. As a result, the only dependency
for the basic PySTAC library is `python-dateutil
<https://dateutil.readthedocs.io/en/stable/>`__.

PySTAC also has the following extras, which can be optionally installed to provide
additional functionality:

* ``aiofiles`` and ``httpx``

  Installs the additional `aiofiles.open <https://pypi.org/project/aiofiles/>`__ and/or
  `httpx <https://www.python-httpx.org>`__ dependencies used by the
  :class:`~pystac.stac_io.DefaultStacIOAsync` default implementaiton of
  :class:`~pystac.StacIO`.

  .. note::
    To get the best performance, it is **highly recommended** that you either install
    these extras or create your own asynchronous :class:`~pystac.StacIO` implementation
    using alternative async I/O libraries.

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
