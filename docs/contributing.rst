Contributing
============

A list of issues and ongoing work is available on the PySTAC `issues page <https://github.com/azavea/pystac/issues>`_. If you want to contribute code, the best way is to coordinate with the core developers via an issue or pull request conversation.

Development installation
^^^^^^^^^^^^^^^^^^^^^^^^
Fork PySTAC into your Github account. Then, clone the repo and install it locally with pip as follows:

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

More details on using ``unittest`` are `here <https://docs.python.org/3/library/unittest.html>`_.
