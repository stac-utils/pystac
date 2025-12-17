import warnings
from collections.abc import Callable
from functools import wraps
from typing import Any


def argument(name: str) -> None:
    warnings.warn(
        f"Argument {name} is deprecated in PySTAC v2.0 and will be removed in a future "
        "version.",
        FutureWarning,
    )


def module(name: str) -> None:
    warnings.warn(
        f"Module pystac.{name} is deprecated in PySTAC v2.0 "
        "and will be removed in a future "
        "version.",
        FutureWarning,
    )


def function(message: str) -> Callable[..., Any]:
    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Issues a FutureWarning for PySTAC deprecations."""

            warnings.warn(
                f"{f.__name__} is deprecated as of PySTAC v2.0 and will be removed "
                f"in a future version. {message}",
                FutureWarning,
            )
            return f(*args, **kwargs)

        return wrapper

    return decorator
