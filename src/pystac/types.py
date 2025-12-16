import datetime
from collections.abc import Sequence

PermissiveBbox = Sequence[Sequence[float | int]] | Sequence[float | int]
PermissiveInterval = (
    Sequence[Sequence[str | datetime.datetime | None]]
    | Sequence[str | datetime.datetime | None]
)
