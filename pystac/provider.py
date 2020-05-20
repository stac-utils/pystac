class Provider:
    """Object with information about the provider of a STAC Asset

    Args:
        name (str): Name of the organization or individual
        description (str): Optional. Multi-line description with additional
            information about the providing organization such as hosting or
            contac information
        roles ([str]): Optional. Roles of the provider. Any of licensor,
            producer, processor or host
        url (str): Optional. Website with dataset description and/or provider
            contact info
    """
    def __init__(self, name, description=None, roles=None, url=None):
        self.name = name
        self.description = description
        self.roles = roles
        self.url = url

    @staticmethod
    def from_dict(d):
        return Provider(**d)

    def to_dict(self):
        d = {'name': self.name}
        if self.description is not None:
            d['description'] = self.description
        if self.roles is not None:
            d['roles'] = self.roles
        if self.url is not None:
            d['url'] = self.url

        return d
