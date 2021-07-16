import unittest

from pystac import Provider


class ProviderTest(unittest.TestCase):
    def test_to_from_dict(self) -> None:
        provider_dict = {
            "name": "Remote Data, Inc",
            "description": "Producers of awesome spatiotemporal assets",
            "roles": ["producer", "processor"],
            "url": "http://remotedata.io",
            "extension:field": "some value",
        }
        expected_extra_fields = {"extension:field": provider_dict["extension:field"]}

        provider = Provider.from_dict(provider_dict)

        self.assertEqual(provider_dict["name"], provider.name)
        self.assertEqual(provider_dict["description"], provider.description)
        self.assertEqual(provider_dict["roles"], provider.roles)
        self.assertEqual(provider_dict["url"], provider.url)
        self.assertDictEqual(expected_extra_fields, provider.extra_fields)

        self.assertDictEqual(provider_dict, provider.to_dict())

