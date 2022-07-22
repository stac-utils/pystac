from html import escape
from copy import deepcopy
from datetime import datetime

from pystac.errors import STACTypeError
from pystac.html.jinja_env import get_jinja_env
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    TYPE_CHECKING,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from dateutil import tz

import pystac
from pystac import STACObjectType, CatalogType
from pystac.asset import Asset
from pystac.catalog import Catalog
from pystac.layout import HrefLayoutStrategy
from pystac.link import Link
from pystac.provider import Provider
from pystac.utils import datetime_to_str, str_to_datetime
from pystac.serialization import (
    identify_stac_object_type,
    identify_stac_object,
    migrate_to_latest,
)
from pystac.summaries import Summaries

if TYPE_CHECKING:
    from pystac.item import Item as Item_Type
    from pystac.provider import Provider as Provider_Type

T = TypeVar("T")
TemporalIntervals = Union[List[List[datetime]], List[List[Optional[datetime]]]]
TemporalIntervalsLike = Union[
    TemporalIntervals, List[datetime], List[Optional[datetime]]
]


class SpatialExtent:
    """Describes the spatial extent of a Collection.

    Args:
        bboxes : A list of bboxes that represent the spatial
            extent of the collection. Each bbox can be 2D or 3D. The length of the bbox
            array must be 2*n where n is the number of dimensions. For example, a
            2D Collection with only one bbox would be [[xmin, ymin, xmax, ymax]]

        extra_fields : Dictionary containing additional top-level fields defined on the
            Spatial Extent object.
    """

    bboxes: List[List[float]]
    """A list of bboxes that represent the spatial
    extent of the collection. Each bbox can be 2D or 3D. The length of the bbox
    array must be 2*n where n is the number of dimensions. For example, a
    2D Collection with only one bbox would be [[xmin, ymin, xmax, ymax]]"""

    extra_fields: Dict[str, Any]
    """Dictionary containing additional top-level fields defined on the Spatial
    Extent object."""

    def __init__(
        self,
        bboxes: Union[List[List[float]], List[float]],
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> None:
        # A common mistake is to pass in a single bbox instead of a list of bboxes.
        # Account for this by transforming the input in that case.
        if isinstance(bboxes, list) and isinstance(bboxes[0], float):
            self.bboxes: List[List[float]] = [cast(List[float], bboxes)]
        else:
            self.bboxes = cast(List[List[float]], bboxes)

        self.extra_fields = extra_fields or {}

    def to_dict(self) -> Dict[str, Any]:
        """Generate a dictionary representing the JSON of this SpatialExtent.

        Returns:
            dict: A serialization of the SpatialExtent that can be written out as JSON.
        """
        d = {"bbox": self.bboxes, **self.extra_fields}
        return d

    def clone(self) -> "SpatialExtent":
        """Clones this object.

        Returns:
            SpatialExtent: The clone of this object.
        """
        return SpatialExtent(
            bboxes=deepcopy(self.bboxes), extra_fields=deepcopy(self.extra_fields)
        )

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "SpatialExtent":
        """Constructs a SpatialExtent from a dict.

        Returns:
            SpatialExtent: The SpatialExtent deserialized from the JSON dict.
        """
        return SpatialExtent(
            bboxes=d["bbox"], extra_fields={k: v for k, v in d.items() if k != "bbox"}
        )

    @staticmethod
    def from_coordinates(
        coordinates: List[Any], extra_fields: Optional[Dict[str, Any]] = None
    ) -> "SpatialExtent":
        """Constructs a SpatialExtent from a set of coordinates.

        This method will only produce a single bbox that covers all points
        in the coordinate set.

        Args:
            coordinates : Coordinates to derive the bbox from.
            extra_fields : Dictionary containing additional top-level fields defined on
                the SpatialExtent object.

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

        return SpatialExtent(
            bboxes=[[xmin, ymin, xmax, ymax]], extra_fields=extra_fields
        )


class TemporalExtent:
    """Describes the temporal extent of a Collection.

    Args:
        intervals :  A list of two datetimes wrapped in a list,
            representing the temporal extent of a Collection. Open date ranges are
            supported by setting either the start (the first element of the interval)
            or the end (the second element of the interval) to None.

        extra_fields : Dictionary containing additional top-level fields defined on the
            Temporal Extent object.
    Note:
        Datetimes are required to be in UTC.
    """

    intervals: TemporalIntervals
    """A list of two datetimes wrapped in a list,
    representing the temporal extent of a Collection. Open date ranges are
    represented by either the start (the first element of the interval) or the
    end (the second element of the interval) being None."""

    extra_fields: Dict[str, Any]
    """Dictionary containing additional top-level fields defined on the Temporal
    Extent object."""

    def __init__(
        self,
        intervals: TemporalIntervals,
        extra_fields: Optional[Dict[str, Any]] = None,
    ):
        # A common mistake is to pass in a single interval instead of a
        # list of intervals. Account for this by transforming the input
        # in that case.
        if isinstance(intervals, list) and isinstance(intervals[0], datetime):
            self.intervals = intervals
        else:
            self.intervals = intervals

        self.extra_fields = extra_fields or {}

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

        d = {"interval": encoded_intervals, **self.extra_fields}
        return d

    def clone(self) -> "TemporalExtent":
        """Clones this object.

        Returns:
            TemporalExtent: The clone of this object.
        """
        return TemporalExtent(
            intervals=deepcopy(self.intervals), extra_fields=deepcopy(self.extra_fields)
        )

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "TemporalExtent":
        """Constructs an TemporalExtent from a dict.

        Returns:
            TemporalExtent: The TemporalExtent deserialized from the JSON dict.
        """
        parsed_intervals: List[List[Optional[datetime]]] = []
        for i in d["interval"]:
            start = None
            end = None

            if i[0]:
                start = str_to_datetime(i[0])
            if i[1]:
                end = str_to_datetime(i[1])
            parsed_intervals.append([start, end])

        return TemporalExtent(
            intervals=parsed_intervals,
            extra_fields={k: v for k, v in d.items() if k != "interval"},
        )

    @staticmethod
    def from_now() -> "TemporalExtent":
        """Constructs an TemporalExtent with a single open interval that has
        the start time as the current time.

        Returns:
            TemporalExtent: The resulting TemporalExtent.
        """
        return TemporalExtent(
            intervals=[[datetime.utcnow().replace(microsecond=0), None]]
        )


class Extent:
    """Describes the spatiotemporal extents of a Collection.

    Args:
        spatial : Potential spatial extent covered by the collection.
        temporal : Potential temporal extent covered by the collection.
        extra_fields : Dictionary containing additional top-level fields defined on the
            Extent object.
    """

    spatial: SpatialExtent
    """Potential spatial extent covered by the collection."""

    temporal: TemporalExtent
    """Potential temporal extent covered by the collection."""

    extra_fields: Dict[str, Any]
    """Dictionary containing additional top-level fields defined on the Extent
    object."""

    def __init__(
        self,
        spatial: SpatialExtent,
        temporal: TemporalExtent,
        extra_fields: Optional[Dict[str, Any]] = None,
    ):
        self.spatial = spatial
        self.temporal = temporal
        self.extra_fields = extra_fields or {}

    def to_dict(self) -> Dict[str, Any]:
        """Generate a dictionary representing the JSON of this Extent.

        Returns:
            dict: A serialization of the Extent that can be written out as JSON.
        """
        d = {
            "spatial": self.spatial.to_dict(),
            "temporal": self.temporal.to_dict(),
            **self.extra_fields,
        }

        return d

    def clone(self) -> "Extent":
        """Clones this object.

        Returns:
            Extent: The clone of this extent.
        """
        return Extent(
            spatial=self.spatial.clone(),
            temporal=self.temporal.clone(),
            extra_fields=deepcopy(self.extra_fields),
        )

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Extent":
        """Constructs an Extent from a dict.

        Returns:
            Extent: The Extent deserialized from the JSON dict.
        """
        return Extent(
            spatial=SpatialExtent.from_dict(d["spatial"]),
            temporal=TemporalExtent.from_dict(d["temporal"]),
            extra_fields={
                k: v for k, v in d.items() if k not in {"spatial", "temporal"}
            },
        )

    @staticmethod
    def from_items(
        items: Iterable["Item_Type"], extra_fields: Optional[Dict[str, Any]] = None
    ) -> "Extent":
        """Create an Extent based on the datetimes and bboxes of a list of items.

        Args:
            items : A list of items to derive the extent from.
            extra_fields : Optional dictionary containing additional top-level fields
                defined on the Extent object.

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
        datetimes: List[datetime] = []
        starts: List[datetime] = []
        ends: List[datetime] = []

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

        return Extent(spatial=spatial, temporal=temporal, extra_fields=extra_fields)


class Collection(Catalog):
    """A Collection extends the Catalog spec with additional metadata that helps
    enable discovery.

    Args:
        id : Identifier for the collection. Must be unique within the STAC.
        description : Detailed multi-line description to fully explain the
            collection. `CommonMark 0.29 syntax <https://commonmark.org/>`_ MAY
            be used for rich text representation.
        extent : Spatial and temporal extents that describe the bounds of
            all items contained within this Collection.
        title : Optional short descriptive one-line title for the
            collection.
        stac_extensions : Optional list of extensions the Collection
            implements.
        href : Optional HREF for this collection, which be set as the
            collection's self link's HREF.
        catalog_type : Optional catalog type for this catalog. Must
            be one of the values in :class`~pystac.CatalogType`.
        license :  Collection's license(s) as a
            `SPDX License identifier <https://spdx.org/licenses/>`_,
            `various`, or `proprietary`. If collection includes
            data with multiple different licenses, use `various` and add a link for
            each. Defaults to 'proprietary'.
        keywords : Optional list of keywords describing the collection.
        providers : Optional list of providers of this Collection.
        summaries : An optional map of property summaries,
            either a set of values or statistics such as a range.
        extra_fields : Extra fields that are part of the top-level
            JSON properties of the Collection.
        assets : A dictionary mapping string keys to :class:`~pystac.Asset` objects. All
            :class:`~pystac.Asset` values in the dictionary will have their
            :attr:`~pystac.Asset.owner` attribute set to the created Collection.
    """

    assets: Dict[str, Asset]
    """Map of Assets"""

    description: str
    """Detailed multi-line description to fully explain the collection."""

    extent: Extent
    """Spatial and temporal extents that describe the bounds of all items contained
    within this Collection."""

    id: str
    """Identifier for the collection."""

    stac_extensions: List[str]
    """List of extensions the Collection implements."""

    title: Optional[str]
    """Optional short descriptive one-line title for the collection."""

    keywords: Optional[List[str]]
    """Optional list of keywords describing the collection."""

    providers: Optional[List[Provider]]
    """Optional list of providers of this Collection."""

    summaries: Summaries
    """A map of property summaries, either a set of values or statistics such as a
    range."""

    links: List[Link]
    """A list of :class:`~pystac.Link` objects representing all links associated with
    this Collection."""

    extra_fields: Dict[str, Any]
    """Extra fields that are part of the top-level JSON properties of the Collection."""

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
        providers: Optional[List["Provider_Type"]] = None,
        summaries: Optional[Summaries] = None,
        assets: Optional[Dict[str, Asset]] = None,
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

        self.assets = {}
        if assets is not None:
            for k, asset in assets.items():
                self.add_asset(k, asset)

    def __repr__(self) -> str:
        return "<Collection id={}>".format(self.id)

    def _repr_html_(self) -> str:
        jinja_env = get_jinja_env()
        if jinja_env:
            template = jinja_env.get_template("Collection.jinja2")
            return str(template.render(catalog=self))
        else:
            return escape(repr(self))

    def add_item(
        self,
        item: "Item_Type",
        title: Optional[str] = None,
        strategy: Optional[HrefLayoutStrategy] = None,
    ) -> None:
        super().add_item(item, title, strategy)
        item.set_collection(self)

    def to_dict(
        self, include_self_link: bool = True, transform_hrefs: bool = True
    ) -> Dict[str, Any]:
        d = super().to_dict(
            include_self_link=include_self_link, transform_hrefs=transform_hrefs
        )
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
        cls = self.__class__
        clone = cls(
            id=self.id,
            description=self.description,
            extent=self.extent.clone(),
            title=self.title,
            stac_extensions=self.stac_extensions.copy(),
            extra_fields=deepcopy(self.extra_fields),
            catalog_type=self.catalog_type,
            license=self.license,
            keywords=self.keywords.copy() if self.keywords is not None else None,
            providers=deepcopy(self.providers),
            summaries=self.summaries.clone(),
            assets={k: asset.clone() for k, asset in self.assets.items()},
        )

        clone._resolved_objects.cache(clone)

        for link in self.links:
            if link.rel == pystac.RelType.ROOT:
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
        preserve_dict: bool = True,
    ) -> "Collection":
        if migrate:
            info = identify_stac_object(d)
            d = migrate_to_latest(d, info)

        if not cls.matches_object_type(d):
            raise STACTypeError(f"{d} does not represent a {cls.__name__} instance")

        catalog_type = CatalogType.determine_type(d)

        if preserve_dict:
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
            providers = list(map(lambda x: pystac.Provider.from_dict(x), providers))
        summaries = d.get("summaries")
        if summaries is not None:
            summaries = Summaries(summaries)

        assets: Optional[Dict[str, Any]] = {
            k: Asset.from_dict(v) for k, v in d.get("assets", {}).items()
        }
        links = d.pop("links")

        d.pop("stac_version")

        collection = cls(
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
            assets=assets,
        )

        for link in links:
            if link["rel"] == pystac.RelType.ROOT:
                # Remove the link that's generated in Catalog's constructor.
                collection.remove_links(pystac.RelType.ROOT)

            if link["rel"] != pystac.RelType.SELF or href is None:
                collection.add_link(Link.from_dict(link))

        if root:
            collection.set_root(root)

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
            key : The unique key of this asset.
            asset : The Asset to add.
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

    @classmethod
    def matches_object_type(cls, d: Dict[str, Any]) -> bool:
        return identify_stac_object_type(d) == STACObjectType.COLLECTION
