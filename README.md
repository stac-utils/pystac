## PySTAC
[![Build Status](https://api.travis-ci.org/azavea/pystac.svg?branch=develop)](https://travis-ci.org/azavea/pystac)
[![PyPI version](https://badge.fury.io/py/pystac.svg)](https://badge.fury.io/py/pystac)
[![Documentation](https://readthedocs.org/projects/pystac/badge/?version=latest)](https://pystac.readthedocs.io/en/latest/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

PySTAC is a library for working with [SpatialTemporal Asset Catalog](https://stacgeo.org) in Python 3.

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
> pip install pystac==0.2.0
```

The table below shows the corresponding versions between pystac and STAC:

| pystac | STAC  |
| ------ | ----  |
| 0.2.x  | 0.8.x |

## Documentation

See the [documentation page](https://pystac.readthedocs.io/en/latest/) for the latest docs.

## Developing

To ensure development libraries are installed, install everything in `requirements-dev.txt`:

```
> pip install -r requirements-dev.txt
```

Unit tests are in the `tests` folder. To run unit tests, use `unittest`:

```
> python -m unittest discover tests
```

## Running the tutorials

There are tutorials written as jupyter notebooks in the `tutorials` folder. To run them, run a jupyter notebook with the `tutorials` directory as the notebook directory:

```
> PYTHONPATH=`pwd`:$PYTHONPATH jupyter notebook --ip 0.0.0.0 --port 8888 --notebook-dir=tutorials
```

Requires [Jupyter](https://jupyter.org/) be installed.
