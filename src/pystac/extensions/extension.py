import warnings
from abc import ABC, abstractmethod
from typing import Any

from typing_extensions import Self

from ..errors import PySTACWarning
from .protocols import Extendable


class Extension(ABC):
    """For now, all extensions are assumed to be in the stac-extensions organization."""

    @classmethod
    @abstractmethod
    def get_name(cls: type[Self]) -> str:
        raise NotImplementedError

    @classmethod
    def get_slug(cls: type[Self]) -> str:
        return cls.get_name()

    @classmethod
    @abstractmethod
    def get_default_version(cls: type[Self]) -> str:
        raise NotImplementedError

    @classmethod
    def get_default_extension_url(cls: type[Self]) -> str:
        return f"https://stac-extensions.github.io/{cls.get_name()}/v{cls.get_default_version()}/schema.json"

    @classmethod
    def get_extension_url_prefix(cls: type[Self]) -> str:
        return f"https://stac-extensions.github.io/{cls.get_name()}"

    def __init__(self, extendable: Extendable) -> None:
        self.extendable: Extendable
        super().__setattr__("extendable", extendable)

    def __getattr__(self, name: str) -> Any:
        key = f"{self.get_slug()}:{name}"
        try:
            return self.extendable.get_fields()[key]
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, name: str, value: Any) -> None:
        key = f"{self.get_slug()}:{name}"
        self.extendable.get_fields()[key] = value

    def add(self) -> None:
        if self.extendable.stac_extensions is None:
            self.extendable.stac_extensions = [self.get_default_extension_url()]
        else:
            prefix = self.get_extension_url_prefix()
            stac_extensions = [
                s for s in self.extendable.stac_extensions if not s.startswith(prefix)
            ]
            stac_extensions.append(self.get_default_extension_url())
            self.extendable.stac_extensions = stac_extensions

    def exists(self) -> bool:
        if self.extendable.stac_extensions is None:
            return False
        else:
            prefix = self.get_extension_url_prefix()
            return any(
                s for s in self.extendable.stac_extensions if s.startswith(prefix)
            )

    def remove(self) -> None:
        if self.extendable.stac_extensions is not None:
            prefix = self.get_extension_url_prefix()
            self.extendable.stac_extensions = [
                s for s in self.extendable.stac_extensions if not s.startswith(prefix)
            ]
            for key in list(self.extendable.get_fields().keys()):
                if key.startswith(f"{self.get_slug()}:"):
                    self.extendable.get_fields().pop(key)

    @property
    def version(self) -> str | None:
        if url := self.get_extension_url():
            parts = url.rsplit("/", 2)
            if len(parts) == 3:
                if parts[1].startswith("v") and len(parts[1]) > 2:
                    return parts[1][1:]
                else:
                    warnings.warn(
                        f"Invalid extension version: {parts[1]}", PySTACWarning
                    )
                    return None
            else:
                warnings.warn(f"Invalid extension url: {url}", PySTACWarning)
                return None
        else:
            return None

    def get_extension_url(self) -> str | None:
        if self.extendable.stac_extensions is None:
            return None
        else:
            prefix = self.get_extension_url_prefix()
            for s in self.extendable.stac_extensions:
                if s.startswith(prefix):
                    return s
            return None
