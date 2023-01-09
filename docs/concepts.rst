Concepts
########

This page will give an overview of some important concepts to understand when working
with PySTAC. If you want to check code examples, see the :ref:`tutorials`.

.. _stac_version_support:

STAC Spec Version Support
=========================

The latest version of PySTAC supports STAC Spec |stac_version| and will automatically
update any catalogs to this version. To work with older versions of the STAC Spec,
please use an older version of PySTAC:

=================  ==============
STAC Spec Version  PySTAC Version
=================  ==============
>=1.0                Latest
0.9                0.4.*
0.8                0.3.*
<0.8               *Not supported*
=================  ==============

Reading STACs
=============

PySTAC can read STAC data from JSON. Generally users read in the root catalog, and then
use the python objects to crawl through the data. Once you read in the root of the STAC,
you can work with the STAC in memory.

.. code-block:: python

   from pystac import Catalog

   catalog = Catalog.from_file('/some/example/catalog.json')

   for root, catalogs, items in catalog.walk():
       # Do interesting things with the STAC data.

To see how to hook into PySTAC for reading from alternate URIs such as cloud object
storage, see :ref:`using stac_io`.

Writing STACs
=============

While working with STACs in-memory don't require setting file paths, in order to save a
STAC, you'll need to give each STAC object a ``self`` link that describes the location
of where it should be saved to. Luckily, PySTAC makes it easy to create a STAC catalog
with a :stac-spec:`canonical layout <best-practices.md#catalog-layout>` and with the
links that follow the :stac-spec:`best practices <best-practices.md#use-of-links>`. You
simply call ``normalize_hrefs`` with the root directory of where the STAC will be saved,
and then call ``save`` with the type of catalog (described in the :ref:`catalog types`
section) that matches your use case.

.. code-block:: python

   from pystac import (Catalog, CatalogType)

   catalog = Catalog.from_file('/some/example/catalog.json')
   catalog.normalize_hrefs('/some/copy/')
   catalog.save(catalog_type=CatalogType.SELF_CONTAINED)

   copycat = Catalog.from_file('/some/copy/catalog.json')


Normalizing HREFs
-----------------

The ``normalize_hrefs`` call sets HREFs for all the links in the STAC according to the
Catalog, Collection and Items, all based off of the root URI that is passed in:

.. code-block:: python

    catalog.normalize_hrefs('/some/location')
    catalog.save(catalog_type=CatalogType.SELF_CONTAINED)

This will lay out the HREFs of the STAC according to the :stac-spec:`best practices
document <best-practices.md>`.

Layouts
~~~~~~~

PySTAC provides a few different strategies for laying out the HREFs of a STAC.
To use them you can pass in a strategy to the normalize_hrefs call.

Using templates
'''''''''''''''

You can utilize template strings to determine the file paths of HREFs set on Catalogs,
Collection or Items. These templates use python format strings, which can name
the property or attribute of the item you want to use for replacing the template
variable. For example:

.. code-block:: python

    from pystac.layout import TemplateLayoutStrategy

    strategy = TemplateLayoutStrategy(item_template="${collection}/${year}/${month}")
    catalog.normalize_hrefs('/some/location', strategy=strategy)
    catalog.save(catalog_type=CatalogType.SELF_CONTAINED)

The above code will save items in subfolders based on the collection ID, year and month
of it's datetime (or start_datetime if a date range is defined and no datetime is
defined). Note that the forward slash (``/``) should be used as path separator in the
template string regardless of the system path separator (thus both in POSIX-compliant
and Windows environments).

You can use dot notation to specify attributes of objects or keys in dictionaries for
template variables. PySTAC will look at the object, it's ``properties`` and its
``extra_fields`` for property names or dictionary keys. Some special cases, like
``year``, ``month``, ``day`` and ``date`` exist for datetime on Items, as well as
``collection`` for Item's Collection's ID.

See the documentation on :class:`~pystac.layout.LayoutTemplate` for more documentation
on how layout templates work.

Using custom functions
''''''''''''''''''''''

If you want to build your own strategy, you can subclass ``HrefLayoutStrategy`` or use
:class:`~pystac.layout.CustomLayoutStrategy` to provide functions that work with
Catalogs, Collections or Items. Similar to the templating strategy, you can provide a
fallback strategy (which defaults to
:class:`~pystac.layout.BestPracticesLayoutStrategy`) for any stac object type that you
don't supply a function for.

.. _catalog types:

Catalog Types
-------------

The STAC :stac-spec:`best practices document <best-practices.md>` lays out different
catalog types, and how their links should be formatted. A brief description is below,
but check out the document for the official take on these types:

The catalog types will also dictate the asset HREF formats. Asset HREFs in any catalog
type can be relative or absolute may be absolute depending on their location; see the
section on :ref:`rel vs abs asset` below.


Self-Contained Catalogs
~~~~~~~~~~~~~~~~~~~~~~~

A self-contained catalog (indicated by ``catalog_type=CatalogType.SELF_CONTAINED``)
applies to STACs that do not have a long term location, and can be moved around. These
STACs are useful for copying data to and from locations, without having to change any
link metadata.

A self-contained catalog has two important properties:

- It contains only relative links
- It contains **no** self links.

For a catalog that is the most easy to copy around, it's recommended that item assets
use relative links, and reside in the same directory as the item's STAC metadata file.

Relative Published Catalogs
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A relative published catalog (indicated by
``catalog_type=CatalogType.RELATIVE_PUBLISHED``) is one that is tied at it's root to a
specific location, but otherwise contains relative links. This is designed so that a
self-contained catalog can be 'published' online by just adding one field (the self
link) to its root catalog.

A relative published catalog has the following properties:

- It contains **only one** self link: the root of the catalog contains a (necessarily
  absolute) link to it's published location.
- All other objects in the STAC contain relative links, and no self links.


Absolute Published Catalogs
~~~~~~~~~~~~~~~~~~~~~~~~~~~

An absolute published catalog (indicated by
``catalog_type=CatalogType.ABSOLUTE_PUBLISHED``) uses absolute links for everything. It
is preferable where possible, since it allows for the easiest provenance tracking out of
all the catalog types.

An absolute published catalog has the following properties:

- Each STAC object contains only absolute links.
- Each STAC object has a self link.

It is not recommended to have relative asset HREFs in an absolute published catalog.


Relative vs Absolute HREFs
--------------------------

HREFs inside a STAC for either links or assets can be relative or absolute.

Relative vs Absolute Link HREFs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Absolute links point to their file locations in a fully described way. Relative links
are relative to the linking object's file location. For example, if a catalog at
``/some/location/catalog.json`` has a link to an item that has an HREF set to
``item-id/item-id.json``, then that link should resolve to the absolute path
``/some/location/item-id/item-id.json``.

Links are set as absolute or relative HREFs at save time, as determine by the root
catalog's catalog_type :attr:`~pystac.Catalog.catalog_type`. This means that, even if
the stored HREF of the link is absolute, if the root
``catalog_type=CatalogType.RELATIVE_PUBLISHED`` or
``catalog_type=CatalogType.SELF_CONTAINED`` and subsequent serializing of the any links
in the catalog will produce a relative link, based on the self link of the parent
object.

You can make all the links of a catalog relative or absolute by setting the
:func:`Catalog.catalog_type` field then resaving the entire catalog.

.. _rel vs abs asset:

Relative vs Absolute Asset HREFs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Asset HREFs can also be relative or absolute. If an asset HREF is relative, then it is
relative to the Item's metadata file. For example, if the item at
``/some/location/item-id/item-id.json`` had an asset with an HREF of ``./image.tif``,
then the fully resolved path for that image would be
``/some/location/item-id/image.tif``

You can make all the asset HREFs of a catalog relative or absolute using the
:func:`Catalog.make_all_asset_hrefs_relative
<pystac.Catalog.make_all_asset_hrefs_relative>` and
:func:`Catalog.make_all_asset_hrefs_absolute
<pystac.Catalog.make_all_asset_hrefs_absolute>` methods. Note that these will not move
any files around, and if the file location does not share a common parent with the
asset's item's self HREF, then the asset HREF will remain absolute as no relative path
is possible.

Including a ``self`` link
-------------------------

Every stac object has a :func:`~pystac.STACObject.save_object` method, that takes as an
argument whether or not to include the object's self link. As noted in the section on
:ref:`catalog types`, a self link is necessarily absolute; if an object only contains
relative links, then it cannot contain the self link. PySTAC uses self links as a way of
tracking the object's file location, either what it was read from or it's pending save
location, so each object can have a self link even if you don't ever want that self link
written (e.g. if you are working with self-contained catalogs).

.. _using stac_io:

I/O in PySTAC
=============

The :class:`pystac.StacIO` class defines fundamental methods for I/O
operations within PySTAC, including serialization and deserialization to and from
JSON files and conversion to and from Python dictionaries. This is an abstract class
and should not be instantiated directly. However, PySTAC provides a
:class:`pystac.stac_io.DefaultStacIO` class with minimal implementations of these
methods. This default implementation provides support for reading and writing files
from the local filesystem as well as HTTP URIs (using ``urllib``). This class is
created automatically by all of the object-specific I/O methods (e.g.
:meth:`pystac.Catalog.from_file`), so most users will not need to instantiate this
class themselves.

If you are dealing with a STAC catalog with URIs that require authentication.
It is possible provide auth headers (or any other customer headers) to the
:class:`pystac.stac_io.DefaultStacIO`.

.. code-block:: python

  from pystac import Catalog
  from pystac import StacIO

  stac_io = StacIO.default()
  stac_io.headers = {"Authorization": "<some-auth-header>"}

  catalog = Catalog.from_file("<URI-requiring-auth>", stac_io=stac_io)


If you require more custom logic for I/O operations or would like to use a
3rd-party library for I/O operations (e.g. ``requests``),
you can create a sub-class of :class:`pystac.StacIO`
(or :class:`pystac.DefaultStacIO`) and customize the methods as
you see fit. You can then pass instances of this custom sub-class into the ``stac_io``
argument of most object-specific I/O methods. You can also use
:meth:`pystac.StacIO.set_default` in your client's ``__init__.py`` file to make this
sub-class the default :class:`pystac.StacIO` implementation throughout the library.

For example, this code will allow
for reading from AWS's S3 cloud object storage using `boto3
<https://boto3.amazonaws.com/v1/documentation/api/latest/index.html>`__:

.. code-block:: python

   from urllib.parse import urlparse
   import boto3
   from pystac import Link
   from pystac.stac_io import DefaultStacIO, StacIO

   class CustomStacIO(DefaultStacIO):
      def __init__(self):
         self.s3 = boto3.resource("s3")

      def read_text(
         self, source: Union[str, Link], *args: Any, **kwargs: Any
      ) -> str:
         parsed = urlparse(source)
         if parsed.scheme == "s3":
            bucket = parsed.netloc
            key = parsed.path[1:]

            obj = self.s3.Object(bucket, key)
            return obj.get()["Body"].read().decode("utf-8")
         else:
            return super().read_text(source, *args, **kwargs)

      def write_text(
         self, dest: Union[str, Link], txt: str, *args: Any, **kwargs: Any
      ) -> None:
         parsed = urlparse(dest)
         if parsed.scheme == "s3":
            bucket = parsed.netloc
            key = parsed.path[1:]
            self.s3.Object(bucket, key).put(Body=txt, ContentEncoding="utf-8")
         else:
            super().write_text(dest, txt, *args, **kwargs)

   StacIO.set_default(CustomStacIO)


If you only need to customize read operations you can inherit from
:class:`~pystac.stac_io.DefaultStacIO` and only overwrite the read method. For example,
to take advantage of connection pooling using a `requests.Session
<https://requests.kennethreitz.org/en/master>`__:

.. code-block:: python

   from urllib.parse import urlparse
   import requests
   from pystac.stac_io import DefaultStacIO, StacIO

   class ConnectionPoolingIO(DefaultStacIO):
      def __init__(self):
         self.session = requests.Session()

      def read_text(
         self, source: Union[str, Link], *args: Any, **kwargs: Any
      ) -> str:
         parsed = urlparse(uri)
         if parsed.scheme.startswith("http"):
            return self.session.get(uri).text
         else:
            return super().read_text(source, *args, **kwargs)

   StacIO.set_default(ConnectionPoolingIO)


.. _validation_concepts:

Validation
==========

PySTAC includes validation functionality that allows users to validate PySTAC objects as
well JSON-encoded STAC objects from STAC versions `0.8.0` and later.

Enabling validation
-------------------

To enable the validation feature you'll need to have installed PySTAC with the optional
dependency via:

.. code-block:: bash

   > pip install pystac[validation]

This installs the ``jsonschema`` package which is used with the default validator. If
you define your own validation class as described below, you are not required to have
this extra dependency.

Validating PySTAC objects
-------------------------

You can validate any :class:`~pystac.Catalog`, :class:`~pystac.Collection` or
:class:`~pystac.Item` by calling the :meth:`~pystac.STACObject.validate` method:

.. code-block:: python

   item.validate()

This will validate against the latest set of JSON schemas hosted at
https://schemas.stacspec.org, including any extensions that the object extends. If there
are validation errors, a :class:`~pystac.validation.STACValidationError` will be raised.

You can also call :meth:`~pystac.Catalog.validate_all` on a Catalog or Collection to
recursively walk through a catalog and validate all objects within it.

.. code-block:: python

   catalog.validate_all()

Validating STAC JSON
--------------------

You can validate STAC JSON represented as a ``dict`` using the
:meth:`pystac.validation.validate_dict` method:

.. code-block:: python

   import json
   from pystac.validation import validate_dict

   with open('/path/to/item.json') as f:
       js = json.load(f)
   validate_dict(js)

You can also recursively validate all of the catalogs, collections and items across STAC
versions using the :meth:`pystac.validation.validate_all` method:

.. code-block:: python

   import json
   from pystac.validation import validate_all

   with open('/path/to/catalog.json') as f:
       js = json.load(f)
   validate_all(js)

Using your own validator
------------------------

By default PySTAC uses the :class:`~pystac.validation.JsonSchemaSTACValidator`
implementation for validation. Users can define their own implementations of
:class:`~pystac.validation.STACValidator` and register it with pystac using
:meth:`pystac.validation.set_validator`.

The :class:`~pystac.validation.JsonSchemaSTACValidator` takes a
:class:`~pystac.validation.SchemaUriMap`, which by default uses the
:class:`~pystac.validation.schema_uri_map.DefaultSchemaUriMap`. If desirable, users cn
create their own implementation of :class:`~pystac.validation.SchemaUriMap` and register
a new instance of :class:`~pystac.validation.JsonSchemaSTACValidator` using that schema
map with :meth:`pystac.validation.set_validator`.

Extensions
==========

From the documentation on :stac-spec:`STAC Spec Extensions <extensions>`:

   Extensions to the core STAC specification provide additional JSON fields that can be
   used to better describe the data. Most tend to be about describing a particular
   domain or type of data, but some imply functionality.

This library makes an effort to support all extensions that are part of the
`stac-extensions GitHub org
<https://stac-extensions.github.io/#extensions-in-stac-extensions-organization>`__, and
we are committed to supporting all STAC Extensions at the "Candidate" maturity level or
above (see the `Extension Maturity
<https://stac-extensions.github.io/#extension-maturity>`__ documentation for details).

Accessing Extension Functionality
---------------------------------

Extension functionality is encapsulated in classes that are specific to the STAC
Extension (e.g. Electro-Optical, Projection, etc.) and STAC Object
(:class:`~pystac.Collection`, :class:`pystac.Item`, or :class:`pystac.Asset`). All
classes that extend these objects inherit from
:class:`pystac.extensions.base.PropertiesExtension`, and you can use the
``ext`` method on these classes to extend an object.

For instance, if you have an item that implements the :stac-ext:`Electro-Optical
Extension <eo>`, you can access the properties associated with that extension using
:meth:`EOExtension.ext <pystac.extensions.eo.EOExtension.ext>`:

.. code-block:: python

   import pystac
   from pystac.extensions.eo import EOExtension

   item = Item(...)  # See docs for creating an Item

   # Check that the Item implements the EO Extension
   if EOExtension.has_extension(item):
      eo_ext = EOExtension.ext(item)

      bands = eo_ext.bands
      cloud_cover = eo_ext.cloud_cover
      ...

.. note:: The ``ext`` method will raise an :exc:`~pystac.ExtensionNotImplemented`
   exception if the object does not implement that extension (e.g. if the extension
   URI is not in that object's :attr:`~pystac.STACObject.stac_extensions` list). In
   the example above, we check that the Item implements the EO Extension before calling
   :meth:`EOExtension.ext <pystac.extensions.eo.EOExtension.ext>` to handle this. See
   the `Adding an Extension`_ section below for details on adding an extension to an
   object.

See the documentation for each extension implementation for details on the supported
properties and other functionality.

Instances of :class:`~pystac.extensions.base.PropertiesExtension` have a
:attr:`~pystac.extensions.base.PropertiesExtension.properties` attribute that gives
access to the properties of the extended object. *This attribute is a reference to the
properties of the* :class:`~pystac.Item` *or* :class:`~pystac.Asset` *being extended and
can therefore mutate those properties.* For instance:

.. code-block:: python

   item = Item.from_file("tests/data-files/eo/eo-landsat-example.json")
   print(item.properties["eo:cloud_cover"])
   # 78

   eo_ext = EOExtension.ext(item)
   print(eo_ext.cloud_cover)
   # 78

   eo_ext.cloud_cover = 45
   print(item.properties["eo:cloud_cover"])
   # 45

There is also a
:attr:`~pystac.extensions.base.PropertiesExtension.additional_read_properties` attribute
that, if present, gives read-only access to properties of any objects that own the
extended object. For instance, an extended :class:`pystac.Asset` instance would have
read access to the properties of the :class:`pystac.Item` that owns it (if there is
one). If a property exists in both additional_read_properties and properties, the value
in additional_read_properties will take precedence.


An ``apply`` method is available on extended objects. This allows you to pass in
property values pertaining to the extension. Properties that are required by the
extension will be required arguments to the ``apply`` method. Optional properties will
have a default value of ``None``:

.. code-block:: python

   # Can also omit cloud_cover entirely...
   eo_ext.apply(0.5, bands, cloud_cover=None)


If you attempt to extend an object that is not supported by an extension, PySTAC will
throw a :class:`pystac.ExtensionTypeError`.


Adding an Extension
-------------------

You can add an extension to a STAC object that does not already implement that extension
using the :meth:`ExtensionManagementMixin.add_to
<pystac.extensions.base.ExtensionManagementMixin.add_to>` method. Any concrete
extension implementations that extend existing STAC objects should inherit from the
:class:`~pystac.extensions.base.ExtensionManagementMixin` class, and will therefore have
this method available. The
:meth:`~pystac.extensions.base.ExtensionManagementMixin.add_to` adds the correct schema
URI to the :attr:`~pystac.STACObject.stac_extensions` list for the object being
extended.

.. code-block:: python

   # Load a basic item without any extensions
   item = Item.from_file("tests/data-files/item/sample-item.json")
   print(item.stac_extensions)
   # []

   # Add the Electro-Optical extension
   EOExtension.add_to(item)
   print(item.stac_extensions)
   # ['https://stac-extensions.github.io/eo/v1.0.0/schema.json']

Extended Summaries
------------------

Extension classes like :class:`~pystac.extensions.eo.EOExtension` may also provide a
``summaries`` static method that can be used to extend the Collection summaries. This
method returns a class inheriting from
:class:`pystac.extensions.base.SummariesExtension` that provides tools for summarizing
the properties defined by that extension. These classes also hold a reference to the
Collection's :class:`pystac.Summaries` instance in the ``summaries`` attribute.

See :class:`pystac.extensions.eo.SummariesEOExtension` for an example implementation.

Item Asset properties
=====================

Properties that apply to Items can be found in two places: the Item's properties or in
any of an Item's Assets. If the property is on an Asset, it applies only that specific
asset. For example, gsd defined for an Item represents the best Ground Sample Distance
(resolution) for the data within the Item. However, some assets may be lower resolution
and thus have a higher gsd. In that case, the `gsd` can be found on the Asset.

See the STAC documentation on :stac-spec:`Additional Fields for Assets
<item-spec/item-spec.md#additional-fields-for-assets>` and the relevant :stac-spec:`Best
Practices <best-practices.md#common-use-cases-of-additional-fields-for-assets>` for more
information.

The implementation of this feature in PySTAC uses the method described here and is
consistent across Item and ItemExtensions. The bare property names represent values for
the Item only, but for each property where it is possible to set on both the Item or the
Asset there is a ``get_`` and ``set_`` methods that optionally take an Asset. For the
``get_`` methods, if the property is found on the Asset, the Asset's value is used;
otherwise the Item's value will be used. For the ``set_`` method, if an Asset is passed
in the value will be applied to the Asset and not the Item.

For example, if we have an Item with a ``gsd`` of 10 with three bands, and only asset
"band3" having a ``gsd`` of 20, the ``get_gsd`` method will behave in the following way:

  .. code-block:: python

     assert item.common_metadata.gsd == 10
     assert item.common_metadata.get_gsd() == 10
     assert item.common_metadata.get_gsd(item.asset['band1']) == 10
     assert item.common_metadata.get_gsd(item.asset['band3']) == 20

Similarly, if we set the asset at 'band2' to have a ``gsd`` of 30, it will only affect
that asset:

  .. code-block:: python

     item.common_metadata.set_gsd(30, item.assets['band2']
     assert item.common_metadata.gsd == 10
     assert item.common_metadata.get_gsd(item.asset['band2']) == 30

Manipulating STACs
==================

PySTAC is designed to allow for STACs to be manipulated in-memory. This includes
:ref:`copy stacs`, walking over all objects in a STAC and mutating their properties, or
using collection-style `map` methods for mapping over items.


Walking over a STAC
-------------------

You can walk through all sub-catalogs and items of a catalog with a method inspired
by the Python Standard Library `os.walk()
<https://docs.python.org/3/library/os.html#os.walk>`_ method: :func:`Catalog.walk()
<pystac.Catalog.walk>`:

.. code-block:: python

   for root, subcats, items in catalog.walk():
       # Root represents a catalog currently being walked in the tree
       root.title = '{} has been walked!'.format(root.id)

       # subcats represents any catalogs or collections owned by root
       for cat in subcats:
           cat.title = 'About to be walked!'

       # items represent all items that are contained by root
       for item in items:
           item.title = '{} - owned by {}'.format(item.id, root.id)

Mapping over Items
------------------

The :func:`Catalog.map_items <pystac.Catalog.map_items>` method is useful for
manipulating items in a STAC. This will create a full copy of the STAC, so will leave
the original catalog unmodified. In the method that manipulates and returns the modified
item, you can return multiple items, in case you are generating new objects (e.g.
creating a :class:`~pystac.LabelItem` for image items in a stac), or splitting items
into smaller chunks (e.g. tiling out large image items).

.. code-block:: python

   def modify_item_title(item):
       item.title = 'Some new title'
       return item

   def create_label_item(item):
       # Assumes the GeoJSON labels are in the
       # same location as the image
       img_href = item.assets['ortho'].href
       label_href = '{}.geojson'.format(os.path.splitext(img_href)[0])
       label_item = LabelItem(id='Labels',
                         geometry=item.geometry,
                         bbox=item.bbox,
                         datetime=datetime.utcnow(),
                         properties={},
                         label_description='labels',
                         label_type='vector',
                         label_properties='label',
                         label_classes=[
                         LabelClasses(classes=['one', 'two'],
                                      name='label')
                         ],
                         label_tasks=['classification'])
       label_item.add_source(item, assets=['ortho'])
       label_item.add_geojson_labels(label_href)

       return [item, label_item]


   c = catalog.map_items(modify_item_title)
   c = c.map_items(create_label_item)
   new_catalog = c

.. _copy stacs:

Copying STACs in-memory
-----------------------

The in-memory copying of STACs to create new ones is crucial to correct manipulations
and mutations of STAC data. The :func:`STACObject.full_copy
<pystac.STACObject.full_copy>` mechanism handles this in a way that ties the elements of
the copies STAC together correctly. This includes situations where there might be cycles
in the graph of connected objects of the STAC (which otherwise would be `a tree
<https://en.wikipedia.org/wiki/Tree_(graph_theory)>`_). For example, if a
:class:`~pystac.LabelItem` lists a :attr:`~pystac.LabelItem.source` that is an item also
contained in the root catalog; the full copy of the STAC will ensure that the
:class:`~pystac.Item` instance representing the source imagery item is the same instance
that is linked to by the :class:`~pystac.LabelItem`.

Resolving STAC objects
======================

PySTAC tries to only "resolve" STAC Objects - that is, load the metadata contained by
STAC files pointed to by links into Python objects in-memory - when necessary. It also
ensures that two links that point to the same object resolve to the same in-memory
object.

Lazy resolution of STAC objects
-------------------------------

Links are read only when they need to be. For instance, when you load a catalog using
:func:`Catalog.from_file <pystac.Catalog.from_file>`, the catalog and all of its links
are read into a :class:`~pystac.Catalog` instance. If you iterate through
:attr:`Catalog.links <pystac.Catalog.links>`, you'll see the :attr:`~pystac.Link.target`
of the :class:`~pystac.Link` will refer to a string - that is the HREF of the link.
However, if you call :func:`Catalog.get_items <pystac.Catalog.get_items>`, for instance,
you'll get back the actual :class:`~pystac.Item` instances that are referred to by each
item link in the Catalog. That's because at the time you call ``get_items``, PySTAC is
"resolving" the links for any link that represents an item in the catalog.

The resolution mechanism is accomplished through :func:`Link.resolve_stac_object
<pystac.Link.resolve_stac_object>`. Though this method is used extensively internally to
PySTAC, ideally this is completely transparent to users of PySTAC, and you won't have to
worry about how and when links get resolved. However, one important aspect to understand
is how object resolution caching happens.

Resolution Caching
------------------

The root :class:`~pystac.Catalog` instance of a STAC (the Catalog which is linked to by
every associated object's ``root`` link) contains a cache of resolved objects. This
cache points to in-memory instances of :class:`~pystac.STACObject` s that have already
been resolved through PySTAC crawling links associated with that root catalog. The cache
works off of the stac object's ID, which is why **it is necessary for every STAC object
in the catalog to have a unique identifier, which is unique across the entire STAC**.

When a link is being resolved from a STACObject that has it's root set, that root is
passed into the :func:`Link.resolve_stac_object <pystac.Link.resolve_stac_object>` call.
That root's :class:`~pystac.resolved_object_cache.ResolvedObjectCache` will be used to
ensure that if the link is pointing to an object that has already been resolved, then
that link will point to the same, single instance in the cache. This ensures working
with STAC objects in memory doesn't create a situation where multiple copies of the same
STAC objects are created from different links, manipulated, and written over each other.

Working with STAC JSON
======================

The ``pystac.serialization`` package has some functionality around working directly with
STAC JSON objects, without utilizing PySTAC object types. This is used internally by
PySTAC, but might also be useful to users working directly with JSON (e.g. on
validation).


Identifying STAC objects from JSON
----------------------------------

Users can identify STAC information, including the object type, version and extensions,
from JSON. The main method for this is
:func:`~pystac.serialization.identify_stac_object`, which returns an object that
contains the object type, the range of versions this object is valid for (according to
PySTAC's best guess), the common extensions implemented by this object, and any custom
extensions (represented by URIs to JSON Schemas).

.. code-block:: python

   from pystac.serialization import identify_stac_object

   json_dict = ...

   info = identify_stac_object(json_dict)

   # The object type
   info.object_type

   # The version range
   info.version_range

   # The common extensions
   info.common_extensions

   # The custom Extensions
   info.custom_extensions

Merging common properties
-------------------------

For pre-1.0.0 STAC, The :func:`~pystac.serialization.merge_common_properties` will take
a JSON dict that represents an item, and if it is associated with a collection, merge in
the collection's properties. You can pass in a dict that contains previously read
collections that caches collections by the HREF of the collection link and/or the
collection ID, which can help avoid multiple reads of
collection links.

Note that this feature was dropped in STAC 1.0.0-beta.1
