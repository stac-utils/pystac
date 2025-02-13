from __future__ import annotations

import datetime
import warnings
from typing import Any, Sequence

from typing_extensions import Self

from .constants import DEFAULT_BBOX, DEFAULT_INTERVAL
from .errors import StacWarning
from .types import PermissiveBbox, PermissiveInterval


class Extent:
    """A spatial and temporal extent."""

    @classmethod
    def from_dict(cls: type[Self], d: dict[str, Any]) -> Self:
        """Creates an extent from a dictionary."""
        return cls(**d)

    def __init__(
        self,
        spatial: SpatialExtent | dict[str, Any] | None = None,
        temporal: TemporalExtent | dict[str, Any] | None = None,
    ):
        """Creates a new extent."""
        if spatial is None:
            self.spatial = SpatialExtent()
        elif isinstance(spatial, SpatialExtent):
            self.spatial = spatial
        else:
            self.spatial = SpatialExtent.from_dict(spatial)
        if temporal is None:
            self.temporal = TemporalExtent()
        elif isinstance(temporal, TemporalExtent):
            self.temporal = temporal
        else:
            self.temporal = TemporalExtent.from_dict(temporal)

    def to_dict(self) -> dict[str, Any]:
        """Converts this extent to a dictionary."""
        return {
            "spatial": self.spatial.to_dict(),
            "temporal": self.temporal.to_dict(),
        }


class SpatialExtent:
    """A spatial extent."""

    @classmethod
    def from_dict(cls: type[Self], d: dict[str, Any]) -> Self:
        """Creates a new spatial extent from a dictionary."""
        return cls(**d)

    def __init__(self, bbox: PermissiveBbox | None = None):
        """Creates a new spatial extent."""
        self.bbox: Sequence[Sequence[float | int]]
        if bbox is None or len(bbox) == 0:
            self.bbox = [DEFAULT_BBOX]
        elif isinstance(bbox[0], Sequence):
            self.bbox = bbox  # type: ignore
        else:
            self.bbox = [bbox]  # type: ignore

    def to_dict(self) -> dict[str, Any]:
        """Converts this spatial extent to a dictionary."""
        return {"bbox": self.bbox}


class TemporalExtent:
    """A temporal extent."""

    @classmethod
    def from_dict(cls: type[Self], d: dict[str, Any]) -> Self:
        """Creates a new temporal extent from a dictionary."""
        return cls(**d)

    def __init__(
        self,
        interval: PermissiveInterval | None = None,
    ):
        """Creates a new temporal extent."""
        if interval is None:
            self.interval = [DEFAULT_INTERVAL]
        else:
            self.interval = []
            for value in interval:
                if isinstance(value, list):
                    self.interval.append(_create_interval(value))
                elif self.interval:  # Skip trailing values
                    warnings.warn(
                        "Invalid temporal interval (trailing single values), "
                        "discarding",
                        StacWarning,
                    )
                else:
                    self.interval.append(_create_interval(interval))  # type: ignore
                    break

    def to_dict(self) -> dict[str, Any]:
        """Converts this temporal extent to a dictionary."""
        return {"interval": self.interval}


def datetime_str(value: datetime.datetime | str | None) -> str | None:
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    elif value is None or isinstance(value, str):
        return value
    else:
        warnings.warn(
            f"Invalid interval value ({type(value)}), converting to None", StacWarning
        )
        return None


def _create_interval(
    interval: list[str | datetime.datetime | None],
) -> list[str | None]:
    if len(interval) == 0:
        warnings.warn("Invalid interval value (empty list)", StacWarning)
        interval = [None, None]
    elif len(interval) == 1:
        warnings.warn("Invalid interval value (single entry list)", StacWarning)
        interval.append(None)
    elif len(interval) > 2:
        warnings.warn(
            f"Invalid interval value ({len(interval)} values), truncating",
            StacWarning,
        )
        interval = interval[0:2]
    return [datetime_str(v) for v in interval]
