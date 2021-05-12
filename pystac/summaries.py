import os
import json
import numbers
import urllib.request

from pystac.utils import get_required

from typing import (Any, Dict, Generic, List, Optional, Type, Union, cast, TypeVar)

T = TypeVar("T")


class RangeSummary(Generic[T]):
    def __init__(self, minimum: T, maximum: T):
        self.minimum = minimum
        self.maximum = maximum

    def to_dict(self) -> Dict[str, Any]:
        return {"minimum": self.minimum, "maximum": self.maximum}

    def update_with_value(self, v: T):
        self.minimum = min(self.minimum, v)
        self.maximum = min(self.maximum, v)

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
    def __init__(self, fields: str = None):
        if fields is None:
            self._load_default_field_definitions()
        else:
            with open(fields) as f:
                jsonfields = json.load(f)
            try:
                self._set_field_definitions(jsonfields)
            except:
                self._load_default_field_definitions()

    def _load_default_field_definitions(self):
        try:
            with urllib.request.urlopen(FIELDS_JSON_URL) as url:
                jsonfields = json.loads(url.read().decode())
        except:
            with open(FIELDS_JSON_LOCAL_PATH) as f:
                jsonfields = json.load(f)
        self._set_field_definitions(jsonfields)

    def _set_field_definitions(self, fields):
        self.summaryfields = {}
        for name, desc in fields["metadata"].items():
            if isinstance(desc, dict):
                if desc.get("summary", True):
                    self.summaryfields[name] = {"mergeArrays": desc.get("mergeArrays", False)}
            else:
                self.summaryfields[name] = {"mergeArrays": False}

    def update_with_item(self, summaries, item):
        for k, v in item.properties.items():
            if k in self.summaryfields:
                if isinstance(v, numbers.Number) and not isinstance(v, bool):
                    rangesummary = summaries.get_range(k, float)
                    if rangesummary is None:
                        summaries.add(k, RangeSummary(v, v))
                    else:
                        rangesummary.update_with_value(v)
                elif isinstance(v, list):
                    listsummary = summaries.get_list(k, Any)
                    if listsummary is None:
                        listsummary = []
                    if self.summaryfields[k]["mergeArrays"]:
                        listsummary = list(set(listsummary) | set(v))
                    else:
                        if v not in listsummary:
                            listsummary.append(v)
                    summaries.add(k, listsummary)
                else:
                    listsummary = summaries.get_list(k, Any) or []
                    if v not in listsummary:
                        listsummary.append(v)
                    summaries.add(k, listsummary)


class Summaries:
    def __init__(self, summaries: Dict[str, Any], summarizer: Summarizer = None) -> None:
        self._summaries = summaries

        self.summarizer = summarizer or Summarizer()
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
    def empty(cls, summarizer: Summarizer = None) -> "Summaries":
        return Summaries({}, summarizer)

    def update_with_item(self, item):
        self.summarizer.update_with_item(self, item)
