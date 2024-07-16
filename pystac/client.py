from __future__ import annotations

from typing import Any

_import_error_message = (
    "pystac-client is not installed.\n\n"
    "Please install pystac-client:\n\n"
    "  pip install pystac-client"
)

try:
    from pystac_client import *  # noqa: F403
except ImportError as e:
    if e.msg == "No module named 'pystac_client'":
        raise ImportError(_import_error_message) from e
    else:
        raise


def __getattr__(value: str) -> Any:
    try:
        import pystac_client
    except ImportError as e:
        raise ImportError(_import_error_message) from e
    return getattr(pystac_client, value)
