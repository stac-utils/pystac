import pystac
from pystac.validation.schema_uri_map import DefaultSchemaUriMap


def test_gets_schema_uri_for_old_version() -> None:
    d = DefaultSchemaUriMap()
    uri = d.get_object_schema_uri(pystac.STACObjectType.ITEM, "0.8.0")

    assert uri == (
        "https://raw.githubusercontent.com/radiantearth/stac-spec/v0.8.0/"
        "item-spec/json-schema/item.json"
    )
