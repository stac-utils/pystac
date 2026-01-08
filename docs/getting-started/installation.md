# Installation

## Requirements

PySTAC requires Python 3.12 or later.

## Install from PyPI (Recommended)

The easiest way to install PySTAC is from PyPI using pip:

```bash
python -m pip install pystac
```

### Optional Dependencies

PySTAC has several optional dependency groups for additional features:

#### Validation

If you want to validate STAC objects against JSON schemas:

```bash
python -m pip install 'pystac[validation]'
```

This installs:
- `jsonschema` - For JSON schema validation
- `referencing` - For schema reference resolution

#### Jinja2 (Jupyter Display)

If you're using Jupyter notebooks and want pretty display of STAC objects:

```bash
python -m pip install 'pystac[jinja2]'
```

#### Object Storage (obstore)

For working with cloud object storage (S3, GCS, Azure):

```bash
python -m pip install 'pystac[obstore]'
```

This installs:
- `obstore` - For object storage access
- `obspec` - For object storage specifications

#### All Optional Dependencies

To install all optional dependencies:

```bash
python -m pip install 'pystac[validation,jinja2,obstore]'
```

## Install from Source

To install the latest development version from GitHub:

```bash
git clone https://github.com/stac-utils/pystac.git
cd pystac
python -m pip install .
```

### Development Installation

If you're contributing to PySTAC, install with development dependencies using [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/stac-utils/pystac.git
cd pystac
uv sync
```

This installs PySTAC in editable mode along with all development and documentation dependencies.

## Verifying Installation

You can verify your installation by checking the version:

```python
import pystac
print(pystac.__version__)
```

Or by running the test suite:

```bash
uv run pytest  # if installed with uv
# or
python -m pytest  # if installed with pip
```

## Next Steps

Now that you have PySTAC installed, check out the [Quickstart Guide](quickstart.md) to learn how to use it.
