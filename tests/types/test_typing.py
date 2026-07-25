import pytest
from dbpy.types import IntType, LiteralColumnVector, ColumnVector, RecordBatch, Schema, Field, \
    FloatType, StringType


def test_vectors_can_return_right_values() -> None:
    vector = ColumnVector(
        IntType(8),
        [1, 2, 3, 4]
    )

    value = vector.get_value(0)

    assert value == 1


def test_vectors_raise_exception_when_index_is_out_of_bounds() -> None:
    vector = ColumnVector(
        IntType(8),
        [1, 2, 3, 4]
    )

    with pytest.raises(IndexError):
        vector.get_value(-1)


def test_literal_column_is_fulfilled_with_the_same_value() -> None:
    literal_integer_vector = LiteralColumnVector(IntType(8), 1, 6)

    for index in range(5):
        assert literal_integer_vector.get_value(index) == 1


def test_record_batches_contains_values() -> None:
    schema = Schema(
        [
            Field("age", IntType(8)),
            Field("money", FloatType(variant=FloatType.FloatingPrecision.SINGLE)),
            Field("name", StringType()),
        ]
    )
    record_batch = RecordBatch(
        schema=schema,
        fields=[
            ColumnVector(IntType(8), [1, 2, 3, 4]),
            ColumnVector(FloatType(variant=FloatType.FloatingPrecision.SINGLE), [56.1, 87.1, 33.5, 46.1]),
            ColumnVector(StringType(), ["John", "Andrew", "Matthew", "Anne"]),
        ]
    )

    print(record_batch)