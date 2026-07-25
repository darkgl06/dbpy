from pathlib import Path

from dbpy.datasources.csv import CSVDataSource
from dbpy.types import StringType, FloatType, IntType


def test_open_csv_works():
    path = Path("./tests/datasources/test.csv")

    csv_source = CSVDataSource(path=str(path.absolute()))

    schema = csv_source.get_schema()

    assert  isinstance(schema.get_field(0).dtype, StringType)
    assert  isinstance(schema.get_field(1).dtype, IntType)
    assert  isinstance(schema.get_field(2).dtype, FloatType)