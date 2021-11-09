## PySTAC
![Build Status](https://github.com/stac-utils/pystac/workflows/CI/badge.svg?branch=main)
[![PyPI version](https://badge.fury.io/py/pystac.svg)](https://badge.fury.io/py/pystac)
[![Documentation](https://readthedocs.org/projects/pystac/badge/?version=latest)](https://pystac.readthedocs.io/en/latest/)
[![codecov](https://codecov.io/gh/stac-utils/pystac/branch/main/graph/badge.svg)](https://codecov.io/gh/stac-utils/pystac)
[![Gitter](https://badges.gitter.im/SpatioTemporal-Asset-Catalog/python.svg)](https://gitter.im/SpatioTemporal-Asset-Catalog/python?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

PySTAC is a library for working with [SpatioTemporal Asset Catalog](https://stacspec.org) in Python 3.

## Installation

PySTAC requires Python >= 3.7. This project follows the recommendations of
[NEP-29](https://numpy.org/neps/nep-0029-deprecation_policy.html) in deprecating support
for Python versions. This means that users can expect support for Python 3.7 to be
removed from the `main` branch after Dec 26, 2021 and therefore from the next release
after that date.

Note that while we support Python 3.10.\*, wheels for the `orjson` library are not always immediately available for all
platforms. If you install PySTAC with the `orjson` extra, you may need to have the Rust toolchain installed (e.g. via [rustup](https://rustup.rs/)) in order to
build the package from source.

PySTAC has a single required dependency (`python-dateutil`).
PySTAC can be installed from pip or the source repository.

```bash
> pip install pystac
```

If you would like to enable the validation feature utilizing the
[jsonschema](https://pypi.org/project/jsonschema/) project, install with the optional
`validation` requirements: 


```bash
> pip install pystac[validation]
```

If you would like to use the [`orjson`](https://pypi.org/project/orjson/) instead of the
standard `json` library for JSON serialization/deserialization, install with the
optional `orjson` requirements:

```bash
> pip install pystac[orjson]
```

> *`orjson` wheels are only available for Linux in Python 3.10. If you are using the
> `orjson` extra with Python 3.10 you will need to have the Rust nightly toolchain
> installed as your default toolchain in order to build the package wheel.*

From source repository:

```bash
> git clone https://github.com/stac-utils/pystac.git
> cd pystac
> pip install .
```


#### Versions
To install a version of PySTAC that works with a specific versions of the STAC
specification, install the matching version of PySTAC from the following table.

| PySTAC | STAC  |
| ------ | ----- |
| 1.x    | 1.0.x |
| 0.5.x  | 1.0.0-beta.* |
| 0.4.x  | 0.9.x |
| 0.3.x  | 0.8.x |

For instance, to work with STAC v0.9.x:

```bash
pip install pystac==0.4.0
```

STAC spec versions below 0.8 are not supported by PySTAC.

## Documentation

See the [documentation page](https://pystac.readthedocs.io/en/latest/) for the latest docs.

## Developing

See [contributing docs](docs/contributing.rst) for details on contributing to this project.

## Running the quickstart and tutorials

There is a quickstart and tutorials written as jupyter notebooks in the `docs/tutorials` folder.
To run the notebooks, run a jupyter notebook with the `docs` directory as the notebook directory:

```
> PYTHONPATH=`pwd`:$PYTHONPATH jupyter notebook --ip 0.0.0.0 --port 8888 --notebook-dir=docs
```

You can then navigate to the notebooks and execute them.

Requires [Jupyter](https://jupyter.org/) be installed.
