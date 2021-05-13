import os
import json
import numbers
import urllib.request

from pystac.utils import get_required

from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    Union,
    cast,
    TypeVar,
    Iterable,
    Protocol,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from pystac.item import Item as Item_Type
    from pystac.collection import Collection as Collection_Type

from abc import abstractmethod


class Comparable(Protocol):
    """Protocol for annotating comparable types."""

    @abstractmethod
    def __lt__(self: "T", other: "T") -> bool:
        pass

T = TypeVar("T", bound=Comparable)


class RangeSummary(Generic[T]):
    def __init__(self, minimum: T, maximum: T):
        self.minimum = minimum
        self.maximum = maximum

    def to_dict(self) -> Dict[str, Any]:
        return {"minimum": self.minimum, "maximum": self.maximum}

    def update_with_value(self, v: T) -> None:
        self.minimum = min(self.minimum, v)
        self.maximum = max(self.maximum, v)

    @classmethod
    def from_dict(cls, d: Dict[str, Any], typ: Type[T] = Any) -> "RangeSummary[T]":
        minimum: Optional[T] = get_required(d.get("minimum"), "RangeSummary", "minimum")
        maximum: Optional[T] = get_required(d.get("maximum"), "RangeSummary", "maximum")
        return cls(minimum=minimum, maximum=maximum)


FIELDS_JSON_URL = "https://cdn.jsdelivr.net/npm/@radiantearth/stac-fields/fields.json"

FIELDS_JSON_LOCAL_PATH = os.path.join(os.path.dirname(__file__), "resources",
                                      "fields-normalized.json")


class Summarizer():
    '''The Summarizer computes summaries from values, following the definition of fields
    to summarize provided in a json file.

    For more information about the structure of the fields json file, see:

    https://github.com/stac-utils/stac-fields

    Args:
        fields(str): the path to the json file with field descriptions.
        If no file is passed, a default one will be used.
    '''

    __default_field_definitions: dict = {}

    def __init__(self, fields: Optional[str] = None):
        if fields is None:
            self._set_default_field_definitions()
        else:
            with open(fields) as f:
                jsonfields = json.load(f)
            try:
                self._set_field_definitions(jsonfields)
            except:
                self._set_default_field_definitions()

    def _set_default_field_definitions(self) ->None:
        if not Summarizer.__default_field_definitions:
            try:
                with urllib.request.urlopen(FIELDS_JSON_URL) as url:
                    type(self).__default_field_definitions = json.loads(url.read().decode())
            except:
                pass
        if not Summarizer.__default_field_definitions:
            with open(FIELDS_JSON_LOCAL_PATH) as f:
                type(self).__default_field_definitions = json.load(f)
        self._set_field_definitions(Summarizer.__default_field_definitions)

    def _set_field_definitions(self, fields: dict) -> None:
        self.summaryfields = {}
        for name, desc in fields["metadata"].items():
            if isinstance(desc, dict):
                if desc.get("summary", True):
                    self.summaryfields[name] = {"mergeArrays": desc.get("mergeArrays", False)}
            else:
                self.summaryfields[name] = {"mergeArrays": False}

    def _update_with_item(self, summaries: "Summaries", item: "Item_Type") -> None:
        for k, v in item.properties.items():
            if k in self.summaryfields:
                if isinstance(v, numbers.Number) and not isinstance(v, bool):
                    rangesummary: Optional[RangeSummary] = summaries.get_range(k, object)
                    if rangesummary is None:
                        summaries.add(k, RangeSummary(v, v))
                    else:
                        rangesummary.update_with_value(v)
                elif isinstance(v, list):
                    listsummary: Optional[list] = summaries.get_list(k, object)
                    if listsummary is None:
                        listsummary = []
                    if self.summaryfields[k]["mergeArrays"]:
                        listsummary = list(set(listsummary) | set(v))
                    else:
                        if v not in listsummary:
                            listsummary.append(v)
                    summaries.add(k, listsummary)
                else:
                    listsummary = summaries.get_list(k, object) or []
                    if v not in listsummary:
                        listsummary.append(v)
                    summaries.add(k, listsummary)

    def summarize(self, source: Union["Collection_Type", Iterable["Item_Type"]]) -> "Summaries":
        """Creates summaries from items
        """
        summaries = Summaries.empty()
        if hasattr(source, "get_items"):
            for item in source.get_items():  # type: ignore[union-attr]
                self._update_with_item(summaries, item)
        else:
            for item in source:  # type: ignore[union-attr]
                self._update_with_item(summaries, item)

        return summaries


DEFAULT_MAXCOUNT = 25

class Summaries:
    def __init__(self, summaries: Dict[str, Any], maxcount: int = DEFAULT_MAXCOUNT) -> None:
        self._summaries = summaries
        self.maxcount = maxcount

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

