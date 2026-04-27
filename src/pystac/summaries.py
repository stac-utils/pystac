from __future__ import annotations

import copy
import datetime as dt
from collections.abc import Iterable, Iterator, MutableMapping
from enum import Enum
from functools import cache
from typing import TYPE_CHECKING, Any, TypedDict, override

from .reader import DEFAULT_READER

if TYPE_CHECKING:
    from .collection import Collection
    from .item import Item


class RangeSummaryDict[T: (int, float, dt.datetime)](TypedDict):
    minimum: T
    maximum: T


class RangeSummary[T: (int, float, dt.datetime)]:
    minimum: T
    maximum: T

    def __init__(self, minimum: T, maximum: T):
        self.minimum = minimum
        self.maximum = maximum

    def to_dict(self) -> RangeSummaryDict[T]:
        return {"minimum": self.minimum, "maximum": self.maximum}

    def update_with_value(self, v: T) -> None:
        self.minimum = min(self.minimum, v)
        self.maximum = max(self.maximum, v)

    @classmethod
    def from_dict(cls, d: RangeSummaryDict[T]) -> RangeSummary[T]:
        minimum: T = d["minimum"]
        maximum: T = d["maximum"]
        return cls(minimum=minimum, maximum=maximum)

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RangeSummary):
            return NotImplemented

        return self.to_dict() == other.to_dict()

    @override
    def __repr__(self) -> str:
        return self.to_dict().__repr__()


@cache
def _get_fields_json(url: str | None) -> dict[str, Any]:
    if url is None:
        import importlib.resources
        import json

        # Every time pystac is released this file gets pulled from
        # https://cdn.jsdelivr.net/npm/@radiantearth/stac-fields/fields-normalized.json
        jsonfields: dict[str, Any] = json.loads(
            importlib.resources.files("pystac.static")
            .joinpath("fields-normalized.json")
            .read_text()
        )
        return jsonfields
    return DEFAULT_READER.get_json(url)


class SummaryStrategy(Enum):
    ARRAY = "v"
    RANGE = "r"
    SCHEMA = "s"
    DONT_SUMMARIZE = False
    DEFAULT = True

    @classmethod
    def try_from(
        cls, strategy: SummaryStrategy | dict[str, Any] | None
    ) -> SummaryStrategy:
        if isinstance(strategy, SummaryStrategy):
            return strategy

        if isinstance(strategy, dict):
            strategy_value = strategy.get("summary", True)
            if strategy_value in cls:
                return SummaryStrategy(strategy_value)

        return SummaryStrategy.DEFAULT


class Summarizer:
    """The Summarizer computes summaries from values, following the definition of fields
    to summarize.

    The fields to summarize can be provided as a JSON file or as a dictionary of
    field names and SummaryStrategys. If nothing is provided, a default JSON file
    will be used.

    Only fields that are in the Item `properties` can be summarized.
    Thus, it is not possible to summarize the top-level fields such as `id` or `assets`.

    For more information about the structure of the fields JSON file, see:
    https://github.com/stac-utils/stac-fields

    The default JSON file used is a snapshot of the following file at the time of
    the pystac release:
    https://cdn.jsdelivr.net/npm/@radiantearth/stac-fields/fields-normalized.json

    Args:
        fields: A string containing the path to the JSON file with field descriptions.
            Alternatively, a dict with the field names as keys and SummaryStrategys
            as values.
            If nothing is passed, a default file with field descriptions will be used.
    """

    summaryfields: dict[str, SummaryStrategy]

    def __init__(
        self,
        fields: str | dict[str, SummaryStrategy | dict[str, Any] | None] | None = None,
    ):
        json_fields: dict[str, SummaryStrategy | dict[str, Any] | None]
        if isinstance(fields, dict):
            json_fields = fields
        else:
            json_fields = _get_fields_json(fields)["metadata"]

        self.summaryfields = {}
        for name, desc in json_fields.items():
            strategy = SummaryStrategy.try_from(desc)
            if strategy != SummaryStrategy.DONT_SUMMARIZE:
                self.summaryfields[name] = strategy

    def _update_with_item(self, summaries: Summaries, item: Item) -> None:
        for k, v in item.properties.items():
            if k in self.summaryfields:
                strategy = self.summaryfields[k]
                summary = summaries.get(k)
                if strategy in [
                    SummaryStrategy.RANGE,
                    SummaryStrategy.DEFAULT,
                ] and isinstance(v, (int, float, dt.datetime)):
                    if summary is None:
                        summaries[k] = RangeSummary(minimum=v, maximum=v)
                    else:
                        summaries[k] = summary.update_with_value(v)
                elif strategy in [
                    SummaryStrategy.ARRAY,
                    SummaryStrategy.DEFAULT,
                ] and isinstance(v, list):
                    if summary is None:
                        summaries[k] = v
                    else:
                        summaries[k] = [*set(summary).union(set(v))]
                else:
                    if summary is None:
                        summaries[k] = [v]
                    elif v not in summary:
                        summaries[k] = [*summary, v]

    def summarize(self, source: Collection | Iterable[Item]) -> Summaries:
        """Creates summaries from items"""
        from .collection import Collection

        summaries = Summaries.empty()
        if isinstance(source, Collection):
            for item in source.get_items(recursive=True):
                self._update_with_item(summaries, item)
        else:
            for item in source:
                self._update_with_item(summaries, item)

        return summaries


DEFAULT_MAXCOUNT = 25


class Summaries(MutableMapping[str, Any]):
    maxcount: int

    def __init__(
        self, summaries: dict[str, Any], maxcount: int = DEFAULT_MAXCOUNT
    ) -> None:
        self._store = summaries
        self.maxcount = maxcount

    @classmethod
    def try_from(cls, summaries: Summaries | dict[str, Any] | None) -> Summaries:
        if isinstance(summaries, Summaries):
            return summaries
        elif isinstance(summaries, dict):
            return Summaries(summaries)
        else:
            return Summaries({})

    @override
    def __getitem__(self, key: str) -> Any:
        return self._store[key]

    @override
    def __setitem__(self, name: str, value: Any, /) -> None:
        if isinstance(value, dict):
            RangeSummary.from_dict(value)
        self._store[name] = value

    @override
    def __delitem__(self, key: str) -> None:
        del self._store[key]

    @override
    def __iter__(self) -> Iterator[str]:
        return iter(self._store)

    @override
    def __len__(self) -> int:
        return len(self._store)

    def get_list(self, prop: str) -> list[Any] | None:
        value = self._store.get(prop)
        if value is not None:
            assert isinstance(value, list)
            return value

    def get_range(self, prop: str) -> RangeSummary[Any] | None:
        value = self._store.get(prop)
        if value is not None:
            assert isinstance(value, RangeSummary)
            return value

    def to_dict(self) -> dict[str, Any]:
        return {
            k: v if not isinstance(v, RangeSummary) else v.to_dict()
            for k, v in self._store.items()
            if not isinstance(v, list) or len(v) < self.maxcount
        }

    def is_empty(self) -> bool:
        return len(self) == 0

    @classmethod
    def empty(cls) -> Summaries:
        return Summaries({})

    def clone(self) -> Summaries:
        return copy.deepcopy(self)
