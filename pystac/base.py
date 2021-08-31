from copy import deepcopy
from typing import Any, Dict, TypeVar


V = TypeVar("V")


class JSONObject:
    """A base class for objects that can be represented as JSON objects.

    Instances of ``JSONObject`` have a :attr:`JSONObject.fields` attribute that is a
    dictionary representation of the JSON object. Any property getters/setters on
    inheriting classes MUST be sure to keep this dictionary up-to-date.
    """

    fields: Dict[str, Any] = {}

    def to_dict(self, preserve_dict: bool = True) -> Dict[str, Any]:
        if preserve_dict:
            return deepcopy(self.fields)
        else:
            return self.fields

    def _set_field(self, name: str, v: Any, *, pop_if_none: bool = False) -> None:
        if v is None and pop_if_none:
            self.fields.pop(name, None)
        else:
            self.fields[name] = v
