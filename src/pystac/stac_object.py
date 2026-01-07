from __future__ import annotations

import copy
import warnings
from abc import ABC, abstractmethod
from collections.abc import Iterator
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Protocol

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
    from .item import Item


def __getattr__(name: str) -> Any:
    from typing import TypeVar

    if name == "S":
        warnings.warn(
            "pystac.stac_object.S is deprecated, just use `type[STACObject]` instead"
        )
        return TypeVar("S", bound="STACObject")
    raise AttributeError(f"module {__name__} has no attribute {name}")


class HrefGenerator(Protocol):
    def get_root(self, prefix: str, container: Container) -> str: ...
    def get_child(self, parent_href: str, container: Container) -> str: ...
    def get_item(self, parent_href: str, item: Item) -> str: ...


class BestPracticesHrefGenerator:
    def get_root(self, prefix: str, container: Container) -> str:
        from .catalog import Catalog
        from .collection import Collection

        if isinstance(container, Catalog):
            return make_absolute_href(prefix, "./catalog.json", start_is_dir=True)
        elif isinstance(container, Collection):
            return make_absolute_href(prefix, "./collection.json", start_is_dir=True)
        else:
            raise ValueError(f"Unsupported root type: {type(container)}")

    def get_child(self, parent_href: str, container: Container) -> str:
        from .catalog import Catalog
        from .collection import Collection

        if isinstance(container, Catalog):
            file_name = "catalog.json"
        elif isinstance(container, Collection):
            file_name = "collection.json"
        else:
            raise ValueError(f"Unsupported child type: {type(container)}")

        return make_absolute_href(
            parent_href, "/".join((container.id, file_name)), start_is_dir=False
        )

    def get_item(self, parent_href: str, item: Item) -> str:
        return make_absolute_href(
            parent_href, "/".join((item.id, f"{item.id}.json")), start_is_dir=False
        )


DEFAULT_HREF_GENERATOR = BestPracticesHrefGenerator()


@deprecated("STACObjectType is deprecated")
class STACObjectType(StrEnum):
    CATALOG = "Catalog"
    COLLECTION = "Collection"
    ITEM = "Feature"


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
            raise STACTypeError(f"Expected {self.type}, got {type}")

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

    @classmethod
    def from_file[T: STACObject](
        cls: type[T], path: str | Path, reader: Reader = DEFAULT_READER
    ) -> T:
        href = make_absolute_href(str(path))
        data = reader.get_json(href)
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
    def from_dict[T: STACObject](cls: type[T], data: dict[str, Any]) -> T:
        from .deserialize import from_dict

        return from_dict(data)  # pyright: ignore[reportReturnType]

    @abstractmethod
    def to_dict(
        self, include_self_link: bool = True, transform_hrefs: bool | None = None
    ) -> dict[str, Any]:
        if transform_hrefs is not None:
            warnings.warn(
                "transform_hrefs is deprecated as an argument in `to_dict`",
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

    def get_links(self, rel: str) -> list[Link]:
        return list(link for link in self.links if link.rel == rel)

    @deprecated("Use get_link instead")
    def get_single_link(self, rel: str) -> Link | None:
        return self.get_link(rel)

    def get_derived_from(self) -> list[STACObject]:
        derived_from: list[STACObject] = []
        for link in self.links:
            if link.is_derived_from():
                derived_from.append(link.get_target(self._href, self.reader))
        return derived_from

    @deprecated("Just append to the links array")
    def add_link(self, link: Link) -> None:
        self.links.append(link)

    def add_derived_from(self, *values: STACObject | str) -> None:
        for value in values:
            if isinstance(value, STACObject):
                self.links.append(Link(target=value, rel=RelType.DERIVED_FROM))
            else:
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
        if self._root is None:
            root = self._maybe_get_link_target("root")
            if isinstance(root, Container):
                self._root = root
            else:
                warnings.warn(
                    "The 'root' link does not point to a collection or catalog"
                )
        return self._root

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
        root: Container | None = None,
        parent: Container | None = None,
        collection: Collection | None = None,
        use_absolute_links: bool = False,
        href_generator: HrefGenerator = DEFAULT_HREF_GENERATOR,
    ) -> Iterator[STACObject]:
        from .item import Item

        self_href = self.get_self_href()
        if self_href is None:
            raise ValueError("Cannot render a self href")
        if root is None and isinstance(self, Container):
            root = self
        links: list[Link] = []
        non_hierarchical_links: list[Link] = []
        if root and (root_href := root.get_self_href()):
            links.append(
                self._make_link(
                    rel=RelType.ROOT,
                    target=root,
                    href=root_href,
                    make_absolute=use_absolute_links,
                )
            )
        if parent and (parent_href := parent.get_self_href()):
            links.append(
                self._make_link(
                    rel=RelType.PARENT,
                    target=parent,
                    href=parent_href,
                    make_absolute=use_absolute_links,
                )
            )
        if collection and (collection_href := collection.get_self_href()):
            links.append(
                self._make_link(
                    rel=RelType.COLLECTION,
                    target=collection,
                    href=collection_href,
                    make_absolute=use_absolute_links,
                )
            )
        for link in self.links:
            if link.is_child() or link.is_item():
                stac_object = link.get_target(self.get_self_href(), self.reader)
                href = stac_object.get_self_href()
                if isinstance(stac_object, Container):
                    if not href:
                        href = href_generator.get_child(self_href, stac_object)
                        stac_object.set_self_href(href)
                    links.append(
                        self._make_link(
                            rel=RelType.CHILD,
                            target=stac_object,
                            href=href,
                            make_absolute=use_absolute_links,
                        )
                    )
                elif isinstance(stac_object, Item):
                    if not href:
                        href = href_generator.get_item(self_href, stac_object)
                        stac_object.set_self_href(href)
                    links.append(
                        self._make_link(
                            rel=RelType.ITEM,
                            target=stac_object,
                            href=href,
                            make_absolute=use_absolute_links,
                        )
                    )

                if isinstance(self, Container):
                    yield from stac_object.render(
                        root=root,
                        parent=self,
                        use_absolute_links=use_absolute_links,
                        href_generator=href_generator,
                    )
                else:
                    yield from stac_object.render(
                        root=root,
                        use_absolute_links=use_absolute_links,
                        href_generator=href_generator,
                    )
            elif not link.is_hierarchical():
                non_hierarchical_links.append(link)

        self.links = links + non_hierarchical_links
        yield self

    def save_object(
        self, include_self_link: bool = True, dest_href: str | None = None
    ) -> None:
        href = dest_href or self._href
        if not href:
            raise ValueError(
                "dest_href was not provided, and object does not have a self href"
            )
        href = make_absolute_href(href)
        self.writer.put_json(self.to_dict(include_self_link), href)

    def clone[T: STACObject](self: T) -> T:
        return self.from_dict(self.to_dict())

    def _make_link(
        self, rel: str, target: STACObject, href: str, make_absolute: bool
    ) -> Link:
        self_href = self.get_self_href()
        href = make_absolute_href(href, self_href, start_is_dir=False)
        if not make_absolute and self_href:
            href = make_relative_href(href, self_href, start_is_dir=False)
        return Link(rel=rel, target=target, href=href)

    def _maybe_get_link_target(self, rel: str) -> STACObject | None:
        link = self.get_link(rel)
        if link:
            return link.get_target(start_href=self._href, reader=self.reader)
        else:
            return None


class Container(STACObject, ABC):
    def get_items(self, recursive: bool = False) -> Iterator[Item]:
        for link in self.links:
            if link.is_item():
                from .item import Item

                stac_object = link.get_target(start_href=self._href, reader=self.reader)
                if isinstance(stac_object, Item):
                    yield stac_object
            elif recursive and link.is_child():
                stac_object = link.get_target(start_href=self._href, reader=self.reader)
                if isinstance(stac_object, Container):
                    yield from stac_object.get_items(recursive=True)

    def add_item(self, item: Item) -> None:
        self.links.append(Link(target=item, rel=RelType.ITEM))

    def get_child(self, id: str) -> Container | None:
        for link in self.links:
            if link.is_child():
                stac_object = link.get_target(start_href=self._href, reader=self.reader)
                if isinstance(stac_object, Container) and stac_object.id == id:
                    return stac_object

    def add_child(self, child: Container) -> None:
        link = Link(target=child, rel=RelType.CHILD)
        self.links.append(link)

    @deprecated("Use render instead")
    def normalize_hrefs(self, root_href: str) -> None:
        href_generator = DEFAULT_HREF_GENERATOR
        self.set_self_href(href_generator.get_root(root_href, self))
        for _ in self.render():
            pass

    def walk(self) -> Iterator[tuple[Container, list[Container], list[Item]]]:
        from .item import Item

        self_href = self.get_self_href()
        children: list[Container] = []
        items: list[Item] = []
        for link in self.links:
            if link.is_child() or link.is_item():
                stac_object = link.get_target(self_href, self.reader)
                if isinstance(stac_object, Container):
                    children.append(stac_object)
                elif isinstance(stac_object, Item):
                    items.append(stac_object)

        yield (self, children, items)

        for child in children:
            yield from child.walk()

    def target_in_hierarchy(self, target: STACObject) -> bool:
        for root, _, items in self.walk():
            if root == target or any(item == target for item in items):
                return True

        return False
