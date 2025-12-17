from __future__ import annotations

import copy
import datetime
import warnings
from collections.abc import Sequence
from typing import Any, Self

from . import deprecate
from .constants import DEFAULT_BBOX, DEFAULT_INTERVAL
from .errors import STACWarning
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
            self.spatial: SpatialExtent = SpatialExtent()
        elif isinstance(spatial, SpatialExtent):
            self.spatial = spatial
        else:
            self.spatial = SpatialExtent.from_dict(spatial)
        if temporal is None:
            self.temporal: TemporalExtent = TemporalExtent()
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

    @classmethod
    @deprecate.function("Use the constructor instead")
    def from_coordinates(
        cls: type[Self],
        coordinates: list[Any],
        extra_fields: dict[str, Any] | None = None,
    ) -> Self:
        if extra_fields:
            return cls(coordinates, **extra_fields)
        else:
            return cls(coordinates)

    def __init__(self, bbox: PermissiveBbox | None = None, **kwargs: Any):
        """Creates a new spatial extent."""
        self.bbox: Sequence[Sequence[float | int]]
        if bbox is None or len(bbox) == 0:
            self.bbox = [DEFAULT_BBOX]
        elif isinstance(bbox[0], Sequence):
            self.bbox = bbox  # pyright: ignore[reportAttributeAccessIssue]
        else:
            self.bbox = [bbox]  # pyright: ignore[reportAttributeAccessIssue]
        self.extra_fields: dict[str, Any] = kwargs

    def to_dict(self) -> dict[str, Any]:
        """Converts this spatial extent to a dictionary."""
        d = copy.deepcopy(self.extra_fields)
        d["bbox"] = self.bbox
        return d


class TemporalExtent:
    """A temporal extent."""

    @classmethod
    def from_dict(cls: type[Self], d: dict[str, Any]) -> Self:
        """Creates a new temporal extent from a dictionary."""
        return cls(**d)

    @classmethod
    def from_now(cls: type[Self]) -> Self:
        """Creates a new temporal extent that starts now and has no end time."""
        return cls([[datetime.datetime.now(tz=datetime.UTC), None]])

    def __init__(
        self,
        interval: PermissiveInterval | None = None,
    ):
        """Creates a new temporal extent."""
        if interval is None:
            self.interval: list[list[str | None]] = [DEFAULT_INTERVAL]
        else:
            self.interval = []
            for value in interval:
                if isinstance(value, list):
                    self.interval.append(_create_interval(value))
                elif self.interval:  # Skip trailing values
                    warnings.warn(
                        "Invalid temporal interval (trailing single values), "
                        "discarding",
                        STACWarning,
                    )
                else:
                    self.interval.append(_create_interval(interval))  # pyright: ignore[reportArgumentType]
                    break

    def to_dict(self) -> dict[str, Any]:
        """Converts this temporal extent to a dictionary."""
        return {"interval": self.interval}


def datetime_str(value: datetime.datetime | str | None) -> str | None:
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    elif value is None or isinstance(value, str):  # pyright: ignore[reportUnnecessaryIsInstance]
        return value
    else:
        warnings.warn(
            f"Invalid interval value ({type(value)}), converting to None", STACWarning
        )
        return None  # pyright: ignore[reportUnreachable]


def _create_interval(
    interval: list[str | datetime.datetime | None],
) -> list[str | None]:
    if len(interval) == 0:
        warnings.warn("Invalid interval value (empty list)", STACWarning)
        interval = [None, None]
    elif len(interval) == 1:
        warnings.warn("Invalid interval value (single entry list)", STACWarning)
        interval.append(None)
    elif len(interval) > 2:
        warnings.warn(
            f"Invalid interval value ({len(interval)} values), truncating",
            STACWarning,
        )
        interval = interval[0:2]
    return [datetime_str(v) for v in interval]
