from typing import Any, Dict, List, Optional
from html import escape

from pystac.html.jinja_env import get_jinja_env
from pystac.utils import StringEnum


class ProviderRole(StringEnum):
    """Enumerates the allows values of the Provider "role" field."""

    LICENSOR = "licensor"
    PRODUCER = "producer"
    PROCESSOR = "processor"
    HOST = "host"


class Provider:
    """Provides information about a provider of STAC data. A provider is any of the
    organizations that captured or processed the content of the collection and therefore
    influenced the data offered by this collection. May also include information about
    the final storage provider hosting the data.

    Args:
        name : The name of the organization or the individual.
        description : Optional multi-line description to add further provider
            information such as processing details for processors and producers,
            hosting details for hosts or basic contact information.
        roles : Optional roles of the provider. Any of
            licensor, producer, processor or host.
        url : Optional homepage on which the provider describes the dataset
            and publishes contact information.
        extra_fields : Optional dictionary containing additional top-level fields
            defined on the Provider object.
    """

    name: str
    """The name of the organization or the individual."""

    description: Optional[str]
    """Optional multi-line description to add further provider
    information such as processing details for processors and producers,
    hosting details for hosts or basic contact information."""

    roles: Optional[List[ProviderRole]]
    """Optional roles of the provider. Any of
    licensor, producer, processor or host."""

    url: Optional[str]
    """Optional homepage on which the provider describes the dataset
    and publishes contact information."""

    extra_fields: Dict[str, Any]
    """Dictionary containing additional top-level fields defined on the Provider
    object."""

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        roles: Optional[List[ProviderRole]] = None,
        url: Optional[str] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.roles = roles
        self.url = url
        self.extra_fields = extra_fields or {}

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Provider):
            return NotImplemented
        return self.to_dict() == o.to_dict()

    def _repr_html_(self) -> str:
        jinja_env = get_jinja_env()
        if jinja_env:
            template = jinja_env.get_template("Provider.jinja2")
            return str(template.render(provider=self))
        else:
            return escape(repr(self))

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

        d.update(self.extra_fields)

        return d

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Provider":
        """Constructs an Provider from a dict.

        Returns:
            Provider: The Provider deserialized from the JSON dict.
        """
        return Provider(
            name=d["name"],
            description=d.get("description"),
            roles=d.get(
                "roles",
            ),
            url=d.get("url"),
            extra_fields={
                k: v
                for k, v in d.items()
                if k not in {"name", "description", "roles", "url"}
            },
        )
