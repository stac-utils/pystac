class STACError(Exception):
    """A STACError is raised for errors relating to STAC, e.g. for
    invalid formats or trying to operate on a STAC that does not have
    the required information available.
    """
    pass


class STACTypeError(Exception):
    """A STACTypeError is raised when encountering a representation of
    a STAC entity that is not correct for the context; for example, if
    a Catalog JSON was read in as an Item.
    """
    pass

class RequiredValueMissing(Exception):
    """ This error is raised when a required value was expected
    to be there but was missing or None. This will happen, for example,
    in an extension that has required properties, where the required
    property is missing from the extended object
    """
    pass