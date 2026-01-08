from __future__ import annotations

from enum import StrEnum
from typing import Any, ClassVar, override

from typing_extensions import deprecated

from . import utils
from .constants import DEFAULT_STAC_VERSION, STAC_OBJECT_TYPE
from .container import Container
from .link import Link
from .rel_type import RelType


class Catalog(Container):
    type: ClassVar[STAC_OBJECT_TYPE] = "Catalog"

    def __init__(
        self,
        id: str,
        description: str,
        type: str = "Catalog",
        stac_version: str = DEFAULT_STAC_VERSION,
        stac_extensions: list[str] | None = None,
        links: list[Link] | list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            type=type,
            id=id,
            stac_version=stac_version,
            stac_extensions=stac_extensions,
            links=links,
            **kwargs,
        )
        self.description: str = description

    @override
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Catalog:
        return cls(**data)

    @override
    def to_dict(
        self, include_self_link: bool = True, transform_hrefs: bool | None = None
    ) -> dict[str, Any]:
        data = super().to_dict(
            include_self_link=include_self_link, transform_hrefs=transform_hrefs
        )
        data["description"] = self.description
        return data


@deprecated("CatalogType is deprecated")
class CatalogType(StrEnum):
    SELF_CONTAINED = "SELF_CONTAINED"
    """A 'self-contained catalog' is one that is designed for portability.
    Users may want to download an online catalog from and be able to use it on their
    local computer, so all links need to be relative.

    See:
        :stac-spec:`The best practices documentation on self-contained catalogs
        <best-practices.md#self-contained-catalogs>`
    """

    ABSOLUTE_PUBLISHED = "ABSOLUTE_PUBLISHED"
    """
    Absolute Published Catalog is a catalog that uses absolute links for everything,
    both in the links objects and in the asset hrefs.

    See:
        :stac-spec:`The best practices documentation on published catalogs
        <best-practices.md#published-catalogs>`
    """

    RELATIVE_PUBLISHED = "RELATIVE_PUBLISHED"
    """
    Relative Published Catalog is a catalog that uses relative links for everything, but
    includes an absolute self link at the root catalog, to identify its online location.

    See:
        :stac-spec:`The best practices documentation on published catalogs
        <best-practices.md#published-catalogs>`
    """

    @classmethod
    def determine_type(cls, stac_json: dict[str, Any]) -> CatalogType | None:  # pyright: ignore[reportDeprecated]
        """Determines the catalog type based on a STAC JSON dict.

        Only applies to Catalogs or Collections

        Args:
            stac_json : The STAC JSON dict to determine the catalog type

        Returns:
            Optional[CatalogType]: The catalog type of the catalog or collection.
            Will return None if it cannot be determined.
        """
        self_link = None
        relative = False
        for link in stac_json["links"]:
            if link["rel"] == RelType.SELF:
                self_link = link
            else:
                relative |= not utils.is_absolute_href(link["href"])

        if self_link:
            if relative:
                return cls.RELATIVE_PUBLISHED
            else:
                return cls.ABSOLUTE_PUBLISHED
        else:
            if relative:
                return cls.SELF_CONTAINED
            else:
                return None
