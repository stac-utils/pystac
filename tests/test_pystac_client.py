# mypy: ignore-errors
import builtins
import sys
from types import ModuleType
from typing import Any

import pytest

real_import = builtins.__import__

try:
    import pystac_client  # noqa:F401

    HAS_PYSTAC_CLIENT = True
except ImportError:
    HAS_PYSTAC_CLIENT = False


@pytest.mark.skipif(not HAS_PYSTAC_CLIENT, reason="requires pystac_client")
def test_import_pystac_client_when_available() -> None:
    from pystac.client import Client

    assert Client.__doc__


# copied from
# http://materials-scientist.com/blog/2021/02/11/mocking-failing-module-import-python/
def monkey_import_importerror(name: str, *args: Any, **kwargs: Any) -> ModuleType:
    if name == "pystac_client":
        raise ImportError(f"No module named '{name}'")
    return real_import(name, *args, **kwargs)


def test_import_pystac_client_when_not_available(monkeypatch: Any) -> None:
    if HAS_PYSTAC_CLIENT:
        monkeypatch.delitem(sys.modules, "pystac_client", raising=False)
        monkeypatch.setattr(builtins, "__import__", monkey_import_importerror)

    with pytest.raises(ImportError):
        from pystac_client import Client  # noqa:F401

    with pytest.raises(ImportError, match="Please install pystac-client:"):
        from pystac.client import Client  # noqa:F401,F811
