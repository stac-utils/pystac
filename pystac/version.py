import os

__version__ = "1.13.0"
"""Library version"""


class STACVersion:
    DEFAULT_STAC_VERSION = "1.1.0"
    """Latest STAC version supported by PySTAC"""

    DEFAULT_STAC_API_VERSION = "1.0.0"
    """Latest STAC API version supported by PySTAC"""

    # Version that holds a user-set STAC version to use.
    _override_version: str | None = None

    OVERRIDE_VERSION_ENV_VAR = "PYSTAC_STAC_VERSION_OVERRIDE"

    @classmethod
    def get_stac_version(cls) -> str:
        if cls._override_version is not None:
            return cls._override_version

        env_version = os.environ.get(cls.OVERRIDE_VERSION_ENV_VAR)
        if env_version is not None:
            return env_version

        return cls.DEFAULT_STAC_VERSION

    @classmethod
    def set_stac_version(cls, stac_version: str | None) -> None:
        cls._override_version = stac_version


def get_stac_version() -> str:
    """Returns the STAC version PySTAC writes as the "stac_version" property for
    any object it serializes into JSON.

    If a call to ``set_stac_version`` was made, this will return the value it was
    called with. Next it will check the environment for a PYSTAC_STAC_VERSION_OVERRIDE
    variable. Otherwise it will return the latest STAC version that this version of
    PySTAC supports.

    Returns:
        str: The STAC Version PySTAC is set up to use.
    """
    return STACVersion.get_stac_version()


def set_stac_version(stac_version: str | None) -> None:
    """Sets the STAC version that PySTAC should use.

    This is the version that will be set as the "stac_version" property
    on any JSON STAC objects written by PySTAC. If set to None, the override version
    will be cleared if previously set and the default or an override taken from the
    environment will be used.

    You can also set the environment variable PYSTAC_STAC_VERSION_OVERRIDE to override
    the version.

    Args:
        stac_version : The STAC version to use instead of the latest STAC version
            that PySTAC supports (described in STACVersion.DEFAULT_STAC_VERSION).
            If None, clear to use the default for this version of PySTAC.

    Note:
        Setting the STAC version to something besides the default version will not
        effect the format of STAC read or written; it will only override the
        ``stac_version`` property of the objects being written. Setting this
        incorrectly can produce invalid STAC.
    """
    STACVersion.set_stac_version(stac_version)
