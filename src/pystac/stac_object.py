from __future__ import annotations

import copy
import warnings
from abc import ABC, abstractmethod
from collections.abc import Iterator
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, override

from typing_extensions import deprecated

from pystac.errors import STACTypeError
from pystac.rel_type import RelType
from pystac.writer import DEFAULT_WRITER

from .constants import STAC_OBJECT_TYPE
from .link import Link
from .reader import DEFAULT_READER, Reader
from .utils import is_absolute_href, make_absolute_href, make_relative_href
from .validator import Validator
from .writer import Writer

if TYPE_CHECKING:
    from .collection import Collection
    from .container import Container
    from .href_generator import HrefGenerator
    from .writer import Writer


class STACObject(ABC):
    type: ClassVar[STAC_OBJECT_TYPE]

    def __init__(
        self,
        type: str,
        id: str,
        stac_version: str,
        stac_extensions: list[str] | None,
        links: list[Link] | list[dict[str, Any]] | None,
        **kwargs: Any,
    ) -> None:
        if type != self.type:
            d = {
                "type": type,
                "id": id,
                "stac_version": stac_version,
                "stac_extensions": stac_extensions,
                "links": links,
            }
            d.update(kwargs)
            raise STACTypeError(
                d,
                self.__class__,
            )

        self.id: str = id
        self.stac_version: str = stac_version
        self.stac_extensions: list[str] | None = stac_extensions
        if links:
            self.links: list[Link] = [Link.try_from(link) for link in links]
        else:
            self.links = []
        self.extra_fields: dict[str, Any] = kwargs

        self.reader: Reader = DEFAULT_READER
        self.writer: Writer = DEFAULT_WRITER

        self._root: Container | None = None
        self._href: str | None = None

    @override
    def __setattr__(self, name: str, value: Any, /) -> None:
        if name == "_stac_io":
            warnings.warn("_stac_io is a deprecated attribute. Set .reader or .writer")

            from .stac_io import StacIOReader, StacIOWriter

            self.reader = StacIOReader(value)
            self.writer = StacIOWriter(value)
        return super().__setattr__(name, value)

    @classmethod
    def from_file[T: STACObject](
        cls: type[T], path: str | Path, reader: Reader = DEFAULT_READER
    ) -> T:
        href = make_absolute_href(str(path))
        data = reader.get_json(href)
        if "type" not in data:
            if "properties" in data:
                type_value = "Feature"
            elif "extents" in data or "license" in data:
                type_value = "Collection"
            else:
                type_value = "Catalog"
            warnings.warn(f"Data does not have a 'type' field, guessed as {type_value}")
            data["type"] = type_value

        stac_object = cls.from_dict(data)
        if not isinstance(stac_object, cls):
            raise ValueError(
                f"Expected {cls.__name__}, got {type(stac_object).__name__}"
            )
        stac_object.reader = reader
        stac_object.set_self_href(href)
        return stac_object

    @classmethod
    @abstractmethod
    def from_dict[T: STACObject](
        cls: type[T],
        data: dict[str, Any],
        preserve_dict: bool = True,
        migrate: bool | None = None,
        root: Container | None = None,
    ) -> T:
        from .deserialize import from_dict

        if preserve_dict:
            data = copy.deepcopy(data)
        return from_dict(data)  # pyright: ignore[reportReturnType]

    @abstractmethod
    def to_dict(
        self, include_self_link: bool = True, transform_hrefs: bool | None = None
    ) -> dict[str, Any]:
        if transform_hrefs is not None:
            warnings.warn(
                "transform_hrefs is deprecated as an argument",
                DeprecationWarning,
            )
            if transform_hrefs:
                raise NotImplementedError
        data = copy.deepcopy(self.extra_fields)
        links = [
            link.to_dict()
            for link in self.links
            # Keep the self link if include_self_link is true and the object
            # doesn't have an href
            if include_self_link and not self._href or not link.is_self()
        ]
        if include_self_link and self._href:
            links.append(Link(rel="self", target=self._href).to_dict())
        data.update(
            {
                "type": self.type,
                "stac_version": self.stac_version,
                "id": self.id,
                "links": links,
            }
        )
        if self.stac_extensions is not None:
            data["stac_extensions"] = self.stac_extensions
        return data

    def get_link(self, rel: str) -> Link | None:
        return next((link for link in self.links if link.rel == rel), None)

    def get_links(self, rel: str | None = None) -> list[Link]:
        return list(link for link in self.links if rel is None or link.rel == rel)

    @deprecated("Use .get_link()")
    def get_single_link(self, rel: str) -> Link | None:
        return self.get_link(rel)

    def get_derived_from(self) -> list[STACObject]:
        derived_from: list[STACObject] = []
        for link in self.links:
            if link.is_derived_from():
                derived_from.append(link.get_target(self._href, self.reader))
        return derived_from

    @deprecated("Append to .links")
    def add_link(self, link: Link) -> None:
        self.links.append(link)

    def add_derived_from(self, *values: STACObject | str) -> None:
        for value in values:
            self.links.append(Link(target=value, rel=RelType.DERIVED_FROM))

    def remove_derived_from(self, id: str) -> None:
        links: list[Link] = []
        for link in self.links:
            if link.is_derived_from():
                stac_object = link.get_target(self._href, self.reader)
                if stac_object.id == id:
                    continue
            links.append(link)
        self.links = links

    def remove_links(self, rel: str) -> None:
        self.links = list(link for link in self.links if not link.rel == rel)

    def remove_hierarchical_links(self, add_canonical: bool = False) -> None:
        self.links = list(link for link in self.links if not link.is_hierarchical())
        if add_canonical and self._href:
            self.links.append(Link(rel="canonical", target=self._href))

    @property
    @deprecated("Use get_self_href")
    def self_href(self) -> str | None:
        return self.get_self_href()

    def get_self_href(self) -> str | None:
        return self._href

    def set_self_href(self, href: str | None) -> None:
        self._href = href
        self.links = list(link for link in self.links if not link.is_self())
        if href:
            self.links.append(Link(rel="self", target=href))

    def get_root(self) -> Container | None:
        from .container import Container

        if self._root is None:
            root = self._maybe_get_link_target(RelType.ROOT)
            if isinstance(root, Container):
                self._root = root
            else:
                warnings.warn(
                    "The 'root' link does not point to a collection or catalog"
                )
        return self._root

    def remove_root(self) -> Container | None:
        root = self._root
        self._root = None
        self.remove_links(RelType.ROOT)
        return root

    def get_parent(self) -> Container | None:
        from .container import Container

        stac_object = self._maybe_get_link_target(RelType.PARENT)
        if isinstance(stac_object, Container):
            return stac_object
        else:
            warnings.warn("The 'parent' link does not point to a collection or catalog")
            return None

    def get_root_link(self) -> Link | None:
        return next((link for link in self.links if link.is_root()), None)

    def set_root(self, root: Container) -> None:
        self._root = root

    def validate(
        self, validate_extensions: bool = True, validator: Validator | None = None
    ) -> None:
        if validator is None:
            from .jsonschema import DEFAULT_JSON_SCHEMA_VALIDATOR

            validator = DEFAULT_JSON_SCHEMA_VALIDATOR

        data = self.to_dict()
        validator.validate_core(self.type, self.stac_version, data)

        if validate_extensions and self.stac_extensions:
            for extension in self.stac_extensions:
                if not is_absolute_href(extension):
                    extension = make_absolute_href(extension, self._href, False)
                validator.validate_extension(extension, data)

    def render(
        self,
        /,
        use_absolute_links: bool = False,
        href_generator: HrefGenerator | None = None,
        previous_self_href: str | None = None,
        skip_unresolved: bool = False,
    ) -> Iterator[STACObject]:
        """Remove and re-create all hierarchical links on this STAC object and
        all children and items, yielding each."""
        yield from self._render(
            use_absolute_links=use_absolute_links,
            href_generator=href_generator,
            previous_self_href=previous_self_href,
            skip_unresolved=skip_unresolved,
            root=None,
            parent=None,
            collection=None,
        )

    def _render(
        self,
        /,
        root: Container | None = None,
        parent: Container | None = None,
        collection: Collection | None = None,
        use_absolute_links: bool = False,
        skip_unresolved: bool = False,
        href_generator: HrefGenerator | None = None,
        previous_self_href: str | None = None,
    ) -> Iterator[STACObject]:
        from .catalog import Catalog
        from .collection import Collection
        from .container import Container
        from .item import Item

        if href_generator is None:
            from .href_generator import BestPracticesHrefGenerator

            href_generator = BestPracticesHrefGenerator()

        self_href = self.get_self_href()
        if self_href is None:
            raise ValueError("Cannot render without a self href")
        if root is None and isinstance(self, Container):
            root = self

        links: list[Link] = []
        if root and (root_href := root.get_self_href()):
            links.append(
                self._update_link_href(
                    Link(rel=RelType.ROOT, target=root),
                    href=root_href,
                    make_absolute=use_absolute_links,
                )
            )
        if parent and (parent_href := parent.get_self_href()):
            links.append(
                self._update_link_href(
                    Link(rel=RelType.PARENT, target=parent),
                    href=parent_href,
                    make_absolute=use_absolute_links,
                )
            )
        if collection and (collection_href := collection.get_self_href()):
            links.append(
                self._update_link_href(
                    Link(rel=RelType.COLLECTION, target=collection),
                    href=collection_href,
                    make_absolute=use_absolute_links,
                )
            )
        for link in self.links:
            if skip_unresolved and not link.is_resolved():
                links.append(link)
                continue

            if link.is_child() or link.is_item():
                stac_object = link.get_target(previous_self_href, self.reader)
                stac_object_previous_self_href = stac_object.get_self_href()
                if isinstance(stac_object, Container):
                    href = href_generator.get_child(self_href, stac_object)
                    stac_object.set_self_href(href)
                    links.append(
                        self._update_link_href(
                            link,
                            href=href,
                            make_absolute=use_absolute_links,
                        )
                    )
                elif isinstance(stac_object, Item):
                    href = href_generator.get_item(self_href, stac_object)
                    stac_object.set_self_href(href)
                    links.append(
                        self._update_link_href(
                            link,
                            href=href,
                            make_absolute=use_absolute_links,
                        )
                    )

                if isinstance(self, Collection):
                    yield from stac_object._render(
                        root=root,
                        parent=self,
                        collection=self,
                        use_absolute_links=use_absolute_links,
                        href_generator=href_generator,
                        previous_self_href=stac_object_previous_self_href,
                    )
                elif isinstance(self, Catalog):
                    yield from stac_object._render(
                        root=root,
                        parent=self,
                        use_absolute_links=use_absolute_links,
                        href_generator=href_generator,
                        previous_self_href=stac_object_previous_self_href,
                    )
                else:
                    yield from stac_object._render(
                        root=root,
                        use_absolute_links=use_absolute_links,
                        href_generator=href_generator,
                        previous_self_href=stac_object_previous_self_href,
                    )
            elif not link.is_hierarchical():
                links.append(link)

        self.links = links
        yield self

    def save_object(
        self,
        include_self_link: bool = True,
        dest_href: str | None = None,
        writer: Writer | None = None,
    ) -> None:
        href = dest_href or self._href
        if not href:
            raise ValueError(
                "dest_href was not provided, and object does not have a self href"
            )
        href = make_absolute_href(href)
        if writer is None:
            writer = self.writer
        writer.put_json(self.to_dict(include_self_link), href)

    def clone[T: STACObject](self: T) -> T:
        return copy.deepcopy(self)

    @override
    def __repr__(self) -> str:
        return f"<{self.__class__} id={self.id}>"

    def _update_link_href(self, link: Link, href: str, make_absolute: bool) -> Link:
        self_href = self.get_self_href()
        href = make_absolute_href(href, self_href, start_is_dir=False)
        if not make_absolute and self_href:
            href = make_relative_href(href, self_href, start_is_dir=False)
        link.set_href(href)
        return link

    def _maybe_get_link_target(self, rel: str) -> STACObject | None:
        link = self.get_link(rel)
        if link:
            return link.get_target(start_href=self._href, reader=self.reader)
        else:
            return None


@deprecated("STACObjectType is deprecated, use pystac.constants.STAC_OBJECT_TYPE")
class STACObjectType(StrEnum):
    CATALOG = "Catalog"
    COLLECTION = "Collection"
    ITEM = "Feature"


def __getattr__(name: str) -> Any:
    from typing import TypeVar

    if name == "S":
        warnings.warn(
            "pystac.stac_object.S is deprecated, use `type[STACObject]`",
            DeprecationWarning,
        )
        return TypeVar("S", bound="STACObject")
    raise AttributeError(f"module {__name__} has no attribute {name}")
