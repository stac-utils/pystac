from copy import copy, deepcopy
from datetime import datetime as Datetime
from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    TYPE_CHECKING,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

import dateutil.parser
from dateutil import tz

import pystac
from pystac import STACObjectType, CatalogType
from pystac.asset import Asset
from pystac.catalog import Catalog
from pystac.layout import HrefLayoutStrategy
from pystac.link import Link
from pystac.utils import datetime_to_str, get_required

if TYPE_CHECKING:
    from pystac.item import Item as Item_Type

T = TypeVar("T")


class SpatialExtent:
    """Describes the spatial extent of a Collection.

    Args:
        bboxes (List[List[float]]): A list of bboxes that represent the spatial
            extent of the collection. Each bbox can be 2D or 3D. The length of the bbox
            array must be 2*n where n is the number of dimensions. For example, a
            2D Collection with only one bbox would be [[xmin, ymin, xmax, ymax]]

    Attributes:
        bboxes (List[List[float]]): A list of bboxes that represent the spatial
            extent of the collection. Each bbox can be 2D or 3D. The length of the bbox
            array must be 2*n where n is the number of dimensions. For example, a
            2D Collection with only one bbox would be [[xmin, ymin, xmax, ymax]]
    """

    def __init__(self, bboxes: Union[List[List[float]], List[float]]) -> None:
        # A common mistake is to pass in a single bbox instead of a list of bboxes.
        # Account for this by transforming the input in that case.
        if isinstance(bboxes, list) and isinstance(bboxes[0], float):
            self.bboxes: List[List[float]] = [cast(List[float], bboxes)]
        else:
            self.bboxes = cast(List[List[float]], bboxes)

    def to_dict(self) -> Dict[str, Any]:
        """Generate a dictionary representing the JSON of this SpatialExtent.

        Returns:
            dict: A serialization of the SpatialExtent that can be written out as JSON.
        """
        d = {"bbox": self.bboxes}
        return d

    def clone(self) -> "SpatialExtent":
        """Clones this object.

        Returns:
            SpatialExtent: The clone of this object.
        """
        return SpatialExtent(deepcopy(self.bboxes))

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "SpatialExtent":
        """Constructs an SpatialExtent from a dict.

        Returns:
            SpatialExtent: The SpatialExtent deserialized from the JSON dict.
        """
        return SpatialExtent(bboxes=d["bbox"])

    @staticmethod
    def from_coordinates(coordinates: List[Any]) -> "SpatialExtent":
        """Constructs a SpatialExtent from a set of coordinates.

        This method will only produce a single bbox that covers all points
        in the coordinate set.

        Args:
            coordinates (List[float]): Coordinates to derive the bbox from.

        Returns:
            SpatialExtent: A SpatialExtent with a single bbox that covers the
            given coordinates.
        """

        def process_coords(
            coord_lists: List[Any],
            xmin: Optional[float] = None,
            ymin: Optional[float] = None,
            xmax: Optional[float] = None,
            ymax: Optional[float] = None,
        ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
            for coord in coord_lists:
                if isinstance(coord[0], list):
                    xmin, ymin, xmax, ymax = process_coords(
                        coord, xmin, ymin, xmax, ymax
                    )
                else:
                    x, y = coord
                    if xmin is None or x < xmin:
                        xmin = x
                    elif xmax is None or xmax < x:
                        xmax = x
                    if ymin is None or y < ymin:
                        ymin = y
                    elif ymax is None or ymax < y:
                        ymax = y
            return xmin, ymin, xmax, ymax

        xmin, ymin, xmax, ymax = process_coords(coordinates)

        if xmin is None or ymin is None or xmax is None or ymax is None:
            raise ValueError(
                f"Could not determine bounds from coordinate sequence {coordinates}"
            )

        return SpatialExtent([[xmin, ymin, xmax, ymax]])


class TemporalExtent:
    """Describes the temporal extent of a Collection.

    Args:
        intervals (List[List[datetime]]):  A list of two datetimes wrapped in a list,
        representing the temporal extent of a Collection. Open date ranges are supported
        by setting either the start (the first element of the interval) or the end (the
        second element of the interval) to None.


    Attributes:
        intervals (List[List[datetime]]):  A list of two datetimes wrapped in a list,
        representing the temporal extent of a Collection. Open date ranges are
        represented by either the start (the first element of the interval) or the
        end (the second element of the interval) being None.

    Note:
        Datetimes are required to be in UTC.
    """

    def __init__(
        self, intervals: Union[List[List[Optional[Datetime]]], List[Optional[Datetime]]]
    ):
        # A common mistake is to pass in a single interval instead of a
        # list of intervals. Account for this by transforming the input
        # in that case.
        if isinstance(intervals, list) and isinstance(intervals[0], Datetime):
            self.intervals = [cast(List[Optional[Datetime]], intervals)]
        else:
            self.intervals = cast(List[List[Optional[Datetime]]], intervals)

    def to_dict(self) -> Dict[str, Any]:
        """Generate a dictionary representing the JSON of this TemporalExtent.

        Returns:
            dict: A serialization of the TemporalExtent that can be written out as JSON.
        """
        encoded_intervals: List[List[Optional[str]]] = []
        for i in self.intervals:
            start = None
            end = None

            if i[0] is not None:
                start = datetime_to_str(i[0])

            if i[1] is not None:
                end = datetime_to_str(i[1])

            encoded_intervals.append([start, end])

        d = {"interval": encoded_intervals}
        return d

    def clone(self) -> "TemporalExtent":
        """Clones this object.

        Returns:
            TemporalExtent: The clone of this object.
        """
        return TemporalExtent(intervals=deepcopy(self.intervals))

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "TemporalExtent":
        """Constructs an TemporalExtent from a dict.

        Returns:
            TemporalExtent: The TemporalExtent deserialized from the JSON dict.
        """
        parsed_intervals: List[List[Optional[Datetime]]] = []
        for i in d["interval"]:
            start = None
            end = None

            if i[0]:
                start = dateutil.parser.parse(i[0])
            if i[1]:
                end = dateutil.parser.parse(i[1])
            parsed_intervals.append([start, end])

        return TemporalExtent(intervals=parsed_intervals)

    @staticmethod
    def from_now() -> "TemporalExtent":
        """Constructs an TemporalExtent with a single open interval that has
        the start time as the current time.

        Returns:
            TemporalExtent: The resulting TemporalExtent.
        """
        return TemporalExtent(
            intervals=[[Datetime.utcnow().replace(microsecond=0), None]]
        )


class Extent:
    """Describes the spatiotemporal extents of a Collection.

    Args:
        spatial (SpatialExtent): Potential spatial extent covered by the collection.
        temporal (TemporalExtent): Potential temporal extent covered by the collection.

    Attributes:
        spatial (SpatialExtent): Potential spatial extent covered by the collection.
        temporal (TemporalExtent): Potential temporal extent covered by the collection.
    """

    def __init__(self, spatial: SpatialExtent, temporal: TemporalExtent):
        self.spatial = spatial
        self.temporal = temporal

    def to_dict(self) -> Dict[str, Any]:
        """Generate a dictionary representing the JSON of this Extent.

        Returns:
            dict: A serialization of the Extent that can be written out as JSON.
        """
        d = {"spatial": self.spatial.to_dict(), "temporal": self.temporal.to_dict()}

        return d

    def clone(self) -> "Extent":
        """Clones this object.

        Returns:
            Extent: The clone of this extent.
        """
        return Extent(spatial=copy(self.spatial), temporal=copy(self.temporal))

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Extent":
        """Constructs an Extent from a dict.

        Returns:
            Extent: The Extent deserialized from the JSON dict.
        """

        # Handle pre-0.8 spatial extents
        spatial_extent = d["spatial"]
        if isinstance(spatial_extent, list):
            spatial_extent_dict: Dict[str, Any] = {"bbox": [spatial_extent]}
        else:
            spatial_extent_dict = spatial_extent

        # Handle pre-0.8 temporal extents
        temporal_extent = d["temporal"]
        if isinstance(temporal_extent, list):
            temporal_extent_dict: Dict[str, Any] = {"interval": [temporal_extent]}
        else:
            temporal_extent_dict = temporal_extent

        return Extent(
            SpatialExtent.from_dict(spatial_extent_dict),
            TemporalExtent.from_dict(temporal_extent_dict),
        )

    @staticmethod
    def from_items(items: Iterable["Item_Type"]) -> "Extent":
        """Create an Extent based on the datetimes and bboxes of a list of items.

        Args:
            items (List[Item]): A list of items to derive the extent from.

        Returns:
            Extent: An Extent that spatially and temporally covers all of the
                given items.
        """
        bounds_values: List[List[float]] = [
            [float("inf")],
            [float("inf")],
            [float("-inf")],
            [float("-inf")],
        ]
        datetimes: List[Datetime] = []
        starts: List[Datetime] = []
        ends: List[Datetime] = []

        for item in items:
            if item.bbox is not None:
                for i in range(0, 4):
                    bounds_values[i].append(item.bbox[i])
            if item.datetime is not None:
                datetimes.append(item.datetime)
            if item.common_metadata.start_datetime is not None:
                starts.append(item.common_metadata.start_datetime)
            if item.common_metadata.end_datetime is not None:
                ends.append(item.common_metadata.end_datetime)

        if not any(datetimes + starts):
            start_timestamp = None
        else:
            start_timestamp = min(
                [
                    dt if dt.tzinfo else dt.replace(tzinfo=tz.UTC)
                    for dt in datetimes + starts
                ]
            )
        if not any(datetimes + ends):
            end_timestamp = None
        else:
            end_timestamp = max(
                [
                    dt if dt.tzinfo else dt.replace(tzinfo=tz.UTC)
                    for dt in datetimes + ends
                ]
            )

        spatial = SpatialExtent(
            [
                [
                    min(bounds_values[0]),
                    min(bounds_values[1]),
                    max(bounds_values[2]),
                    max(bounds_values[3]),
                ]
            ]
        )
        temporal = TemporalExtent([[start_timestamp, end_timestamp]])

        return Extent(spatial, temporal)


class Provider:
    """Provides information about a provider of STAC data. A provider is any of the
    organizations that captured or processed the content of the collection and therefore
    influenced the data offered by this collection. May also include information about
    the final storage provider hosting the data.

    Args:
        name (str): The name of the organization or the individual.
        description (str): Optional multi-line description to add further provider
            information such as processing details for processors and producers,
            hosting details for hosts or basic contact information.
        roles (List[str]): Optional roles of the provider. Any of
            licensor, producer, processor or host.
        url (str): Optional homepage on which the provider describes the dataset
            and publishes contact information.

    Attributes:
        name (str): The name of the organization or the individual.
        description (str): Optional multi-line description to add further provider
            information such as processing details for processors and producers,
            hosting details for hosts or basic contact information.
        roles (List[str]): Optional roles of the provider. Any of
            licensor, producer, processor or host.
        url (str): Optional homepage on which the provider describes the dataset
            and publishes contact information.
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        roles: Optional[List[str]] = None,
        url: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.roles = roles
        self.url = url

    def to_dict(self) -> Dict[str, Any]:
        """Generate a dictionary representing the JSON of this Provider.

        Returns:
            dict: A serialization of the Provider that can be written out as JSON.
        """
        d: Dict[str, Any] = {"name": self.name}
        if self.description is not None:
            d["description"] = self.description
        if self.roles is not None:
            d["roles"] = self.roles
        if self.url is not None:
            d["url"] = self.url

        return d

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Provider":
        """Constructs an Provider from a dict.

        Returns:
            TemporalExtent: The Provider deserialized from the JSON dict.
        """
        return Provider(
            name=d["name"],
            description=d.get("description"),
            roles=d.get("roles"),
            url=d.get("url"),
        )


class RangeSummary(Generic[T]):
    def __init__(self, minimum: T, maximum: T):
        self.minimum = minimum
        self.maximum = maximum

    def to_dict(self) -> Dict[str, Any]:
        return {"minimum": self.minimum, "maximum": self.maximum}

    @classmethod
    def from_dict(cls, d: Dict[str, Any], typ: Type[T] = Any) -> "RangeSummary[T]":
        minimum: Optional[T] = get_required(d.get("minimum"), "RangeSummary", "minimum")
        maximum: Optional[T] = get_required(d.get("maximum"), "RangeSummary", "maximum")
        return cls(minimum=minimum, maximum=maximum)


class Summaries:
    def __init__(self, summaries: Dict[str, Any]) -> None:
        self._summaries = summaries

        self.lists: Dict[str, List[Any]] = {}
        self.ranges: Dict[str, RangeSummary[Any]] = {}
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.other: Dict[str, Any] = {}

        for prop_key, summary in summaries.items():
            self.add(prop_key, summary)

    def get_list(self, prop: str, typ: Type[T]) -> Optional[List[T]]:
        return self.lists.get(prop)

    def get_range(self, prop: str, typ: Type[T]) -> Optional[RangeSummary[T]]:
        return self.ranges.get(prop)

    def get_schema(self, prop: str) -> Optional[Dict[str, Any]]:
        return self.schemas.get(prop)

    def add(
        self,
        prop_key: str,
        summary: Union[List[Any], RangeSummary[Any], Dict[str, Any]],
    ) -> None:
        if isinstance(summary, list):
            self.lists[prop_key] = summary
        elif isinstance(summary, dict):
            if "minimum" in summary:
                self.ranges[prop_key] = RangeSummary[Any].from_dict(
                    cast(Dict[str, Any], summary)
                )
            else:
                self.schemas[prop_key] = summary
        elif isinstance(summary, RangeSummary):
            self.ranges[prop_key] = summary
        else:
            self.other[prop_key] = summary

    def remove(self, prop_key: str) -> None:
        self.lists.pop(prop_key, None)
        self.ranges.pop(prop_key, None)
        self.schemas.pop(prop_key, None)
        self.other.pop(prop_key, None)

    def is_empty(self):
        return not (
            any(self.lists) or any(self.ranges) or any(self.schemas) or any(self.other)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.lists,
            **{k: v.to_dict() for k, v in self.ranges.items()},
            **self.schemas,
            **self.other,
        }

    @classmethod
    def empty(cls) -> "Summaries":
        return Summaries({})


class Collection(Catalog):
    """A Collection extends the Catalog spec with additional metadata that helps
    enable discovery.

    Args:
        id (str): Identifier for the collection. Must be unique within the STAC.
        description (str): Detailed multi-line description to fully explain the
            collection. `CommonMark 0.28 syntax <http://commonmark.org/>`_ MAY
            be used for rich text representation.
        extent (Extent): Spatial and temporal extents that describe the bounds of
            all items contained within this Collection.
        title (str or None): Optional short descriptive one-line title for the
            collection.
        stac_extensions (List[str]): Optional list of extensions the Collection
            implements.
        href (str or None): Optional HREF for this collection, which be set as the
            collection's self link's HREF.
        catalog_type (str or None): Optional catalog type for this catalog. Must
            be one of the values in :class`~pystac.CatalogType`.
        license (str):  Collection's license(s) as a
            `SPDX License identifier <https://spdx.org/licenses/>`_,
            `various`, or `proprietary`. If collection includes
            data with multiple different licenses, use `various` and add a link for
            each. Defaults to 'proprietary'.
        keywords (List[str]): Optional list of keywords describing the collection.
        providers (List[Provider]): Optional list of providers of this Collection.
        summaries (dict): An optional map of property summaries,
            either a set of values or statistics such as a range.
        extra_fields (dict or None): Extra fields that are part of the top-level
            JSON properties of the Collection.

    Attributes:
        id (str): Identifier for the collection.
        description (str): Detailed multi-line description to fully explain the
            collection.
        extent (Extent): Spatial and temporal extents that describe the bounds of
            all items contained within this Collection.
        title (str or None): Optional short descriptive one-line title for the
            collection.
        stac_extensions (List[str]): Optional list of extensions the Collection
            implements.
        keywords (List[str] or None): Optional list of keywords describing the
            collection.
        providers (List[Provider] or None): Optional list of providers of this
            Collection.
        assets (Optional[Dict[str, Asset]]): Optional map of Assets
        summaries (dict or None): An optional map of property summaries,
            either a set of values or statistics such as a range.
        links (List[Link]): A list of :class:`~pystac.Link` objects representing
            all links associated with this Collection.
        extra_fields (dict or None): Extra fields that are part of the top-level
            JSON properties of the Catalog.
    """

    STAC_OBJECT_TYPE = STACObjectType.COLLECTION

    DEFAULT_FILE_NAME = "collection.json"
    """Default file name that will be given to this STAC object
    in a canonical format."""

    def __init__(
        self,
        id: str,
        description: str,
        extent: Extent,
        title: Optional[str] = None,
        stac_extensions: Optional[List[str]] = None,
        href: Optional[str] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
        catalog_type: Optional[CatalogType] = None,
        license: str = "proprietary",
        keywords: Optional[List[str]] = None,
        providers: Optional[List[Provider]] = None,
        summaries: Optional[Summaries] = None,
    ):
        super().__init__(
            id,
            description,
            title,
            stac_extensions,
            extra_fields,
            href,
            catalog_type or CatalogType.ABSOLUTE_PUBLISHED,
        )
        self.extent = extent
        self.license = license

        self.stac_extensions: List[str] = stac_extensions or []
        self.keywords = keywords
        self.providers = providers
        self.summaries = summaries or Summaries.empty()

        self.assets: Dict[str, Asset] = {}

    def __repr__(self) -> str:
        return "<Collection id={}>".format(self.id)

    def add_item(
        self,
        item: "Item_Type",
        title: Optional[str] = None,
        strategy: Optional[HrefLayoutStrategy] = None,
    ) -> None:
        super().add_item(item, title, strategy)
        item.set_collection(self)

    def to_dict(self, include_self_link: bool = True) -> Dict[str, Any]:
        d = super().to_dict(include_self_link)
        d["extent"] = self.extent.to_dict()
        d["license"] = self.license
        if self.stac_extensions is not None:
            d["stac_extensions"] = self.stac_extensions
        if self.keywords is not None:
            d["keywords"] = self.keywords
        if self.providers is not None:
            d["providers"] = list(map(lambda x: x.to_dict(), self.providers))
        if not self.summaries.is_empty():
            d["summaries"] = self.summaries.to_dict()
        if any(self.assets):
            d["assets"] = {k: v.to_dict() for k, v in self.assets.items()}

        return d

    def clone(self) -> "Collection":
        clone = Collection(
            id=self.id,
            description=self.description,
            extent=self.extent.clone(),
            title=self.title,
            stac_extensions=self.stac_extensions,
            extra_fields=self.extra_fields,
            catalog_type=self.catalog_type,
            license=self.license,
            keywords=self.keywords,
            providers=self.providers,
            summaries=self.summaries,
        )

        clone._resolved_objects.cache(clone)

        for link in self.links:
            if link.rel == "root":
                # Collection __init__ sets correct root to clone; don't reset
                # if the root link points to self
                root_is_self = link.is_resolved() and link.target is self
                if not root_is_self:
                    clone.set_root(None)
                    clone.add_link(link.clone())
            else:
                clone.add_link(link.clone())

        return clone

    @classmethod
    def from_dict(
        cls,
        d: Dict[str, Any],
        href: Optional[str] = None,
        root: Optional[Catalog] = None,
        migrate: bool = False,
    ) -> "Collection":
        if migrate:
            result = pystac.read_dict(d, href=href, root=root)
            if not isinstance(result, Collection):
                raise pystac.STACError(f"{result} is not a Catalog")
            return result

        catalog_type = CatalogType.determine_type(d)

        d = deepcopy(d)
        id = d.pop("id")
        description = d.pop("description")
        license = d.pop("license")
        extent = Extent.from_dict(d.pop("extent"))
        title = d.get("title")
        stac_extensions = d.get("stac_extensions")
        keywords = d.get("keywords")
        providers = d.get("providers")
        if providers is not None:
            providers = list(map(lambda x: Provider.from_dict(x), providers))
        summaries = d.get("summaries")
        if summaries is not None:
            summaries = Summaries(summaries)

        assets: Optional[Dict[str, Any]] = d.get("assets", None)
        links = d.pop("links")

        d.pop("stac_version")

        collection = Collection(
            id=id,
            description=description,
            extent=extent,
            title=title,
            stac_extensions=stac_extensions,
            extra_fields=d,
            license=license,
            keywords=keywords,
            providers=providers,
            summaries=summaries,
            href=href,
            catalog_type=catalog_type,
        )

        for link in links:
            if link["rel"] == "root":
                # Remove the link that's generated in Catalog's constructor.
                collection.remove_links("root")

            if link["rel"] != "self" or href is None:
                collection.add_link(Link.from_dict(link))

        if assets is not None:
            for asset_key, asset_dict in assets.items():
                collection.add_asset(asset_key, Asset(asset_dict))

        return collection

    def get_assets(self) -> Dict[str, Asset]:
        """Get this item's assets.

        Returns:
            Dict[str, Asset]: A copy of the dictionary of this item's assets.
        """
        return dict(self.assets.items())

    def add_asset(self, key: str, asset: Asset) -> None:
        """Adds an Asset to this item.

        Args:
            key (str): The unique key of this asset.
            asset (Asset): The Asset to add.
        """
        asset.set_owner(self)
        self.assets[key] = asset

    def update_extent_from_items(self) -> None:
        """
        Update datetime and bbox based on all items to a single bbox and time window.
        """
        self.extent = Extent.from_items(self.get_all_items())

    def full_copy(
        self, root: Optional["Catalog"] = None, parent: Optional["Catalog"] = None
    ) -> "Collection":
        return cast(Collection, super().full_copy(root, parent))

    @classmethod
    def from_file(
        cls, href: str, stac_io: Optional[pystac.StacIO] = None
    ) -> "Collection":
        result = super().from_file(href, stac_io)
        if not isinstance(result, Collection):
            raise pystac.STACTypeError(f"{result} is not a {Collection}.")
        return result
