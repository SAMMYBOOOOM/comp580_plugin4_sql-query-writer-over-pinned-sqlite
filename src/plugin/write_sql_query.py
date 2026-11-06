import math
from typing import Any

from contract import WriteSQLQueryOutput


SCHEMA = {
    "authors": {
        "id": "INTEGER",
        "name": "TEXT",
        "country": "TEXT",
    },
    "books": {
        "id": "INTEGER",
        "title": "TEXT",
        "author_id": "INTEGER",
        "price": "REAL",
        "published_year": "INTEGER",
        "stock": "INTEGER",
    },
    "customers": {
        "id": "INTEGER",
        "name": "TEXT",
        "email": "TEXT",
        "country": "TEXT",
    },
    "orders": {
        "id": "INTEGER",
        "customer_id": "INTEGER",
        "order_date": "TEXT",
        "total_amount": "REAL",
        "status": "TEXT",
    },
}

ALLOWED_OPERATORS = {
    "=",
    "!=",
    ">",
    ">=",
    "<",
    "<=",
    "LIKE",
    "IS NULL",
    "IS NOT NULL",
}

ALLOWED_DIRECTIONS = {"ASC", "DESC"}

MAX_LIMIT = 1000


def _validate_scalar(value: Any) -> bool:
    if value is None:
        return True

    if type(value) in (str, int):
        return True

    if type(value) is float:
        return math.isfinite(value)

    return False


def _validate_input(
    table: Any,
    columns: Any,
    filters: Any,
    order_by: Any,
    limit: Any,
    distinct: Any,
) -> None:
    if type(table) is not str or table not in SCHEMA:
        raise ValueError("unknown or invalid table")

    if type(columns) is not list or not columns:
        raise ValueError("columns must be a nonempty list")

    if not all(type(column) is str for column in columns):
        raise ValueError("column names must be strings")

    if columns == ["*"]:
        pass
    elif "*" in columns:
        raise ValueError("wildcard must be used alone")
    elif len(set(columns)) != len(columns):
        raise ValueError("duplicate selected columns")
    elif any(column not in SCHEMA[table] for column in columns):
        raise ValueError("unknown selected column")

    if type(filters) is not list:
        raise ValueError("filters must be a list")

    for item in filters:
        if type(item) is not dict:
            raise ValueError("each filter must be an object")

        if set(item) != {"column", "operator", "value"}:
            raise ValueError("filter must contain column, operator, and value")

        column = item["column"]
        operator = item["operator"]
        value = item["value"]

        if type(column) is not str or column not in SCHEMA[table]:
            raise ValueError("unknown filter column")

        if type(operator) is not str or operator not in ALLOWED_OPERATORS:
            raise ValueError("unsupported filter operator")

        if not _validate_scalar(value):
            raise ValueError("filter value must be a finite scalar or null")

        if operator in {"IS NULL", "IS NOT NULL"}:
            if value is not None:
                raise ValueError("NULL operators require a null value")
        elif value is None:
            raise ValueError("comparison operators require a non-null value")

        if operator == "LIKE" and type(value) is not str:
            raise ValueError("LIKE requires a string value")

    if type(order_by) is not list:
        raise ValueError("order_by must be a list")

    seen_sort_columns = set()

    for item in order_by:
        if type(item) is not dict:
            raise ValueError("each sorting specification must be an object")

        if set(item) != {"column", "direction"}:
            raise ValueError("sorting specification must contain column and direction")

        column = item["column"]
        direction = item["direction"]

        if type(column) is not str or column not in SCHEMA[table]:
            raise ValueError("unknown sorting column")

        if column in seen_sort_columns:
            raise ValueError("duplicate sorting column")

        seen_sort_columns.add(column)

        if type(direction) is not str or direction not in ALLOWED_DIRECTIONS:
            raise ValueError("unsupported sorting direction")

    if limit is not None and (type(limit) is not int or not 1 <= limit <= MAX_LIMIT):
        raise ValueError("limit must be an integer from 1 through 1000")

    if type(distinct) is not bool:
        raise ValueError("distinct must be a boolean")


def _generate(
    table: str,
    columns: list[str],
    filters: list[dict],
    order_by: list[dict],
    limit: int | None,
    distinct: bool,
) -> dict:
    selected = ", ".join(f'"{column}"' for column in columns)

    distinct_clause = "DISTINCT " if distinct else ""

    sql = f'SELECT {distinct_clause}{selected} FROM "{table}"'
    parameters = []

    if filters:
        conditions = []

        for item in filters:
            column = item["column"]
            operator = item["operator"]
            value = item["value"]

            if operator in {"IS NULL", "IS NOT NULL"}:
                conditions.append(f'"{column}" {operator}')
            else:
                conditions.append(f'"{column}" {operator} ?')
                parameters.append(value)

        sql += " WHERE " + " AND ".join(conditions)

    if order_by:
        ordering = [
            f'"{item["column"]}" {item["direction"]}'
            for item in order_by
        ]
        sql += " ORDER BY " + ", ".join(ordering)

    if limit is not None:
        sql += " LIMIT ?"
        parameters.append(limit)

    return {
        "sql": sql,
        "parameters": parameters,
        "table": table,
        "columns": columns.copy(),
    }


def write_sql_query(
    table: str,
    columns: list[str],
    filters: list[dict],
    order_by: list[dict],
    limit: int | None = None,
    distinct: bool = False,
) -> dict:
    """
    Generate a parameterized SQLite SELECT query.

    Only the pinned bookstore schema is supported.
    No SQL is executed by this tool.
    """
    _validate_input(
        table,
        columns,
        filters,
        order_by,
        limit,
        distinct,
    )

    result = _generate(
        table,
        columns,
        filters,
        order_by,
        limit,
        distinct,
    )

    output = WriteSQLQueryOutput(
        sql=result["sql"],
        parameters=result["parameters"],
        table=result["table"],
        columns=result["columns"],
    )

    return {
        "sql": output.sql,
        "parameters": output.parameters,
        "table": output.table,
        "columns": output.columns,
    }