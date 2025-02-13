class PystacError(Exception):
    """A custom error class for this library."""


class StacError(PystacError):
    """A subclass of [PystacError][pystac.PystacError] for errors related to the
    STAC specification itself."""


class PystacWarning(Warning):
    """A custom warning class for this library."""


class StacWarning(PystacWarning):
    """A warning about something incorrect per the STAC specification."""
