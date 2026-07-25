from dbpy.datasources import DataSource
from dbpy.types import RecordBatch, Schema, Field, BaseType
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

    def _extract_headers_or_default(self, line: str) -> list[str]:
        """
        Tries to extract headers from the first line of the CSV file, otherwise will generate default headers
        :param line:
        :return:
        """


    @functools.cache
    def get_schema(self) -> Schema:
        with open(self.path) as f:
            reader = csv.reader(f)
            headers = next(reader)
            first_line = next(reader)
        fields = [
            Field(name, BaseType.deduce_dtype(value)) for name, value in zip(headers, first_line)
        ]
        return Schema(fields)

    def scan(self, projection: list[str]) -> list[RecordBatch]:
        pass
