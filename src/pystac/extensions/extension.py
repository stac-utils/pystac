import warnings

from ..errors import PySTACWarning
from .protocols import Extendable


class Extension:
    """For now, all extensions are assumed to be in the stac-extensions organization."""

    _name: str
    _slug: str
    _version: str

    def get_default_url(self) -> str:
        return f"https://stac-extensions.github.io/{self._name}/v{self._version}/schema.json"

    def get_url_prefix(self) -> str:
        return f"https://stac-extensions.github.io/{self._name}"

    def __init__(self, extendable: Extendable, frozen: bool = True) -> None:
        super().__init__(**extendable.get_fields(), frozen=frozen)
        self._extendable: Extendable = extendable

    def apply(self, fields):
        self._extendable.get_fields().update(
            fields.model_dump(by_alias=True, mode="json", exclude_unset=True)
        )

    def add(self) -> None:
        if not hasattr(self._extendable, "stac_extensions"):
            raise TypeError(
                "STAC Extensions can only be added to Catalogs, Collections, and Items"
            )
        if self._extendable.stac_extensions is None:
            self._extendable.stac_extensions = [self.get_default_url()]
        else:
            prefix = self.get_url_prefix()
            stac_extensions = [
                s for s in self._extendable.stac_extensions if not s.startswith(prefix)
            ]
            stac_extensions.append(self.get_default_url())
            self._extendable.stac_extensions = stac_extensions

    def exists(self) -> bool:
        if not hasattr(self._extendable, "stac_extensions"):
            raise TypeError(
                "STAC Extensions list only exists on Catalogs, Collections, and Items"
            )
        if self._extendable.stac_extensions is None:
            return False
        else:
            prefix = self.get_url_prefix()
            return any(
                s for s in self._extendable.stac_extensions if s.startswith(prefix)
            )

    def remove(self) -> None:
        if not hasattr(self._extendable, "stac_extensions"):
            raise TypeError(
                "STAC Extensions list only exists on Catalogs, Collections, and Items"
            )

        if self._extendable.stac_extensions is not None:
            prefix = self.get_url_prefix()
            self._extendable.stac_extensions = [
                s for s in self._extendable.stac_extensions if not s.startswith(prefix)
            ]

    def get_url(self) -> str | None:
        if not hasattr(self._extendable, "stac_extensions"):
            raise TypeError(
                "STAC Extensions list only exists on Catalogs, Collections, and Items"
            )

        if self._extendable.stac_extensions is None:
            return None
        else:
            prefix = self.get_url_prefix()
            for s in self._extendable.stac_extensions:
                if s.startswith(prefix):
                    return s
            return None

    def get_version(self) -> str | None:
        if not hasattr(self._extendable, "stac_extensions"):
            raise TypeError(
                "STAC Extensions list only exists on Catalogs, Collections, and Items"
            )

        if url := self.get_url():
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
