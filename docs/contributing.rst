Contributing
============

A list of issues and ongoing work is available on the PySTAC `issues page <https://github.com/azavea/pystac/issues>`_. If you want to contribute code, the best way is to coordinate with the core developers via an issue or pull request conversation.

Development installation
^^^^^^^^^^^^^^^^^^^^^^^^
Fork PySTAC into your GitHub account. Then, clone the repo and install it locally with pip as follows:

.. code-block:: bash

	$ git clone git@github.com:your_user_name/pystac.git
	$ cd  pystac
	$ pip install -e .

Testing
^^^^^^^
PySTAC runs tests using ``unittest``. You can find unit tests in the ``tests/`` directory.

Run a single test with:

.. code-block:: bash

	python -m unittest tests/test_catalog.py

or an entire folder using:

.. code-block:: bash

	python -m unittest discover -v -s tests/

or the entire project using:

.. code-block:: bash

	./scripts/test

More details on using ``unittest`` are `here <https://docs.python.org/3/library/unittest.html>`_.

Code quality checks
^^^^^^^^^^^^^^^^^^^

PySTAC uses `flake8 <http://flake8.pycqa.org/en/latest/>`_ and `yapf <https://github.com/google/yapf>`_ for code formatting and style checks.

To run the flake8 style checks:

.. code-block:: bash

   > flake8 pystac
   > flake8 tests

To format code:

.. code-block:: bash

   > yapf -ipr pystac
   > yapf -ipr tests

You can also run the ``./scripts/test`` script to check flake8 and yapf.
