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

CHANGELOG
^^^^^^^^^

PySTAC maintains a `changelog  <https://github.com/stac-utils/pystac/blob/develop/CHANGELOG.md>`_
to track changes between releases. All PRs should make a changelog entry unless
the change is trivial (e.g. fixing typos) or is entirely invisible to users who may
be upgrading versions (e.g. an improvement to the CI system).

For changelog entries, please link to the PR of that change. This needs to happen in a few steps:

- Make a PR to PySTAC with your changes
- Record the link to the PR
- Push an additional commit to your branch with the changelog entry with the link to the PR.

For more information on changelogs and how to write a good entry, see `keep a changelog <https://keepachangelog.com/en/1.0.0/>`_