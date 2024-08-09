from __future__ import annotations

import os
import posixpath
import warnings
from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import Callable
from string import Formatter
from typing import TYPE_CHECKING, Any

import pystac
from pystac.utils import is_file_path

if TYPE_CHECKING:
    from pystac.catalog import Catalog
    from pystac.collection import Collection
    from pystac.item import Item
    from pystac.stac_object import STACObject


class TemplateError(Exception):
    """DEPRECATED.

    .. deprecated:: 1.7.0
        Use :class:`pystac.errors.TemplateError` instead.

    Exception thrown when an error occurs during converting a template
    string into data for :class:`~pystac.layout.LayoutTemplate`
    """

    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        warnings.warn(
            message=(
                "TemplateError in pystac.layout is deprecated and will be "
                "removed in pystac version 2.0.0. Use TemplateError in "
                "pystac.errors instead."
            ),
            category=DeprecationWarning,
        )
        super().__init__(*args, **kwargs)


class LayoutTemplate:
    """Represents a template that can be used for deriving paths or other information
    based on properties of STAC objects supplied as a template string.

    Template strings use variables that can be pulled out of Catalogs, Collections
    and Items. The variable names can represent properties on the object itself,
    or keys in the dictionaries of the properties or extra_fields on the
    object (if they exist). The search order is as follows:

    - The object's attributes
    - Keys in the ``properties`` attribute, if it exists.
    - Keys in the ``extra_fields`` attribute, if it exists.

    Some special keys can be used in template variables:

    +--------------------+--------------------------------------------------------+
    | Template variable  | Meaning                                                |
    +====================+========================================================+
    | ``year``           | The year of an Item's datetime, or                     |
    |                    | start_datetime if datetime is null                     |
    +--------------------+--------------------------------------------------------+
    | ``month``          | The month of an Item's datetime, or                    |
    |                    | start_datetime if datetime is null                     |
    +--------------------+--------------------------------------------------------+
    | ``day``            | The day of an Item's datetime, or                      |
    |                    | start_datetime if datetime is null                     |
    +--------------------+--------------------------------------------------------+
    | ``date``           | The date (iso format) of an Item's                     |
    |                    | datetime, or start_datetime if datetime is null        |
    +--------------------+--------------------------------------------------------+
    | ``collection``     | The collection ID of an Item's collection.             |
    +--------------------+--------------------------------------------------------+

    The forward slash (``/``) should be used as path separator in the template
    string regardless of the system path separator (thus both in POSIX-compliant
    and Windows environments).

    Examples::

        # Uses the year, month and day of the item
        template = LayoutTemplate("${year}/${month}/${day}")

        # Uses a custom extension properties found on in the item properties.
        template = LayoutTemplate("${landsat:path}/${landsat:row}")

        # Uses the collection ID and a common metadata property for an item.
        template = LayoutTemplate("${collection}/${common_metadata.license}")

    Args:
        template : The template string to use.
        defaults : A dictionary of template vars to values. These values
            will be used in case a value cannot be derived from a stac object.
    """

    template: str
    """The template string to use."""

    defaults: dict[str, str]
    """A dictionary of template vars to values. These values will be used in case a
    value cannot be derived from a stac object."""

    template_vars: list[str]
    """List of template vars to use when templating."""

    # Special template vars specific to Items
    ITEM_TEMPLATE_VARS = ["date", "year", "month", "day", "collection"]

    def __init__(self, template: str, defaults: dict[str, str] | None = None) -> None:
        self.template = template
        self.defaults = defaults or {}

        # Generate list of template vars
        template_vars = []
        for formatter_parse_result in Formatter().parse(template):
            v = formatter_parse_result[1]
            if v is not None:
                if formatter_parse_result[2] != "":
                    v = f"{v}:{formatter_parse_result[2]}"
                template_vars.append(v)
        self.template_vars = template_vars

    def _get_template_value(self, stac_object: STACObject, template_var: str) -> Any:
        if template_var in self.ITEM_TEMPLATE_VARS:
            if isinstance(stac_object, pystac.Item):
                # Datetime
                dt = stac_object.datetime
                if dt is None:
                    dt = stac_object.common_metadata.start_datetime
                if dt is None:
                    raise pystac.TemplateError(
                        "Item {} does not have a datetime or "
                        "datetime range set; cannot template {} in {}".format(
                            stac_object, template_var, self.template
                        )
                    )

                if template_var == "year":
                    return dt.year
                if template_var == "month":
                    return dt.month
                if template_var == "day":
                    return dt.day
                if template_var == "date":
                    return dt.date().isoformat()

                # Collection
                if template_var == "collection":
                    if stac_object.collection_id is not None:
                        return stac_object.collection_id
                    raise pystac.TemplateError(
                        f"Item {stac_object} does not have a collection ID set; "
                        f"cannot template {template_var} in {self.template}"
                    )
            else:
                raise pystac.TemplateError(
                    '"{}" cannot be used to template non-Item {} in {}'.format(
                        template_var, stac_object, self.template
                    )
                )

        # Allow dot-notation properties for arbitrary object values.
        props = template_var.split(".")
        prop_source: pystac.STACObject | dict[str, Any] | None = None
        error = pystac.TemplateError(
            "Cannot find property {} on {} for template {}".format(
                template_var, stac_object, self.template
            )
        )

        try:
            if hasattr(stac_object, props[0]):
                prop_source = stac_object

            if prop_source is None and hasattr(stac_object, "properties"):
                obj_props: dict[str, Any] | None = stac_object.properties
                if obj_props is not None and props[0] in obj_props:
                    prop_source = obj_props

            if prop_source is None and hasattr(stac_object, "extra_fields"):
                extra_fields: dict[str, Any] | None = stac_object.extra_fields
                if extra_fields is not None and props[0] in extra_fields:
                    prop_source = extra_fields

            if prop_source is None:
                raise error

            v: Any = prop_source
            for prop in template_var.split("."):
                if isinstance(v, dict):
                    if prop not in v:
                        raise error
                    v = v[prop]
                else:
                    if not hasattr(v, prop):
                        raise error
                    v = getattr(v, prop)
        except pystac.TemplateError as e:
            if template_var in self.defaults:
                return self.defaults[template_var]
            raise e

        return v

    def get_template_values(self, stac_object: STACObject) -> dict[str, Any]:
        """Gets a dictionary of template variables to values derived from
        the given stac_object. If the template vars cannot be found in the
        stac object, and defaults was supplied to this template, a default
        value is used; if there is no default then this will raise an error.

        Args:
            stac_object : The STACObject to derive template
                variable values from.

        Returns:
            [dict]: A dictionary with keys being the template variables
            and values being the respective values based on the given
            stac object.

        Raises:
            pystac.TemplateError: If a value for a template variable cannot be
                derived from the stac object and there is no default,
                this error will be raised.
        """
        return OrderedDict(
            [(k, self._get_template_value(stac_object, k)) for k in self.template_vars]
        )

    def substitute(self, stac_object: STACObject) -> str:
        """Substitutes the values derived from
        :meth:`~pystac.layout.LayoutTemplate.get_template_values` into
        the template string for this template.

        Args:
            stac_object : The STACObject to derive template
                variable values from.

        Returns:
            str: The original template supplied to this LayoutTemplate
            with template variables replaced by the values derived
            from this stac object.

        Raises:
            pystac.TemplateError: If a value for a template variable cannot be
                derived from the stac object and there is no default,
                this error will be raised.
        """
        parts = self.get_template_values(stac_object)

        s = self.template
        for key, value in parts.items():
            s = s.replace("${" + f"{key}" + "}", f"{value}")
        return s


class HrefLayoutStrategy(ABC):
    """Base class for HREF Layout strategies."""

    def get_href(
        self, stac_object: STACObject, parent_dir: str, is_root: bool = False
    ) -> str:
        if is_file_path(parent_dir):
            parent_dir = os.path.dirname(parent_dir)

        if isinstance(stac_object, pystac.Item):
            return self.get_item_href(stac_object, parent_dir)
        elif isinstance(stac_object, pystac.Collection):
            return self.get_collection_href(stac_object, parent_dir, is_root)
        elif isinstance(stac_object, pystac.Catalog):
            return self.get_catalog_href(stac_object, parent_dir, is_root)
        else:
            raise pystac.STACError(f"Unknown STAC object type {stac_object}")

    @abstractmethod
    def get_catalog_href(self, cat: Catalog, parent_dir: str, is_root: bool) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_collection_href(
        self, col: Collection, parent_dir: str, is_root: bool
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_item_href(self, item: Item, parent_dir: str) -> str:
        raise NotImplementedError


class CustomLayoutStrategy(HrefLayoutStrategy):
    """Layout strategy that allows users to supply functions to dictate
    stac object paths.

    Args:
        catalog_func : A function that takes
            an catalog, a parent directory, and a flag specifying whether
            or not this catalog is the root. If it is the root, its usually
            best to not create a subdirectory and put the Catalog file directly
            in the parent directory. Must return the string path.
        collection_func : A function that
            is used for collections in the same manner at ``catalog_func``. This
            takes the same parameters.
        item_func  : A function that takes
            an item and a parent directory and returns the path to be used
            for the item.
        fallback_strategy : The fallback strategy to
            use if a function is not provided for a stac object type. Defaults to
            :class:`~pystac.layout.BestPracticesLayoutStrategy`
    """

    catalog_func: Callable[[Catalog, str, bool], str] | None
    """A function that takes a :class:`~pystac.Catalog`, a parent directory, and a
    boolean specifying whether or not this Catalog is the root. If it is the root, it
    is usually best to not create a subdirectory and put the Catalog file directly
    in the parent directory. Must return the string path."""

    collection_func: Callable[[Collection, str, bool], str] | None
    """A function that is used for collections in the same manner as
    :attr:`~catalog_func`. This takes the same parameters."""

    fallback_strategy: HrefLayoutStrategy
    """The fallback strategy to use if a function is not provided for a stac object
    type. Defaults to :class:`~pystac.layout.BestPracticesLayoutStrategy`."""

    item_func: Callable[[Item, str], str] | None
    """An optional function that takes an :class:`~pystac.Item` and a parent directory
    and returns the path to be used for the Item."""

    def __init__(
        self,
        catalog_func: Callable[[Catalog, str, bool], str] | None = None,
        collection_func: Callable[[Collection, str, bool], str] | None = None,
        item_func: Callable[[Item, str], str] | None = None,
        fallback_strategy: HrefLayoutStrategy | None = None,
    ):
        self.item_func = item_func
        self.collection_func = collection_func
        self.catalog_func = catalog_func
        if fallback_strategy is None:
            fallback_strategy = BestPracticesLayoutStrategy()
        self.fallback_strategy = fallback_strategy

    def get_catalog_href(self, cat: Catalog, parent_dir: str, is_root: bool) -> str:
        if self.catalog_func is not None:
            result = self.catalog_func(cat, parent_dir, is_root)
            if result is not None:
                return result
        return self.fallback_strategy.get_catalog_href(cat, parent_dir, is_root)

    def get_collection_href(
        self, col: Collection, parent_dir: str, is_root: bool
    ) -> str:
        if self.collection_func is not None:
            result = self.collection_func(col, parent_dir, is_root)
            if result is not None:
                return result
        return self.fallback_strategy.get_collection_href(col, parent_dir, is_root)

    def get_item_href(self, item: Item, parent_dir: str) -> str:
        if self.item_func is not None:
            result = self.item_func(item, parent_dir)
            if result is not None:
                return result
        return self.fallback_strategy.get_item_href(item, parent_dir)


class TemplateLayoutStrategy(HrefLayoutStrategy):
    """Layout strategy that can take strings to be supplied to
    :class:`~pystac.layout.LayoutTemplate` s to derive paths. Template strings
    can be supplied for catalogs, collections and items separately. If no
    template is supplied, a fallback layout strategy is supplied, which defaults
    to the :class:`~pystac.layout.BestPracticesLayoutStrategy`.

    All templated paths will be joined with the parent directory of the stac
    object.

    Args:
        catalog_template : The template string to use for catalog paths.
            Must be a valid template string that can be used by
            :class:`~pystac.layout.LayoutTemplate`
        collection_template : The template string to use for collection paths.
            Must be a valid template string that can be used by
            :class:`~pystac.layout.LayoutTemplate`
        item_template : The template string to use for item paths.
            Must be a valid template string that can be used by
            :class:`~pystac.layout.LayoutTemplate`
        fallback_strategy : The fallback strategy to
            use if a template is not provided. Defaults to
            :class:`~pystac.layout.BestPracticesLayoutStrategy`
    """

    catalog_template: LayoutTemplate | None
    """The template string to use for catalog paths. Must be a valid template string
    that can be used by :class:`~pystac.layout.LayoutTemplate`."""

    collection_template: LayoutTemplate | None
    """The template string to use for collection paths. Must be a valid template string
    that can be used by :class:`~pystac.layout.LayoutTemplate`."""

    fallback_strategy: HrefLayoutStrategy
    """The fallback strategy to use if a template is not provided. Defaults to
    :class:`~pystac.layout.BestPracticesLayoutStrategy`."""

    item_template: LayoutTemplate | None
    """The template string to use for item paths. Must be a valid template string that
    can be used by :class:`~pystac.layout.LayoutTemplate`."""

    def __init__(
        self,
        catalog_template: str | None = None,
        collection_template: str | None = None,
        item_template: str | None = None,
        fallback_strategy: HrefLayoutStrategy | None = None,
    ):
        self.catalog_template = (
            LayoutTemplate(catalog_template) if catalog_template is not None else None
        )
        self.collection_template = (
            LayoutTemplate(collection_template)
            if collection_template is not None
            else None
        )
        self.item_template = (
            LayoutTemplate(item_template) if item_template is not None else None
        )

        if fallback_strategy is None:
            fallback_strategy = BestPracticesLayoutStrategy()
        self.fallback_strategy = fallback_strategy

    def get_catalog_href(self, cat: Catalog, parent_dir: str, is_root: bool) -> str:
        if is_root or self.catalog_template is None:
            return self.fallback_strategy.get_catalog_href(cat, parent_dir, is_root)
        else:
            template_path = self.catalog_template.substitute(cat)
            if not template_path.endswith(".json"):
                template_path = posixpath.join(template_path, cat.DEFAULT_FILE_NAME)

            return posixpath.join(parent_dir, template_path)

    def get_collection_href(
        self, col: Collection, parent_dir: str, is_root: bool
    ) -> str:
        if is_root or self.collection_template is None:
            return self.fallback_strategy.get_collection_href(col, parent_dir, is_root)
        else:
            template_path = self.collection_template.substitute(col)
            if not template_path.endswith(".json"):
                template_path = posixpath.join(template_path, col.DEFAULT_FILE_NAME)

            return posixpath.join(parent_dir, template_path)

    def get_item_href(self, item: Item, parent_dir: str) -> str:
        if self.item_template is None:
            return self.fallback_strategy.get_item_href(item, parent_dir)
        else:
            template_path = self.item_template.substitute(item)
            if not template_path.endswith(".json"):
                template_path = posixpath.join(template_path, f"{item.id}.json")

            return posixpath.join(parent_dir, template_path)


class BestPracticesLayoutStrategy(HrefLayoutStrategy):
    """Layout strategy that represents the catalog layout described
    in the :stac-spec:`STAC Best Practices documentation
    <best-practices.md>`

    For a root catalog or collection, this will use the filename 'catalog.json'
    or 'collection.json' to the given directory. For a non-root catalog or collection,
    the ID will be used as a subdirectory, e.g. ``${id}/catalog.json`` or
    ``${id}/collection.json``. For items, a subdirectory with a name of the item
    ID will be made, and the item ID will be used in the filename, i.e.
    ``${id}/${id}.json``

    All paths are appended to the parent directory.
    """

    def get_catalog_href(self, cat: Catalog, parent_dir: str, is_root: bool) -> str:
        if is_root:
            cat_root = parent_dir
        else:
            cat_root = posixpath.join(parent_dir, f"{cat.id}")

        return posixpath.join(cat_root, cat.DEFAULT_FILE_NAME)

    def get_collection_href(
        self, col: Collection, parent_dir: str, is_root: bool
    ) -> str:
        if is_root:
            col_root = parent_dir
        else:
            col_root = posixpath.join(parent_dir, f"{col.id}")

        return posixpath.join(col_root, col.DEFAULT_FILE_NAME)

    def get_item_href(self, item: Item, parent_dir: str) -> str:
        item_root = posixpath.join(parent_dir, f"{item.id}")

        return posixpath.join(item_root, f"{item.id}.json")


class AsIsLayoutStrategy(HrefLayoutStrategy):
    """Layout strategy that simply preserves the current href of all objects.

    If any object doesn't have a self href, a ValueError is raised.
    """

    def get_catalog_href(self, cat: Catalog, parent_dir: str, is_root: bool) -> str:
        href = cat.self_href
        if href is None:
            raise ValueError(
                f"Catalog is missing href, required for AsIsLayoutStrategy: {cat}"
            )
        else:
            return href

    def get_collection_href(
        self, col: Collection, parent_dir: str, is_root: bool
    ) -> str:
        href = col.self_href
        if href is None:
            raise ValueError(
                f"Collection is missing href, required for AsIsLayoutStrategy: {col}"
            )
        else:
            return href

    def get_item_href(self, item: Item, parent_dir: str) -> str:
        href = item.self_href
        if href is None:
            raise ValueError(
                f"Item is missing href, required for AsIsLayoutStrategy: {item}"
            )
        else:
            return href


class APILayoutStrategy(HrefLayoutStrategy):
    """Layout strategy that represents the STAC API endpoint layout described
    in the `STAC API Specifications
    <https://github.com/radiantearth/stac-api-spec/blob/v1.0.0/overview.md#endpoints>`_

    The URL of the root catalog will be the base URL of the API.
    Other catalogs will be listed underneath their parent catalog
    at ``./${id}``.
    Collections will be found underneath the root or their parent
    catalog at ``./collections/${id}``. Collection cannot be the root themselves.
    Items will be found underneath their collections at
    ``./collections/${collection}/items/${id}``.
    """

    def get_catalog_href(
        self, cat: Catalog | str, parent_dir: str, is_root: bool
    ) -> str:
        """
        Generate a catalog href based on the provided parameters.

        Parameters:
        cat (Catalog | str): The catalog object or its ID.
        parent_dir (str): The parent directory for the catalog.
        is_root (bool): A flag indicating whether the catalog is a root catalog.

        Returns:
        str: The generated catalog href.
        """

        if not isinstance(cat, str):
            cat = cat.id

        if is_root:
            cat_href = parent_dir
        else:
            cat_href = posixpath.join(parent_dir, cat)

        return cat_href

    def get_collections_href(self, parent_dir: str) -> str:
        """
        Generate a collections href based on the provided parent directory.

        Parameters:
        parent_dir (str): The parent directory for the collections.

        Returns:
        str: The generated collections href.
        """
        return posixpath.join(parent_dir, "collections")

    def get_collection_href(
        self, col: Collection | str, parent_dir: str, is_root: bool
    ) -> str:
        """
        Generate a collection href based on the provided parameters.

        Parameters:
        col (Collection | str): The collection object or its ID.
        parent_dir (str): The parent directory for the collection.
        is_root (bool): A flag indicating whether the collection is a root collection.

        Returns:
        str: The generated collection href.

        Raises:
        ValueError: If the collection is set as root.
        """

        if not isinstance(col, str):
            col = col.id

        if is_root:
            raise ValueError("Collections cannot be root")

        col_root = self.get_collections_href(parent_dir)

        return posixpath.join(col_root, col)

    def get_items_href(self, parent_dir: str) -> str:
        """
        Generate an items href based on the provided parent directory.

        Parameters:
        parent_dir (str): The parent directory for the items.

        Returns:
        str: The generated items href.
        """
        return posixpath.join(parent_dir, "items")

    def get_item_href(self, item: Item | str, parent_dir: str) -> str:
        """
        Generate an item href based on the provided parameters.

        Parameters:
        item (Item | str): The item object or its ID.
        parent_dir (str): The parent directory for the item.

        Returns:
        str: The generated item href.
        """
        if not isinstance(item, str):
            item = item.id

        item_root = self.get_items_href(parent_dir)

        return posixpath.join(item_root, item)

    def get_search_href(self, parent_dir: str) -> str:
        """
        Generate a search href based on the provided parent directory.

        Parameters:
        parent_dir (str): The parent directory for the search.

        Returns:
        str: The generated search href.
        """
        return posixpath.join(parent_dir, "search")

    def get_conformance_href(self, parent_dir: str) -> str:
        """
        Generate a conformance href based on the provided parent directory.

        Parameters:
        parent_dir (str): The parent directory for the conformance.

        Returns:
        str: The generated conformance href.
        """
        return posixpath.join(parent_dir, "conformance")

    def get_service_desc_href(self, parent_dir: str) -> str:
        """
        Generate an API service description href based on the provided parent directory.

        Parameters:
        parent_dir (str): The parent directory for the API.

        Returns:
        str: The generated API href.
        """
        return posixpath.join(parent_dir, "api")

    def get_service_doc_href(self, parent_dir: str) -> str:
        """
        Generate an API service documentation href based on
        the provided parent directory.

        Parameters:
        parent_dir (str): The parent directory for the API.

        Returns:
        str: The generated API href.
        """
        return posixpath.join(parent_dir, "api.html")
