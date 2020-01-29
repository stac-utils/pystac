## PySTAC
[![Build Status](https://api.travis-ci.org/azavea/pystac.svg?branch=develop)](https://travis-ci.org/azavea/pystac)
[![PyPI version](https://badge.fury.io/py/pystac.svg)](https://badge.fury.io/py/pystac)
[![Documentation](https://readthedocs.org/projects/pystac/badge/?version=latest)](https://pystac.readthedocs.io/en/latest/)
[![Gitter chat](https://badges.gitter.im/azavea/pystac.svg)](https://gitter.im/azavea/pystac)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

PySTAC is a library for working with [SpatialTemporal Asset Catalog](https://stacspec.org) in Python 3.

## Installation

PySTAC has a single dependency (`python-dateutil`).
PySTAC can be installed from pip or the source repository.

```bash
> pip install pystac
```

From source repository:

```bash
> git clone https://github.com/azavea/pystac.git
> cd pystac
> pip install .
```


#### Versions
To install a specific versions of STAC, install the matching version of pystac.

```bash
> pip install pystac==0.3.*
```

The table below shows the corresponding versions between pystac and STAC:

| pystac | STAC  |
| ------ | ----  |
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

### Code quality checks

PySTAC uses [flake8](http://flake8.pycqa.org/en/latest/) and [yapf](https://github.com/google/yapf) for code formatting and style checks.

To run the flake8 style checks:

```
> flake8 pystac
> flake8 tests
```

To format code:

```
> yapf -ipr pystac
> yapf -ipr tests
```

You could also run the `.travis/style_checks` script to check flake8 and yapf.

### Documentation

To build and develop the documentation locally, make sure sphinx is available (which is installed with `requirements-dev.txt`), and use the Makefile in the docs folder:

```
> cd docs
> make html
> make livehtml
```

Use 'make' without arguments to see a list of available commands.

__Note__: `nbsphinx` requires that a local `pystac` is installed; use `pip install -e .`.



## Runing the quickstart and tutorials

There is a quickstart and tutorials written as jupyter notebooks in the `docs/tutorials` folder.
To run the notebooks, run a jupyter notebook with the `docs` directory as the notebook directory:

```
> PYTHONPATH=`pwd`:$PYTHONPATH jupyter notebook --ip 0.0.0.0 --port 8888 --notebook-dir=docs
```

You can then navigate to the notebooks and execute them.

Requires [Jupyter](https://jupyter.org/) be installed.
