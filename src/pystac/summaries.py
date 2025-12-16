from __future__ import annotations

import importlib.resources
import json
import numbers
from abc import abstractmethod
from collections.abc import Iterable
from copy import deepcopy
from enum import Enum
from functools import lru_cache
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Protocol,
    TypeVar,
)

import pystac
from pystac.utils import get_required

if TYPE_CHECKING:
    from pystac.collection import Collection
    from pystac.item import Item


def __getattr__(name: str) -> Any:
    if name == "FIELDS_JSON_URL":
        import warnings

        warnings.warn(
            "FIELDS_JSON_URL is deprecated and will be removed in v2",
            DeprecationWarning,
        )
        return (
            "https://cdn.jsdelivr.net/npm/@radiantearth/"
            "stac-fields/fields-normalized.json"
        )
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class _Comparable_x(Protocol):
    """Protocol for annotating comparable types.

    For matching __lt__ that takes an 'x' parameter
    (e.g. float)
    """

    @abstractmethod
    def __lt__(self: T, x: T) -> bool:
        return NotImplemented


class _Comparable_other(Protocol):
    """Protocol for annotating comparable types.

    For matching __lt___ that takes an 'other' parameter
    (e.g. datetime)
    """

    @abstractmethod
    def __lt__(self: T, other: T) -> bool:
        return NotImplemented


T = TypeVar("T", bound=_Comparable_x | _Comparable_other)


class RangeSummary(Generic[T]):
    minimum: T
    maximum: T

    def __init__(self, minimum: T, maximum: T):
        self.minimum = minimum
        self.maximum = maximum

    def to_dict(self) -> dict[str, Any]:
        return {"minimum": self.minimum, "maximum": self.maximum}

    def update_with_value(self, v: T) -> None:
        self.minimum = min(self.minimum, v)
        self.maximum = max(self.maximum, v)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RangeSummary[T]:
        minimum: T = get_required(d.get("minimum"), "RangeSummary", "minimum")
        maximum: T = get_required(d.get("maximum"), "RangeSummary", "maximum")
        return cls(minimum=minimum, maximum=maximum)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, RangeSummary):
            return NotImplemented

        return self.to_dict() == o.to_dict()

    def __repr__(self) -> str:
        return self.to_dict().__repr__()


@lru_cache(maxsize=None)
def _get_fields_json(url: str | None) -> dict[str, Any]:
    if url is None:
        # Every time pystac is released this file gets pulled from
        # https://cdn.jsdelivr.net/npm/@radiantearth/stac-fields/fields-normalized.json
        jsonfields: dict[str, Any] = json.loads(
            importlib.resources.files("pystac.static")
            .joinpath("fields-normalized.json")
            .read_text()
        )
        return jsonfields
    return pystac.StacIO.default().read_json(url)


class SummaryStrategy(Enum):
    ARRAY = "v"
    RANGE = "r"
    SCHEMA = "s"
    DONT_SUMMARIZE = False
    DEFAULT = True


class Summarizer:
    """The Summarizer computes summaries from values, following the definition of fields
    to summarize.

    The fields to summarize can be provided as a JSON file or as a dictionary of
    field names and SummaryStrategys. If nothing is provided, a default JSON file
    will be used.

    Only fields that are in the Item `properties` can be summarized.
    Thus it is not possible to summarize the top-level fields such as `id` or `assets`.

    For more information about the structure of the fields JSON file, see:
    https://github.com/stac-utils/stac-fields

    The default JSON file used is a snapshot of the following file at the time of
    the pystac release:
    https://cdn.jsdelivr.net/npm/@radiantearth/stac-fields/fields-normalized.json

    Args:
        fields: A string containing the path to the json file with field descriptions.
            Alternatively, a dict with the field names as keys and SummaryStrategys
            as values.
            If nothing is passed, a default file with field descriptions will be used.
    """

    summaryfields: dict[str, SummaryStrategy]

    def __init__(self, fields: str | dict[str, SummaryStrategy] | None = None):
        if isinstance(fields, dict):
            self._set_field_definitions(fields)
        else:
            jsonfields = _get_fields_json(fields)
            self._set_field_definitions(jsonfields["metadata"])

    def _set_field_definitions(self, fields: dict[str, Any]) -> None:
        self.summaryfields = {}
        for name, desc in fields.items():
            strategy: SummaryStrategy = SummaryStrategy.DEFAULT
            if isinstance(desc, SummaryStrategy):
                strategy = desc
            elif isinstance(desc, dict):
                strategy_value = desc.get("summary", True)
                try:
                    strategy = SummaryStrategy(strategy_value)
                except ValueError:
                    pass

            if strategy != SummaryStrategy.DONT_SUMMARIZE:
                self.summaryfields[name] = strategy

    def _update_with_item(self, summaries: Summaries, item: Item) -> None:
        for k, v in item.properties.items():
            if k in self.summaryfields:
                strategy = self.summaryfields[k]
                if strategy == SummaryStrategy.RANGE or (
                    strategy == SummaryStrategy.DEFAULT
                    and isinstance(v, numbers.Number)
                    and not isinstance(v, bool)
                ):
                    rangesummary: RangeSummary[Any] | None = summaries.get_range(k)
                    if rangesummary is None:
                        summaries.add(k, RangeSummary(v, v))
                    else:
                        rangesummary.update_with_value(v)
                elif strategy == SummaryStrategy.ARRAY or (
                    strategy == SummaryStrategy.DEFAULT and isinstance(v, list)
                ):
                    listsummary: list[Any] = summaries.get_list(k) or []
                    if not isinstance(v, list):
                        v = [v]
                    for element in v:
                        if element not in listsummary:
                            listsummary.append(element)
                    summaries.add(k, listsummary)
                else:
                    summary: list[Any] = summaries.get_list(k) or []
                    if v not in summary:
                        summary.append(v)
                    summaries.add(k, summary)

    def summarize(self, source: Collection | Iterable[Item]) -> Summaries:
        """Creates summaries from items"""
        summaries = Summaries.empty()
        if isinstance(source, pystac.Collection):
            for item in source.get_items(recursive=True):
                self._update_with_item(summaries, item)
        else:
            for item in source:
                self._update_with_item(summaries, item)

        return summaries


DEFAULT_MAXCOUNT = 25


class Summaries:
    _summaries: dict[str, Any]

    lists: dict[str, list[Any]]
    other: dict[str, Any]
    ranges: dict[str, RangeSummary[Any]]
    schemas: dict[str, dict[str, Any]]
    maxcount: int

    def __init__(
        self, summaries: dict[str, Any], maxcount: int = DEFAULT_MAXCOUNT
    ) -> None:
        self._summaries = summaries
        self.maxcount = maxcount

        self.lists = {}
        self.ranges = {}
        self.schemas = {}
        self.other = {}

        for prop_key, summary in summaries.items():
            self.add(prop_key, summary)

    def get_list(self, prop: str) -> list[Any] | None:
        return self.lists.get(prop)

    def get_range(self, prop: str) -> RangeSummary[Any] | None:
        return self.ranges.get(prop)

    def get_schema(self, prop: str) -> dict[str, Any] | None:
        return self.schemas.get(prop)

    def add(
        self,
        prop_key: str,
        summary: list[Any] | RangeSummary[Any] | dict[str, Any],
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

    def update(self, summaries: Summaries) -> None:
        self.lists.update(summaries.lists)
        self.ranges.update(summaries.ranges)
        self.schemas.update(summaries.schemas)
        self.other.update(summaries.other)

    def combine(self, summaries: Summaries) -> None:
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

    def clone(self) -> Summaries:
        """Clones this object.

        Returns:
            Summaries: The clone of this object
        """
        cls = self.__class__
        summaries = cls(summaries=deepcopy(self._summaries), maxcount=self.maxcount)
        summaries.lists = deepcopy(self.lists)
        summaries.other = deepcopy(self.other)
        summaries.ranges = deepcopy(self.ranges)
        summaries.schemas = deepcopy(self.schemas)
        return summaries

    def to_dict(self) -> dict[str, Any]:
        return {
            **{k: v for k, v in self.lists.items() if len(v) < self.maxcount},
            **{k: v.to_dict() for k, v in self.ranges.items()},
            **self.schemas,
            **self.other,
        }

    @classmethod
    def empty(cls) -> Summaries:
        return Summaries({})
