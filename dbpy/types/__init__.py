import abc
import typing
from dataclasses import dataclass, field
import pyarrow as pa

from enum import Enum

@dataclass(frozen=True)
class BaseType:
    """BaseType is the Apache Arrow's wrapper"""
    name: str = field(init=False)


@dataclass(frozen=True)
class IntType(BaseType):
    bit_width: int
    name: str = field(init=False, default="int")

    def __post_init__(self):
        if self.bit_width not in (8, 16, 32, 64):
            raise ValueError("bit_width must be 8, 16, 32 or 64")

    def to_arrow(self) -> pa.DataType:
        mapping = {
            8: pa.int8(),
            16: pa.int16(),
            32: pa.int32(),
            64: pa.int64(),
        }
        return mapping[self.bit_width]


@dataclass(frozen=True)
class FloatType(BaseType):
    class FloatingPrecision(Enum):
        SINGLE = "single"
        DOUBLE = "double"

    name: str = field(init=False, default="float")
    variant: FloatingPrecision

    def to_arrow(self) -> pa.DataType:
        return pa.float32() if self.variant is self.FloatingPrecision.SINGLE else pa.float64()


@dataclass(frozen=True)
class StringType(BaseType):
    name: str = field(init=False, default="string")

    def to_arrow(self) -> pa.DataType:
        return pa.string()


class Field:
    """Represents a column in a table"""

    def __init__(self, name: str, dtype: BaseType):
        self.name = name
        self.dtype = dtype
        self.rules = None # TODO

    def __repr__(self) -> str:
        return f"Field(name={self.name!r}, type={self.dtype})"


class Schema:
    def __init__(self, fields: list[Field]):
        self._fields = fields

    def __len__(self) -> int:
        return len(self._fields)

    def get_field(self, index: int) -> Field:
        return self._fields[index]


### Vectors

class BaseColumnVector(abc.ABC):
    """Represents a vector in a table"""

    def __init__(self, dtype: BaseType, size: int):
        if size < 0:
            raise ValueError("size cannot be negative")

        self.dtype = dtype
        self.size = size

    def __len__(self) -> int:
        return self.size

    def get_type(self) -> BaseType:
        return self.dtype

    def _validate_index(self, index: int) -> None:
        if index < 0 or index >= self.size:
            raise IndexError("index out of range")

    @abc.abstractmethod
    def get_value(self, index: int) -> typing.Any:
        raise NotImplementedError


class ColumnVector(BaseColumnVector):
    def __init__(self, dtype: BaseType, values: list[typing.Any]):
        self.values = values
        super().__init__(dtype, len(values))

    def get_value(self, index: int) -> typing.Any:
        self._validate_index(index)
        return self.values[index]

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.values})"


class LiteralColumnVector(BaseColumnVector):
    """Represents a virtual vector containing one repeated value."""

    def __init__(self, dtype: BaseType, value: typing.Any, size: int):
        self.value = value
        super().__init__(dtype, size)

    def get_value(self, index: int) -> typing.Any:
        self._validate_index(index)
        return self.value

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(value={self.value!r}, size={self.size})"
        )


class RecordBatch:
    """
    Record batches represents small pieces of data in a table.

    They are very useful when we want to get data from a table, but it has thousand or hundred of thousand of records
    that will impact the performance. Instead of loading everything in memory, we pick a small piece.
    """

    def __init__(self, schema: Schema, fields: list[BaseColumnVector]):
        self._schema = schema
        self._fields = fields

    def column_count(self) -> int:
        return len(self._fields)

    def row_count(self) -> int:
        """All vectors must have the same number of rows."""
        if not self._fields:
            return 0
        return len(self._fields[0])

    def __repr__(self) -> str:
        columns = []

        for index, vector in enumerate(self._fields):
            field = self._schema.get_field(index)

            values = [
                vector.get_value(row)
                for row in range(self.row_count())
            ]

            columns.append(f"{field}={values!r}")

        formatted_columns = ", ".join(columns)

        return (
            f"RecordBatch("
            f"rows={self.row_count()}, "
            f"columns={self.column_count()}, "
            f"data={{ {formatted_columns} }}"
            f")"
        )