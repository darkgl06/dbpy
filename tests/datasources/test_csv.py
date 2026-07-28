import pytest

from dbpy.datasources.csv import CSVDataSource
from dbpy.types import (
    FloatType,
    IntType,
    StringType,
)


@pytest.fixture
def csv_file(tmp_path):
    path = tmp_path / "employees.csv"

    path.write_text(
        "\n".join(
            [
                "id,name,department,salary",
                "1,Alice,Engineering,95000.5",
                "2,Bob,Sales,87000.0",
                "3,Carol,Engineering,102000.75",
            ]
        ),
        encoding="utf-8",
    )

    return path


def test_get_schema_deduces_column_types(csv_file):
    source = CSVDataSource(path=str(csv_file))

    schema = source.get_schema()

    assert len(schema) == 4

    assert schema.get_field(0).name == "id"
    assert isinstance(schema.get_field(0).dtype, IntType)

    assert schema.get_field(1).name == "name"
    assert isinstance(schema.get_field(1).dtype, StringType)

    assert schema.get_field(2).name == "department"
    assert isinstance(schema.get_field(2).dtype, StringType)

    assert schema.get_field(3).name == "salary"
    assert isinstance(schema.get_field(3).dtype, FloatType)


def test_scan_returns_all_columns_when_projection_is_empty(csv_file):
    source = CSVDataSource(path=str(csv_file))

    batches = list(source.scan([]))

    assert len(batches) == 1

    batch = batches[0]

    assert batch.row_count() == 3
    assert batch.column_count() == 4

    assert batch._fields[0].values == [1, 2, 3]
    assert batch._fields[1].values == ["Alice", "Bob", "Carol"]
    assert batch._fields[2].values == [
        "Engineering",
        "Sales",
        "Engineering",
    ]
    assert batch._fields[3].values == [
        95000.5,
        87000.0,
        102000.75,
    ]


def test_scan_applies_projection(csv_file):
    source = CSVDataSource(path=str(csv_file))

    batches = list(source.scan(["name", "salary"]))

    assert len(batches) == 1

    batch = batches[0]

    assert batch.row_count() == 3
    assert batch.column_count() == 2

    assert batch._schema.get_field(0).name == "name"
    assert batch._schema.get_field(1).name == "salary"

    assert batch._fields[0].values == [
        "Alice",
        "Bob",
        "Carol",
    ]
    assert batch._fields[1].values == [
        95000.5,
        87000.0,
        102000.75,
    ]


def test_scan_preserves_projection_order(csv_file):
    source = CSVDataSource(path=str(csv_file))

    batches = list(source.scan(["salary", "id"]))

    batch = batches[0]

    assert batch._schema.get_field(0).name == "salary"
    assert batch._schema.get_field(1).name == "id"

    assert batch._fields[0].values == [
        95000.5,
        87000.0,
        102000.75,
    ]
    assert batch._fields[1].values == [1, 2, 3]


def test_scan_raises_error_for_unknown_column(csv_file):
    source = CSVDataSource(path=str(csv_file))

    with pytest.raises(
        ValueError,
        match="Unknown columns",
    ):
        list(source.scan(["name", "unknown"]))


def test_scan_creates_multiple_batches(csv_file):
    source = CSVDataSource(path=str(csv_file))
    source._batch_size = 2

    batches = list(source.scan(["id", "name"]))

    assert len(batches) == 2

    first_batch = batches[0]
    second_batch = batches[1]

    assert first_batch.row_count() == 2
    assert first_batch._fields[0].values == [1, 2]
    assert first_batch._fields[1].values == ["Alice", "Bob"]

    assert second_batch.row_count() == 1
    assert second_batch._fields[0].values == [3]
    assert second_batch._fields[1].values == ["Carol"]


def test_scan_does_not_duplicate_rows(csv_file):
    source = CSVDataSource(path=str(csv_file))
    source._batch_size = 2

    batches = list(source.scan(["id"]))

    ids = [
        value
        for batch in batches
        for value in batch._fields[0].values
    ]

    assert ids == [1, 2, 3]


def test_scan_empty_data_file_returns_no_batches(tmp_path):
    path = tmp_path / "empty_data.csv"

    path.write_text(
        "id,name\n",
        encoding="utf-8",
    )

    source = CSVDataSource(
        path=str(path),
        schema=None,
    )

    with pytest.raises(ValueError):
        source.get_schema()


def test_scan_rejects_rows_with_wrong_column_count(tmp_path):
    path = tmp_path / "invalid.csv"

    path.write_text(
        "\n".join(
            [
                "id,name,salary",
                "1,Alice,95000",
                "2,Bob",
            ]
        ),
        encoding="utf-8",
    )

    source = CSVDataSource(path=str(path))

    with pytest.raises(
        ValueError,
        match="Invalid column count",
    ):
        list(source.scan([]))