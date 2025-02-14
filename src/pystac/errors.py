class PySTACError(Exception):
    """A custom error class for this library."""


class STACError(PySTACError):
    """A subclass of [PySTACError][pystac.PySTACError] for errors related to the
    STAC specification itself."""


class PySTACWarning(Warning):
    """A custom warning class for this library."""


class STACWarning(PySTACWarning):
    """A warning about something incorrect per the STAC specification."""
