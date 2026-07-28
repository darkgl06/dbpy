from email import header
from typing import Iterator, Any

from dbpy.datasources import DataSource
from dbpy.types import RecordBatch, Schema, Field, BaseType, ColumnVector, IntType, FloatType, StringType
import functools

import csv


class CSVDataSource(DataSource):
    """
    Reads data from a CSV file.

    Here is what a CSV file might look like:
    id,name,department,salary
    1,Alice,Engineering,95000
    2,Bob,Sales,87000
    3,Carol,Engineering,102000
    """

    def __init__(self, *, path: str, schema: Schema | None = None):
        self.path = path
        self.schema = schema if schema else self.get_schema()
        self._batch_size = 1024

    @functools.cache
    def get_schema(self) -> Schema:
        with open(
                self.path,
                mode="r",
                encoding="utf-8",
                newline="",
        ) as file:
            reader = csv.reader(file)

            try:
                headers = next(reader)
                first_row = next(reader)
            except StopIteration as error:
                raise ValueError(
                    "Cannot infer schema from an empty CSV file"
                ) from error

        if len(headers) != len(first_row):
            raise ValueError(
                "CSV header and first row have different column counts"
            )

        fields = [
            Field(
                name=name,
                dtype=BaseType.deduce_dtype(value),
            )
            for name, value in zip(
                headers,
                first_row,
                strict=True,
            )
        ]

        return Schema(fields)

    @staticmethod
    def _parse_value(
            value: str,
            dtype: BaseType,
    ) -> Any:
        value = value.strip()

        if isinstance(dtype, IntType):
            return int(value)

        if isinstance(dtype, FloatType):
            return float(value)

        if isinstance(dtype, StringType):
            return value

        raise TypeError(f"Unsupported data type: {dtype}")

    def _create_record_batch(
            self,
            column_names: list[str],
            rows: list[list[str]],
    ) -> RecordBatch:
        selected_fields = [
            self.schema.get_field_by_name(column_name)
            for column_name in column_names
        ]

        vectors: list[ColumnVector] = []

        for column_index, field in enumerate(selected_fields):
            raw_values = [
                row[column_index]
                for row in rows
            ]

            parsed_values = [
                self._parse_value(value, field.dtype)
                for value in raw_values
            ]

            vectors.append(
                ColumnVector(
                    dtype=field.dtype,
                    values=parsed_values,
                )
            )

        projected_schema = Schema(selected_fields)

        return RecordBatch(
            schema=projected_schema,
            fields=vectors,
        )

    def scan(
        self,
        projection: list[str] | None = None,
    ) -> Iterator[RecordBatch]:
        """
        Sequentially scans the CSV and yields RecordBatch objects.
        """
        with open(
            self.path,
            mode="r",
            encoding="utf-8",
            newline="",
        ) as file:
            reader = csv.reader(file)

            try:
                headers = next(reader)
            except StopIteration:
                return

            selected_columns = projection or headers

            unknown_columns = [
                column
                for column in selected_columns
                if column not in headers
            ]

            if unknown_columns:
                raise ValueError(
                    f"Unknown columns: {unknown_columns}"
                )

            projection_indexes = [
                headers.index(column)
                for column in selected_columns
            ]

            batch_records: list[list[str]] = []

            for row_number, row in enumerate(reader, start=2):
                if len(row) != len(headers):
                    raise ValueError(
                        f"Invalid column count at row {row_number}: "
                        f"expected {len(headers)}, got {len(row)}"
                    )

                projected_row = [
                    row[index]
                    for index in projection_indexes
                ]

                batch_records.append(projected_row)

                if len(batch_records) == self._batch_size:
                    yield self._create_record_batch(
                        selected_columns,
                        batch_records,
                    )

                    batch_records = []

            # This must remain outside the for loop.
            if batch_records:
                yield self._create_record_batch(
                    selected_columns,
                    batch_records,
                )
