from copy import deepcopy
from pystac.errors import STACTypeError
from typing import Any, Dict, Iterator, List, Optional, Sized, Iterable

import pystac
from pystac.utils import make_absolute_href, is_absolute_href
from pystac.serialization.identify import identify_stac_object_type


class ItemCollection(Sized, Iterable[pystac.Item]):
    """Implementation of a GeoJSON FeatureCollection whose features are all STAC
    Items.

    All :class:`~pystac.Item` instances passed to the :class:`~ItemCollection` instance
    during instantation are cloned and have their ``"root"`` URL cleared. Instances of
    this class are iterable and sized (see examples below).
    
    Any additional top-level fields in the FeatureCollection are retained in
    :attr:`~ItemCollection.extra_fields` by the :meth:`~ItemCollection.from_dict` and
    :meth:`~ItemCollection.from_file` methods and will be present in the serialized file
    from :meth:`~ItemCollection.save_object`.

    Examples:

        Loop over all items in the ItemCollection

        >>> item_collection: ItemCollection = ...
        >>> for item in item_collection:
        ...     ...

        Get the number of Items in the ItemCollection

        >>> length: int = len(item_collection)

    """

    items: List[pystac.Item]
    """The list of :class:`pystac.Item` instances contained in this
    ``ItemCollection``."""

    extra_fields: Dict[str, Any]
    """Dictionary containing additional top-level fields for the GeoJSON
    FeatureCollection."""

    def __init__(
        self, items: List[pystac.Item], extra_fields: Optional[Dict[str, Any]] = None
    ):
        self.items = [item.clone() for item in items]
        for item in self.items:
            item.clear_links("root")
        self.extra_fields = extra_fields or {}

    def __getitem__(self, idx: int) -> pystac.Item:
        return self.items[idx]

    def __iter__(self) -> Iterator[pystac.Item]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes an :class:`ItemCollection` instance to a JSON-like dictionary."""
        return {
            "type": "FeatureCollection",
            "features": [item.to_dict() for item in self.items],
            **self.extra_fields,
        }

    def clone(self) -> "ItemCollection":
        """Creates a clone of this instance. This clone is a deep copy; all
        :class:`~pystac.Item` instances are cloned and all additional top-level fields
        are deep copied."""
        return self.__class__(
            items=[item.clone() for item in self.items],
            extra_fields=deepcopy(self.extra_fields),
        )

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ItemCollection":
        """Creates a :class:`ItemCollection` instance from a dictionary."""
        if identify_stac_object_type(d) != pystac.STACObjectType.ITEMCOLLECTION:
            raise STACTypeError("Dict is not a valid ItemCollection")

        items = [pystac.Item.from_dict(item) for item in d.get("features", [])]
        extra_fields = {k: v for k, v in d.items() if k not in ("features", "type")}

        return cls(items=items, extra_fields=extra_fields)

    @classmethod
    def from_file(
        cls, href: str, stac_io: Optional[pystac.StacIO] = None
    ) -> "ItemCollection":
        """Reads a :class:`ItemCollection` from a JSON file.

        Arguments:
            href : Path to the file.
            stac_io : A :class:`~pystac.StacIO` instance to use for file I/O
        """
        if stac_io is None:
            stac_io = pystac.StacIO.default()

        if not is_absolute_href(href):
            href = make_absolute_href(href)

        d = stac_io.read_json(href)

        return cls.from_dict(d)

    def save_object(
        self,
        dest_href: str,
        stac_io: Optional[pystac.StacIO] = None,
    ) -> None:
        """Saves this instance to the ``dest_href`` location.

        Args:
            dest_href : Location to which the file will be saved.
            stac_io: Optional :class:`~pystac.StacIO` instance to use. If not provided,
                will use the default instance.
        """
        if stac_io is None:
            stac_io = pystac.StacIO.default()

        stac_io.save_json(dest_href, self.to_dict())
