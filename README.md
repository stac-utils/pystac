## PySTAC
![Build Status](https://github.com/stac-utils/pystac/workflows/CI/badge.svg?branch=develop)
[![PyPI version](https://badge.fury.io/py/pystac.svg)](https://badge.fury.io/py/pystac)
[![Documentation](https://readthedocs.org/projects/pystac/badge/?version=latest)](https://pystac.readthedocs.io/en/latest/)
[![codecov](https://codecov.io/gh/stac-utils/pystac/branch/main/graph/badge.svg)](https://codecov.io/gh/stac-utils/pystac)
[![Gitter chat](https://badges.gitter.im/azavea/pystac.svg)](https://gitter.im/azavea/pystac)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

PySTAC is a library for working with [SpatialTemporal Asset Catalog](https://stacspec.org) in Python 3.

## Installation

PySTAC has a single dependency (`python-dateutil`).
PySTAC can be installed from pip or the source repository.

```bash
> pip install pystac
```

if you'd like to enable the validation feature utilizing the [jsonschema](https://pypi.org/project/jsonschema/) project, install with the optional `validation` requirements:


```bash
> pip install pystac[validation]
```

From source repository:

```bash
> git clone https://github.com/stac-utils/pystac.git
> cd pystac
> pip install .
```


#### Versions
To install a specific versions of STAC, install the matching version of pystac.

```bash
> pip install pystac==0.5.*
```

The table below shows the corresponding versions between pystac and STAC:

| pystac | STAC  |
| ------ | ----- |
| 1.x    | 1.0.x |
| 0.5.x  | 1.0.0-beta.* |
| 0.4.x  | 0.9.x |
| 0.3.x  | 0.8.x |

## Documentation

See the [documentation page](https://pystac.readthedocs.io/en/latest/) for the latest docs.

## Developing

To ensure development libraries are installed, install everything in `requirements-dev.txt`:

```
> pip install -r requirements-dev.txt
```

### Unit Tests

Unit tests are in the `tests` folder. To run unit tests, use `unittest`:

```
> python -m unittest discover tests
```

To run linters, code formatters, and test suites all together, use `test`:

```
> ./scripts/test
```

### Code quality checks

PySTAC uses [flake8](http://flake8.pycqa.org/en/latest/) and [yapf](https://github.com/google/yapf) for code formatting and style checks.

To run the flake8 style checks:

```
> flake8 pystac tests
```

To format code:

```
> yapf -ipr pystac tests
```

Note that you may have to use `yapf3` explicitly depending on your environment.

To check for spelling mistakes in modified files:

```
> git diff --name-only | xargs codespell -I .codespellignore -f
```

You can also run the `./scripts/test` script to check for linting, spelling, and run unit tests.

### Continuous Integration

CI will run the `scripts/test` script to check for code quality. If you have a Pull Request that fails CI, make sure to fix any linting, spelling or test issues reported by `scripts/test`.

### Documentation

To build and develop the documentation locally, make sure sphinx is available (which is installed with `requirements-dev.txt`), and use the Makefile in the docs folder:

```
> cd docs
> make html
> make livehtml
```

> Note: You will see some warnings along the lines of
> ```
> WARNING: duplicate object description of pystac.Collection.id,
> other instance in api, use :noindex: for one of them
> ```
> for some of the
> classes. This is expected due to [sphinx-doc/sphinx#8664](https://github.com/sphinx-doc/sphinx/issues/8664).

Use 'make' without arguments to see a list of available commands.

__Note__: `nbsphinx` requires that a local `pystac` is installed; use `pip install -e .`.



## Running the quickstart and tutorials

There is a quickstart and tutorials written as jupyter notebooks in the `docs/tutorials` folder.
To run the notebooks, run a jupyter notebook with the `docs` directory as the notebook directory:

```
> PYTHONPATH=`pwd`:$PYTHONPATH jupyter notebook --ip 0.0.0.0 --port 8888 --notebook-dir=docs
```

You can then navigate to the notebooks and execute them.

Requires [Jupyter](https://jupyter.org/) be installed.
