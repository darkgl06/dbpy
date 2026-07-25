import abc

from dbpy.types import Schema, RecordBatch


class DataSource(abc.ABC):
    """
    Abstract class representing a data source.
    """
    @abc.abstractmethod
    def get_schema(self) -> Schema:
        """
        Return the schema of the data source. It's used by the query planner to validates the query.
        :return:
        """
        pass

    @abc.abstractmethod
    def scan(self, projection: list[str]) -> list[RecordBatch]:
        """
        Reads the data and return it as a tuple of record batches
        :param projection: Columns to read
        :return:
        """
        pass