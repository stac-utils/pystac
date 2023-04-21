Contributing
============

A list of issues and ongoing work is available on the PySTAC `issues page
<https://github.com/stac-utils/pystac/issues>`_. If you want to contribute code, the best
way is to coordinate with the core developers via an issue or pull request conversation.

Development installation
^^^^^^^^^^^^^^^^^^^^^^^^
Fork PySTAC into your GitHub account. Then, clone the repo and install it locally with
pip as follows:

.. code-block:: bash

    git clone git@github.com:your_user_name/pystac.git
    cd  pystac
    pip install -e '.[dev]'

Testing
^^^^^^^
PySTAC runs tests using ``pytest``. You can find unit tests in the ``tests/``
directory.

Run a single test with:

.. code-block:: bash

    pytest tests/test_catalog.py::CatalogTest::test_create_and_read

or an entire folder using:

.. code-block:: bash

    pytest tests/extensions

or the entire project using:

.. code-block:: bash

    ./scripts/test

The last command will also check test coverage. To view the coverage report, you can run
`coverage report` (to view the report in the terminal) or `coverage html` (to generate
an HTML report that can be opened in a browser).

More details on using ``pytest`` are `here
<https://docs.pytest.org>`_.

Code quality checks
^^^^^^^^^^^^^^^^^^^

tl;dr: Run ``pre-commit install --overwrite`` to perform checks when committing, and
``./scripts/test`` to run all checks and tests.

PySTAC uses

- `ruff <https://github.com/charliermarsh/ruff>`_ for Python code linting
- `black <https://github.com/psf/black>`_ for Python code formatting
- `codespell <https://github.com/codespell-project/codespell/>`_ to check code for common misspellings
- `doc8 <https://github.com/pycqa/doc8>`__ for style checking on RST files in the docs
- `mypy <http://www.mypy-lang.org/>`_ for Python type annotation checks

Run all of these with ``pre-commit run --all-files`` or a single one using
``pre-commit run --all-files ID``, where ``ID`` is one of the command names above. For
example, to format all the Python code, run ``pre-commit run --all-files black``.

You can also install a Git pre-commit hook which will run the relevant linters and
formatters on any staged code when committing. This will be much faster than running on
all files, which is usually [#]_ only required when changing the pre-commit version or
configuration. Once installed you can bypass this check by adding the ``--no-verify``
flag to Git commit commands, as in ``git commit --no-verify``.

.. [#] In rare cases changes to one file might invalidate an unchanged file, such as
   when modifying the return type of a function used in another file.

Documentation
^^^^^^^^^^^^^

All new features or changes should include API documentation, in the form of
docstrings.  Additionally, if you are updating an extension version, check to
see if that extension is used in the ``examples/`` STAC objects at the top level
of the repository. If so, update the extension version, then re-run
``docs/quickstart.ipynb`` to include the new extension versions in the notebook
cell output.

Benchmarks
^^^^^^^^^^

PySTAC uses `asv <https://asv.readthedocs.io>`_ for benchmarking. Benchmarks are
defined in the ``./benchmarks`` directory. Due to the inherent uncertainty in
the environment of Github workflow runners, benchmarks are not executed in CI.
If your changes may affect performance, use the provided script to run the
benchmark suite locally. You'll need to install the benchmark dependencies
first. This script will compare your current ``HEAD`` with the **main** branch
and report any improvements or regressions.

.. code-block:: bash

    pip install -e '.[bench]'
    scripts/bench

The benchmark suite takes a while to run, and will report any significant
changes to standard output. For example, here's a benchmark comparison between
v1.0.0 and v1.6.1 (from `@gadomski's <https://github.com/gadomski>`_ computer)::

          before           after         ratio
        [eee06027]       [579c071b]
        <v1.0.0^0>       <v1.6.1^0>
    -        533±20μs         416±10μs     0.78  collection.CollectionBench.time_collection_from_file [gadomski/virtualenv-py3.10-orjson]
    -         329±8μs         235±10μs     0.72  collection.CollectionBench.time_collection_from_dict [gadomski/virtualenv-py3.10-orjson]
    -        332±10μs          231±4μs     0.70  collection.CollectionBench.time_collection_from_dict [gadomski/virtualenv-py3.10]
    -         174±4μs          106±2μs     0.61  item.ItemBench.time_item_from_dict [gadomski/virtualenv-py3.10]
    -         174±4μs          106±2μs     0.61  item.ItemBench.time_item_from_dict [gadomski/virtualenv-py3.10-orjson]
        before           after         ratio
        [eee06027]       [579c071b]
        <v1.0.0^0>       <v1.6.1^0>
    +        87.1±3μs          124±5μs     1.42  catalog.CatalogBench.time_catalog_from_dict [gadomski/virtualenv-py3.10]
    +        87.1±4μs          122±5μs     1.40  catalog.CatalogBench.time_catalog_from_dict [gadomski/virtualenv-py3.10-orjson]

When developing new benchmarks, you can run a shortened version of the benchmark suite:

.. code-block:: bash

    asv dev


CHANGELOG
^^^^^^^^^

PySTAC maintains a `changelog  <https://github.com/stac-utils/pystac/blob/develop/CHANGELOG.md>`_
to track changes between releases. All PRs should make a changelog entry unless
the change is trivial (e.g. fixing typos) or is entirely invisible to users who may
be upgrading versions (e.g. an improvement to the CI system).

For changelog entries, please link to the PR of that change. This needs to happen in a
few steps:

- Make a PR to PySTAC with your changes
- Record the link to the PR
- Push an additional commit to your branch with the changelog entry with the link to the
  PR.

For more information on changelogs and how to write a good entry, see `keep a changelog
<https://keepachangelog.com/en/1.0.0/>`_.


Style
^^^^^

In an effort to maintain a consistent codebase, PySTAC conforms to the following rules:

.. code-block:: python

   # DO
   from datetime import datetime

   # DON't
   import datetime
   import datetime as dt

The exception to this rule is when ``datetime`` is only imported for type checking and
using the class directly interferes with another variable name. In this case, in the
TYPE_CHECKING block you should do ``from datetime import datetime as Datetime``.
