from abc import (abstractmethod, ABC)
from collections import OrderedDict
import os
from string import Formatter

import pystac


class TemplateError(Exception):
    """Exception thrown when an error occurs during converting a template
    string into data for :class:`~pystac.layout.LayoutTemplate`
    """
    pass


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

    Examples::

        # Uses the year, month and day of the item
        template = LayoutTemplate("${year}/${month}/${day}")

        # Uses a custom extension properties found on in the item properties.
        template = LayoutTemplate("${landsat:path}/${landsat:row}")

        # Uses the collection ID and a common metadata property for an item.
        template = LayoutTemplate("${collection}/${common_metadata.license}")

    Args:
        template (str): The template string to use.
        defaults (dict): A dictionary of template vars to values. These values
            will be used in case a value cannot be derived from a stac object.
    """

    # Special template vars specific to Items
    ITEM_TEMPLATE_VARS = ['date', 'year', 'month', 'day', 'collection']

    def __init__(self, template, defaults=None):
        self.template = template
        self.defaults = defaults or {}

        # Generate list of template vars
        template_vars = []
        for formatter_parse_result in Formatter().parse(template):
            v = formatter_parse_result[1]
            if v is not None:
                if formatter_parse_result[2] != '':
                    v = '{}:{}'.format(v, formatter_parse_result[2])
                template_vars.append(v)
        self.template_vars = template_vars

    def _get_template_value(self, stac_object, template_var):
        if template_var in self.ITEM_TEMPLATE_VARS:
            if stac_object.STAC_OBJECT_TYPE == pystac.STACObjectType.ITEM:
                # Datetime
                dt = stac_object.datetime
                if dt is None:
                    dt = stac_object.common_metadata.start_datetime
                if dt is None:
                    raise TemplateError('Item {} does not have a datetime or '
                                        'datetime range set; cannot template {} in {}'.format(
                                            stac_object, template_var, self.template))

                if template_var == 'year':
                    return dt.year
                if template_var == 'month':
                    return dt.month
                if template_var == 'day':
                    return dt.day
                if template_var == 'date':
                    return dt.date().isoformat()

                # Collection
                if template_var == 'collection':
                    if stac_object.collection_id is not None:
                        return stac_object.collection_id
                    raise TemplateError(
                        'Item {} does not have a collection ID set; cannot template {} in {}'.
                        format(stac_object, template_var, self.template))
            else:
                raise TemplateError('"{}" cannot be used to template non-Item {} in {}'.format(
                    template_var, stac_object, self.template))

        # Allow dot-notation properties for arbitrary object values.
        props = template_var.split('.')
        prop_location = None
        error = TemplateError('Cannot find property {} on {} for template {}'.format(
            template_var, stac_object, self.template))

        try:
            if hasattr(stac_object, props[0]):
                prop_location = stac_object
            elif hasattr(
                    stac_object,
                    "properties") and stac_object.properties and props[0] in stac_object.properties:
                prop_location = stac_object.properties
            elif hasattr(stac_object, "extra_fields"
                         ) and stac_object.extra_fields and props[0] in stac_object.extra_fields:
                prop_location = stac_object.extra_fields
            else:
                raise error

            v = prop_location
            for prop in template_var.split('.'):
                if type(v) is dict:
                    if prop not in v:
                        raise error
                    v = v[prop]
                else:
                    if not hasattr(v, prop):
                        raise error
                    v = getattr(v, prop)
        except TemplateError as e:
            if template_var in self.defaults:
                return self.defaults[template_var]
            raise e

        return v

    def get_template_values(self, stac_object):
        """Gets a dictionary of template variables to values derived from
        the given stac_object. If the template vars cannot be found in the
        stac object, and defaults was supplied to this template, a default
        value is used; if there is no default then this will raise an error.

        Args:
            stac_object (STACObject): The STACObject to derive template
                variable values from.

        Returns:
            [dict]: A dictionary with keys being the template variables
                and values being the respective values based on the given
                stac object.

        Raises:
            TemplateError: If a value for a template variable cannot be
                derived from the stac object and there is no default,
                this error will be raised.
        """
        return OrderedDict([(k, self._get_template_value(stac_object, k))
                            for k in self.template_vars])

    def substitute(self, stac_object):
        """Substitutes the values derived from
        :meth:`~pystac.layout.LayoutTemplate.get_template_values` into
        the template string for this template.

        Args:
            stac_object (STACObject): The STACObject to derive template
                variable values from.

        Returns:
            [str]: The original template supplied to this LayoutTemplate
                with template variables replaced by the values derived
                from this stac object.

        Raises:
            TemplateError: If a value for a template variable cannot be
                derived from the stac object and there is no default,
                this error will be raised.
        """
        parts = self.get_template_values(stac_object)

        s = self.template
        for key, value in parts.items():
            s = s.replace('${' + '{}'.format(key) + '}', '{}'.format(value))
        return s


class HrefLayoutStrategy(ABC):
    """Base class for HREF Layout strategies."""
    def get_href(self, stac_object, parent_dir, is_root=False):
        stac_object_type = stac_object.STAC_OBJECT_TYPE
        if stac_object_type == pystac.STACObjectType.CATALOG:
            return self.get_catalog_href(stac_object, parent_dir, is_root)
        elif stac_object_type == pystac.STACObjectType.COLLECTION:
            return self.get_collection_href(stac_object, parent_dir, is_root)
        elif stac_object_type == pystac.STACObjectType.ITEM:
            return self.get_item_href(stac_object, parent_dir)
        else:
            raise pystac.STACError('Unknown STAC object type {}'.format(stac_object_type))

    @abstractmethod
    def get_catalog_href(self, cat, parent_dir, is_root):
        pass

    @abstractmethod
    def get_collection_href(self, col, parent_dir, is_root):
        pass

    @abstractmethod
    def get_item_href(self, item, parent_dir):
        pass


class CustomLayoutStrategy(HrefLayoutStrategy):
    """Layout strategy that allows users to supply functions to dictate
    stac object paths.

    Args:
        catalog_func (Callable[Catalog, str, bool] -> str): A function that takes
            an catalog, a parent directory, and a flag specifying whether
            or not this catalog is the root. If it is the root, its usually
            best to not create a subdirectory and put the Catalog file directly
            in the parent directory. Must return the string path.
        collection_func (Callable[Catalog, str, bool] -> str): A function that
            is used for collections in the same manner at ``catalog_func``. This
            takes the same parameters.
        item_func  (Callable[Catalog, str] -> str): A function that takes
            an item and a parent directory and returns the path to be used
            for the item.
        fallback_strategy (HrefLayoutStrategy): The fallback strategy to
            use if a function is not provided for a stac object type. Defaults to
            :class:`~pystac.layout.BestPracticesLayoutStrategy`
    """
    def __init__(self,
                 catalog_func=None,
                 collection_func=None,
                 item_func=None,
                 fallback_strategy=None):
        self.item_func = item_func
        self.collection_func = collection_func
        self.catalog_func = catalog_func
        if fallback_strategy is None:
            fallback_strategy = BestPracticesLayoutStrategy()
        self.fallback_strategy = fallback_strategy

    def get_catalog_href(self, cat, parent_dir, is_root):
        if self.catalog_func is not None:
            result = self.catalog_func(cat, parent_dir, is_root)
            if result is not None:
                return result
        return self.fallback_strategy.get_catalog_href(cat, parent_dir, is_root)

    def get_collection_href(self, col, parent_dir, is_root):
        if self.collection_func is not None:
            result = self.collection_func(col, parent_dir, is_root)
            if result is not None:
                return result
        return self.fallback_strategy.get_collection_href(col, parent_dir, is_root)

    def get_item_href(self, item, parent_dir):
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
        catalog_template (str): The template string to use for catalog paths.
            Must be a valid template string that can be used by
            :class:`~pystac.layout.LayoutTemplate`
        collection_template (str): The template string to use for collection paths.
            Must be a valid template string that can be used by
            :class:`~pystac.layout.LayoutTemplate`
        item_template (str): The template string to use for item paths.
            Must be a valid template string that can be used by
            :class:`~pystac.layout.LayoutTemplate`
        fallback_strategy (HrefLayoutStrategy): The fallback strategy to
            use if a template is not provided. Defaults to
            :class:`~pystac.layout.BestPracticesLayoutStrategy`
    """
    def __init__(self,
                 catalog_template=None,
                 collection_template=None,
                 item_template=None,
                 fallback_strategy=None):
        self.catalog_template = LayoutTemplate(
            catalog_template) if catalog_template is not None else None
        self.collection_template = LayoutTemplate(
            collection_template) if collection_template is not None else None
        self.item_template = LayoutTemplate(item_template) if item_template is not None else None

        if fallback_strategy is None:
            fallback_strategy = BestPracticesLayoutStrategy()
        self.fallback_strategy = fallback_strategy

    def get_catalog_href(self, cat, parent_dir, is_root):
        if is_root or self.catalog_template is None:
            return self.fallback_strategy.get_catalog_href(cat, parent_dir, is_root)
        else:
            template_path = self.catalog_template.substitute(cat)
            if not template_path.endswith('.json'):
                template_path = os.path.join(template_path, cat.DEFAULT_FILE_NAME)

            return os.path.join(parent_dir, template_path)

    def get_collection_href(self, col, parent_dir, is_root):
        if is_root or self.collection_template is None:
            return self.fallback_strategy.get_collection_href(col, parent_dir, is_root)
        else:
            template_path = self.collection_template.substitute(col)
            if not template_path.endswith('.json'):
                template_path = os.path.join(template_path, col.DEFAULT_FILE_NAME)

            return os.path.join(parent_dir, template_path)

    def get_item_href(self, item, parent_dir):
        if self.item_template is None:
            return self.fallback_strategy.get_item_href(item, parent_dir)
        else:
            template_path = self.item_template.substitute(item)
            if not template_path.endswith('.json'):
                template_path = os.path.join(template_path, '{}.json'.format(item.id))

            return os.path.join(parent_dir, template_path)


class BestPracticesLayoutStrategy(HrefLayoutStrategy):
    """Layout strategy that represents the catalog layout described
    in the `STAC Best Practices documentation
    <https://github.com/radiantearth/stac-spec/blob/v1.0.0-beta.2/best-practices.md>`_

    For a root catalog or collection, this will use the filename 'catalog.json'
    or 'collection.json' to the given directory. For a non-root catalog or collection,
    the ID will be used as a subdirectory, e.g. ``${id}/catalog.json`` or
    ``${id}/collection.json``. For items, a subdirectory with a name of the item
    ID will be made, and the item ID will be used in the filename, i.e.
    ``${id}/${id}.json``

    All paths are appended to the parent directory.
    """
    def get_catalog_href(self, cat, parent_dir, is_root):
        if is_root:
            cat_root = parent_dir
        else:
            cat_root = os.path.join(parent_dir, '{}'.format(cat.id))

        return os.path.join(cat_root, cat.DEFAULT_FILE_NAME)

    def get_collection_href(self, col, parent_dir, is_root):
        if is_root:
            col_root = parent_dir
        else:
            col_root = os.path.join(parent_dir, '{}'.format(col.id))

        return os.path.join(col_root, col.DEFAULT_FILE_NAME)

    def get_item_href(self, item, parent_dir):
        item_root = os.path.join(parent_dir, '{}'.format(item.id))

        return os.path.join(item_root, '{}.json'.format(item.id))
