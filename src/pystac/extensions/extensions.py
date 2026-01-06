import warnings
from functools import cache

from pydantic import BaseModel

from .extension import Extension
from .protocols import Extendable


@cache
def _dynamic_extension_cls(
    name: str, slug: str, version: str, fields_cls: type[BaseModel]
):
    class SpecificExtension(Extension, fields_cls):
        _name: str = name
        _slug: str = slug
        _version: str = version

    return SpecificExtension


# Inspired by xarray
class _RegisteredExtension:
    """Custom property-like object (descriptor) for accession extensions."""

    def __init__(self, name: str, slug: str, version: str, fields_cls: type[BaseModel]):
        self._extension_cls = _dynamic_extension_cls(name, slug, version, fields_cls)
        self._extension_cls.__name__ = f"{name.capitalize()}Extension"

    def __get__(self, obj, cls):
        try:
            extension_obj = self._extension_cls(obj.extendable, frozen=True)
        except AttributeError as err:
            # __getattr__ on data object will swallow any AttributeErrors
            # raised when initializing the extension, so we need to raise as
            # something else:
            raise RuntimeError(
                f"error initializing {self._extension_cls._name!r} extension."
            ) from err

        return extension_obj


def register_extension(name, slug, version):
    """Register a pydantic model representing the STAC Extension fields

    Use this decorator to include a new attribute on the `obj.ext`
    """

    def decorator(fields_cls):
        if hasattr(Extensions, name):
            warnings.warn(
                f"registration of extension {fields_cls!r} under name {name!r} is "
                "overriding a preexisting attribute with the same name.",
                UserWarning,
                stacklevel=2,
            )
        setattr(Extensions, name, _RegisteredExtension(name, slug, version, fields_cls))
        if slug != name:
            setattr(
                Extensions, slug, _RegisteredExtension(name, slug, version, fields_cls)
            )
        return fields_cls

    return decorator


class Extensions:
    """Manage extensions on a STAC object.

    Attributes are dynamically registered via the `register_extension` decorator
    """

    def __init__(self, extendable: Extendable) -> None:
        self.extendable = extendable
