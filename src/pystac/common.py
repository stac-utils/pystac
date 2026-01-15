from __future__ import annotations

from typing import Literal, TypedDict


class T_Basics(TypedDict, total=False):
    title: str
    description: str
    keywords: list[str]
    roles: list[str]


class T_DateTime(TypedDict, total=False):
    datetime: str
    created: str
    updated: str
    start_datetime: str
    end_datetime: str


class T_Instrument(TypedDict, total=False):
    platform: str
    instruments: list[str]
    constellation: str
    mission: str
    gsd: int


class T_Statistics(TypedDict, total=False):
    minimum: float
    maximum: float
    mean: float
    stddev: float
    count: int
    valid_percent: float


class T_DataValue(TypedDict, total=False):
    nodata: float | str
    unit: str
    data_type: DataType
    statistics: T_Statistics


type DataType = Literal[
    "int8",
    "int16",
    "int32",
    "int64",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "float16",
    "float32",
    "float64",
    "cint16",
    "cint32",
    "cfloat32",
    "cfloat64",
    "other",
]
