# PySTAC

[![Build Status](https://github.com/stac-utils/pystac/actions/workflows/continuous-integration.yml/badge.svg)](https://github.com/stac-utils/pystac/actions/workflows/continuous-integration.yml)
[![PyPI version](https://badge.fury.io/py/pystac.svg)](https://badge.fury.io/py/pystac)
[![Conda (channel only)](https://img.shields.io/conda/vn/conda-forge/pystac)](https://anaconda.org/conda-forge/pystac)
[![Documentation](https://readthedocs.org/projects/pystac/badge/?version=latest)](https://pystac.readthedocs.io/en/latest/)
[![codecov](https://codecov.io/gh/stac-utils/pystac/branch/main/graph/badge.svg)](https://codecov.io/gh/stac-utils/pystac)
[![Gitter](https://badges.gitter.im/SpatioTemporal-Asset-Catalog/python.svg)](https://gitter.im/SpatioTemporal-Asset-Catalog/python?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

PySTAC is a library for working with the [SpatioTemporal Asset Catalog](https://stacspec.org) specification in Python 3.

## Installation

### Install from PyPi (recommended)

```shell
python -m pip install pystac
```

If you would like to enable the validation feature utilizing the
[jsonschema](https://pypi.org/project/jsonschema/) project, install with the optional
`validation` requirements:

```shell
python -m pip install 'pystac[validation]'
```

If you would like to use the [`orjson`](https://pypi.org/project/orjson/) instead of the
standard `json` library for JSON serialization/deserialization, install with the
optional `orjson` requirements:

```shell
python -m pip install 'pystac[orjson]'
```

If you would like to use a custom `RetryStacIO` class for automatically retrying
network requests when reading with PySTAC, you'll need
[`urllib3`](https://urllib3.readthedocs.io/en/stable/):

```shell
python -m pip install 'pystac[urllib3]'
```

If you are using jupyter notebooks and want to enable pretty display of pystac
objects you'll need [`jinja2`](https://pypi.org/project/Jinja2/)

```shell
python -m pip install 'pystac[jinja2]'
```

### Install from source

```shell
git clone https://github.com/stac-utils/pystac.git
cd pystac
python -m pip install .
```

See the [installation page](https://pystac.readthedocs.io/en/latest/installation.html)
for more options.

## Documentation

See the [documentation page](https://pystac.readthedocs.io/en/latest/) for the latest docs.

## Developing

See [contributing docs](https://pystac.readthedocs.io/en/latest/contributing.html)
for details on contributing to this project.

## Running the quickstart and tutorials

There is a quickstart and tutorials written as jupyter notebooks in the `docs/tutorials` folder.
To run the notebooks, run a jupyter notebook with the `docs` directory as the notebook directory:

```shell
jupyter notebook --ip 0.0.0.0 --port 8888 --notebook-dir=docs
```

You can then navigate to the notebooks and execute them.

Requires [Jupyter](https://jupyter.org/) be installed.
