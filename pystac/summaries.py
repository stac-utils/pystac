from copy import deepcopy
import numbers
from enum import Enum
from functools import lru_cache

import pystac
from pystac.utils import get_required

from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Union,
    TypeVar,
    Iterable,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from pystac.item import Item as Item_Type
    from pystac.collection import Collection as Collection_Type

from abc import abstractmethod


class _Comparable_x(Protocol):
    """Protocol for annotating comparable types.

    For matching __lt__ that takes an 'x' parameter
    (e.g. float)
    """

    @abstractmethod
    def __lt__(self: "T", x: "T") -> bool:
        return NotImplemented


class _Comparable_other(Protocol):
    """Protocol for annotating comparable types.

    For matching __lt___ that takes an 'other' parameter
    (e.g. datetime)
    """

    @abstractmethod
    def __lt__(self: "T", other: "T") -> bool:
        return NotImplemented


T = TypeVar("T", bound=Union[_Comparable_x, _Comparable_other])


class RangeSummary(Generic[T]):
    minimum: T
    maximum: T

    def __init__(self, minimum: T, maximum: T):
        self.minimum = minimum
        self.maximum = maximum

    def to_dict(self) -> Dict[str, Any]:
        return {"minimum": self.minimum, "maximum": self.maximum}

    def update_with_value(self, v: T) -> None:
        self.minimum = min(self.minimum, v)
        self.maximum = max(self.maximum, v)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RangeSummary[T]":
        minimum: T = get_required(d.get("minimum"), "RangeSummary", "minimum")
        maximum: T = get_required(d.get("maximum"), "RangeSummary", "maximum")
        return cls(minimum=minimum, maximum=maximum)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, RangeSummary):
            return NotImplemented

        return self.to_dict() == o.to_dict()

    def __repr__(self) -> str:
        return self.to_dict().__repr__()


FIELDS_JSON_URL = (
    "https://cdn.jsdelivr.net/npm/@radiantearth/stac-fields/fields-normalized.json"
)


@lru_cache(maxsize=None)
def _get_fields_json(url: str) -> Dict[str, Any]:
    return pystac.StacIO.default().read_json(url)


class SummaryStrategy(Enum):
    ARRAY = "v"
    RANGE = "r"
    SCHEMA = "s"
    DONT_SUMMARIZE = False
    DEFAULT = True


class Summarizer:
    """The Summarizer computes summaries from values, following the definition of fields
    to summarize provided in a json file.

    For more information about the structure of the fields json file, see:

    https://github.com/stac-utils/stac-fields

    Args:
        fields (str): the path to the json file with field descriptions.
        If no file is passed, a default one will be used.
    """

    summaryfields: Dict[str, SummaryStrategy]

    def __init__(self, fields: Optional[str] = None):
        fieldspath = fields or FIELDS_JSON_URL
        try:
            jsonfields = _get_fields_json(fieldspath)
        except:
            if fields is None:
                raise Exception(
                    "Could not read fields definition file at "
                    f"{fields} or it is invalid.\n"
                    "Try using a local fields definition file."
                )
            else:
                raise
        self._set_field_definitions(jsonfields)

    def _set_field_definitions(self, fields: Dict[str, Any]) -> None:
        self.summaryfields = {}
        for name, desc in fields["metadata"].items():
            if isinstance(desc, dict):
                strategy_value = desc.get("summary", True)
                try:
                    strategy: SummaryStrategy = SummaryStrategy(strategy_value)
                except ValueError:
                    strategy = SummaryStrategy.DEFAULT
                if strategy != SummaryStrategy.DONT_SUMMARIZE:
                    self.summaryfields[name] = strategy
            else:
                self.summaryfields[name] = SummaryStrategy.DEFAULT

    def _update_with_item(self, summaries: "Summaries", item: "Item_Type") -> None:
        for k, v in item.properties.items():
            if k in self.summaryfields:
                strategy = self.summaryfields[k]
                if strategy == SummaryStrategy.RANGE or (
                    strategy == SummaryStrategy.DEFAULT
                    and isinstance(v, numbers.Number)
                    and not isinstance(v, bool)
                ):
                    rangesummary: Optional[RangeSummary[Any]] = summaries.get_range(k)
                    if rangesummary is None:
                        summaries.add(k, RangeSummary(v, v))
                    else:
                        rangesummary.update_with_value(v)
                elif strategy == SummaryStrategy.ARRAY or (
                    strategy == SummaryStrategy.DEFAULT and isinstance(v, list)
                ):
                    listsummary: List[Any] = summaries.get_list(k) or []
                    if not isinstance(v, list):
                        v = [v]
                    for element in v:
                        if element not in listsummary:
                            listsummary.append(element)
                    summaries.add(k, listsummary)
                else:
                    summary: List[Any] = summaries.get_list(k) or []
                    if v not in summary:
                        summary.append(v)
                    summaries.add(k, summary)

    def summarize(
        self, source: Union["Collection_Type", Iterable["Item_Type"]]
    ) -> "Summaries":
        """Creates summaries from items"""
        summaries = Summaries.empty()
        if isinstance(source, pystac.Collection):
            for item in source.get_all_items():
                self._update_with_item(summaries, item)
        else:
            for item in source:
                self._update_with_item(summaries, item)

        return summaries


DEFAULT_MAXCOUNT = 25


class Summaries:
    _summaries: Dict[str, Any]

    lists: Dict[str, List[Any]]
    other: Dict[str, Any]
    ranges: Dict[str, RangeSummary[Any]]
    schemas: Dict[str, Dict[str, Any]]
    maxcount: int

    def __init__(
        self, summaries: Dict[str, Any], maxcount: int = DEFAULT_MAXCOUNT
    ) -> None:
        self._summaries = summaries
        self.maxcount = maxcount

        self.lists = {}
        self.ranges = {}
        self.schemas = {}
        self.other = {}

        for prop_key, summary in summaries.items():
            self.add(prop_key, summary)

    def get_list(self, prop: str) -> Optional[List[Any]]:
        return self.lists.get(prop)

    def get_range(self, prop: str) -> Optional[RangeSummary[Any]]:
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
                self.ranges[prop_key] = RangeSummary[Any].from_dict(summary)
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

    def update(self, summaries: "Summaries") -> None:
        self.lists.update(summaries.lists)
        self.ranges.update(summaries.ranges)
        self.schemas.update(summaries.schemas)
        self.other.update(summaries.other)

    def combine(self, summaries: "Summaries") -> None:
        for listname, listvalue in summaries.lists.items():
            if listname in self.lists:
                self.lists[listname].extend(listvalue)
            else:
                self.lists[listname] = listvalue
        for rangename, rang in summaries.ranges.items():
            if rangename in self.ranges:
                self.ranges[rangename].update_with_value(rang.minimum)
                self.ranges[rangename].update_with_value(rang.maximum)
            else:
                self.ranges[rangename] = rang
        for schemaname, schema in summaries.schemas.items():
            if schemaname in self.schemas:
                self.schemas[schemaname].update(schema)
            else:
                self.schemas[schemaname] = schema
        for k, v in summaries.other.items():
            if k in self.other:
                self.other[k].update(v)
            else:
                self.other[k] = v

    def is_empty(self) -> bool:
        return not (
            any(self.lists) or any(self.ranges) or any(self.schemas) or any(self.other)
        )

    def clone(self) -> "Summaries":
        """Clones this object.

        Returns:
            Summaries: The clone of this object
        """
        summaries = Summaries(
            summaries=deepcopy(self._summaries), maxcount=self.maxcount
        )
        summaries.lists = deepcopy(self.lists)
        summaries.other = deepcopy(self.other)
        summaries.ranges = deepcopy(self.ranges)
        summaries.schemas = deepcopy(self.schemas)
        return summaries

    def to_dict(self) -> Dict[str, Any]:
        return {
            **{k: v for k, v in self.lists.items() if len(v) < self.maxcount},
            **{k: v.to_dict() for k, v in self.ranges.items()},
            **self.schemas,
            **self.other,
        }

    @classmethod
    def empty(cls) -> "Summaries":
        return Summaries({})
