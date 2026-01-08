# Contributing

Thank you for your interest in contributing to PySTAC!

## Development Setup

PySTAC uses [uv](https://docs.astral.sh/uv/) for dependency management.

### Clone and Install

```bash
git clone https://github.com/stac-utils/pystac.git
cd pystac
uv sync
```

This installs PySTAC in editable mode along with all development and documentation dependencies.

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_item.py

# Run tests matching a pattern
uv run pytest -k test_item_creation

# Run with coverage
uv run pytest --cov=pystac
```

### Linting and Formatting

PySTAC uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
# Check code
uv run ruff check

# Format code
uv run ruff format

# Fix auto-fixable issues
uv run ruff check --fix
```

### Type Checking

PySTAC uses [basedpyright](https://docs.basedpyright.com/) with strict mode:

```bash
uv run basedpyright
```

All code must pass type checking with strict mode enabled.

### Pre-commit Hooks

PySTAC uses pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run hooks manually
uv run pre-commit run --all-files
```

Hooks include:
- `ruff` for linting and formatting
- `basedpyright` for type checking
- `codespell` for spell checking

## Documentation

### Building Documentation

```bash
# Serve docs locally
uv run mkdocs serve

# Build docs
uv run mkdocs build
```

The documentation uses mkdocs-material and mkdocstrings for API documentation.

### Writing Documentation

- User guides go in `docs/user-guide/`
- API documentation is auto-generated from docstrings
- Use Google-style docstrings

Example docstring:

```python
def example_function(param: str) -> int:
    """Short description.

    Longer description with more details.

    Args:
        param: Description of parameter.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param is invalid.
    """
    pass
```

## Pull Request Process

1. **Fork and clone** the repository
2. **Create a branch** for your changes
3. **Make your changes** with tests
4. **Run tests and linting** locally
5. **Push and create a pull request**
6. **Respond to review feedback**

### PR Guidelines

- Write clear commit messages
- Include tests for new functionality
- Update documentation as needed
- Ensure all tests pass
- Keep PRs focused on a single concern

## Code Style

- Follow PEP 8 (enforced by ruff)
- Use type hints for all public APIs
- Write descriptive variable and function names
- Keep functions focused and small
- Add docstrings for public APIs

## Testing Guidelines

- Write tests for all new features
- Test edge cases and error conditions
- Use descriptive test names
- Keep tests simple and focused
- Mock external dependencies

Example test:

```python
def test_item_creation():
    """Test that items can be created with required fields."""
    item = pystac.Item(
        id="test-item",
        geometry={"type": "Point", "coordinates": [0, 0]},
        bbox=[0, 0, 0, 0],
        datetime=datetime.now(timezone.utc),
        properties={}
    )
    assert item.id == "test-item"
    assert item.geometry is not None
```

## Version Support

PySTAC requires Python 3.12 or later.

## Questions?

- Open an [issue](https://github.com/stac-utils/pystac/issues)
- Ask in [discussions](https://github.com/radiantearth/stac-spec/discussions/categories/stac-software)
- Join the [Gitter chat](https://gitter.im/SpatioTemporal-Asset-Catalog/python)

## Code of Conduct

This project adheres to the Contributor Covenant [Code of Conduct](https://github.com/stac-utils/pystac/blob/main/CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.
