import math
from collections.abc import Iterable

from contract import TASKS, TOOLS, Task, Tool


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

OPERATORS = {
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

DIRECTIONS = {"ASC", "DESC"}


def _scalar_is_valid(value):
    if value is None:
        return True
    if type(value) in (str, int):
        return True
    if type(value) is float:
        return math.isfinite(value)
    return False


def _derive(inputs):
    if type(inputs) is not dict:
        return "inputs must be an object"

    required = {
        "table",
        "columns",
        "filters",
        "order_by",
        "limit",
        "distinct",
    }

    for field in required:
        if field not in inputs:
            return f"missing input field: {field}"

    table = inputs["table"]
    columns = inputs["columns"]
    filters = inputs["filters"]
    order_by = inputs["order_by"]
    limit = inputs["limit"]
    distinct = inputs["distinct"]

    if type(table) is not str or table not in SCHEMA:
        return "unknown or invalid table"

    if type(columns) is not list or not columns:
        return "columns must be a nonempty list"

    if not all(type(column) is str for column in columns):
        return "column names must be strings"

    if columns == ["*"]:
        pass
    elif "*" in columns:
        return "wildcard must be used alone"
    elif len(set(columns)) != len(columns):
        return "duplicate selected columns"
    elif any(column not in SCHEMA[table] for column in columns):
        return "unknown selected column"

    if type(filters) is not list:
        return "filters must be a list"

    for item in filters:
        if type(item) is not dict:
            return "each filter must be an object"

        if set(item) != {"column", "operator", "value"}:
            return "filter must contain column, operator, and value"

        column = item["column"]
        operator = item["operator"]
        value = item["value"]

        if type(column) is not str or column not in SCHEMA[table]:
            return "unknown filter column"

        if type(operator) is not str or operator not in OPERATORS:
            return "unsupported filter operator"

        if not _scalar_is_valid(value):
            return "filter value must be a finite scalar or null"

        if operator in {"IS NULL", "IS NOT NULL"}:
            if value is not None:
                return "NULL operators require a null value"
        elif value is None:
            return "comparison operators require a non-null value"

        if operator == "LIKE" and type(value) is not str:
            return "LIKE requires a string value"

    if type(order_by) is not list:
        return "order_by must be a list"

    seen = set()

    for item in order_by:
        if type(item) is not dict:
            return "each sorting specification must be an object"

        if set(item) != {"column", "direction"}:
            return "sorting specification must contain column and direction"

        column = item["column"]
        direction = item["direction"]

        if type(column) is not str or column not in SCHEMA[table]:
            return "unknown sorting column"

        if column in seen:
            return "duplicate sorting column"

        seen.add(column)

        if type(direction) is not str or direction not in DIRECTIONS:
            return "unsupported sorting direction"

    if limit is not None:
        if type(limit) is not int or not 1 <= limit <= 1000:
            return "limit must be an integer from 1 through 1000"

    if type(distinct) is not bool:
        return "distinct must be a boolean"

    selected = ", ".join(f'"{column}"' for column in columns)
    prefix = "DISTINCT " if distinct else ""

    sql = f'SELECT {prefix}{selected} FROM "{table}"'
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
        ordering = []

        for item in order_by:
            ordering.append(
                f'"{item["column"]}" {item["direction"]}'
            )

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


def _valid_tool(tool):
    return tool == Tool.WRITE_SQL_QUERY or tool == "write_sql_query"


def verify_input(tool, inputs):
    if not _valid_tool(tool):
        return "unknown tool"

    expected = _derive(inputs)

    if isinstance(expected, str):
        return expected

    return None


def verify_output(tool, inputs, output, ctx):
    if not _valid_tool(tool):
        return "unknown tool"

    expected = _derive(inputs)

    if isinstance(expected, str):
        return expected

    if type(output) is not dict:
        return "output must be an object"

    fields = (
        "sql",
        "parameters",
        "table",
        "columns",
    )

    for field in fields:
        if field not in output:
            return f"missing field: {field}"

    if type(output["sql"]) is not str:
        return "sql must be a string"

    if type(output["parameters"]) is not list:
        return "parameters must be a list"

    if type(output["table"]) is not str:
        return "table must be a string"

    if type(output["columns"]) is not list:
        return "columns must be a list"

    checks = (
        ("sql", expected["sql"], output["sql"]),
        ("parameters", expected["parameters"], output["parameters"]),
        ("table", expected["table"], output["table"]),
        ("columns", expected["columns"], output["columns"]),
    )

    for field, exp, act in checks:
        if exp != act:
            return f"{field}: expected {exp!r}, got {act!r}"

    return None


def verify_task(task, tools, inputs, output, ctx):
    if task != Task.WRITE_SQL_QUERY and task != "write-sql-query":
        return "unknown task"

    if task not in TASKS and task != "write-sql-query":
        return "task is not registered"

    if isinstance(tools, str):
        available = {tools}
    else:
        try:
            available = set(tools)
        except TypeError:
            return "tools must be a string or iterable"

    if (
        Tool.WRITE_SQL_QUERY not in available
        and "write_sql_query" not in available
    ):
        return "required tool is missing"

    return verify_output(
        Tool.WRITE_SQL_QUERY,
        inputs,
        output,
        ctx,
    )