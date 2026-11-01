from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Any

from slimconfig import Output


class Tool(StrEnum):
    WRITE_SQL_QUERY = "write_sql_query"


class Task(StrEnum):
    WRITE_SQL_QUERY = "write-sql-query"


@dataclass
class Filter(Output):
    column: Annotated[str, "A column in the selected table."]
    operator: Annotated[
        str,
        "Allowed operators: =, !=, >, >=, <, <=, LIKE, IS NULL, IS NOT NULL.",
    ]
    value: Annotated[
        Any,
        "A scalar parameter value (str, int, or float). "
        "NULL operators require None; other operators require a non-null scalar.",
    ]


@dataclass
class SortOrder(Output):
    column: Annotated[str, "A column in the selected table."]
    direction: Annotated[str, "Allowed directions: ASC or DESC."]


@dataclass
class WriteSQLQueryInput(Output):
    table: Annotated[str, "One of: authors, books, customers, orders."]
    columns: Annotated[
        list[str],
        "A nonempty list of valid columns, or exactly ['*'].",
    ]
    filters: Annotated[
        list[Filter],
        "Zero or more AND-connected filters.",
    ]
    order_by: Annotated[
        list[SortOrder],
        "Zero or more sorting specifications.",
    ]
    limit: Annotated[
        int | None,
        "Optional integer from 1 through 1000.",
    ]
    distinct: Annotated[bool, "Whether SELECT DISTINCT is used."]


@dataclass
class WriteSQLQueryOutput(Output):
    sql: Annotated[str, "The generated parameterized SQLite SELECT statement."]
    parameters: Annotated[
        list[Any],
        "Parameter values in SQL placeholder order (str, int, or float).",
    ]
    table: Annotated[str, "The selected table."]
    columns: Annotated[list[str], "The selected columns."]


TOOLS = {
    Tool.WRITE_SQL_QUERY: (WriteSQLQueryInput, WriteSQLQueryOutput),
}

TASKS = {
    Task.WRITE_SQL_QUERY: (WriteSQLQueryInput, WriteSQLQueryOutput),
}