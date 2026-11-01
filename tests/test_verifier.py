import pytest

from contract import Task, Tool
from src.plugin.write_sql_query import write_sql_query
from verifier import verify_input, verify_output, verify_task


def base_input(**overrides):
    data = {
        "table": "books",
        "columns": ["title", "price"],
        "filters": [],
        "order_by": [],
        "limit": None,
        "distinct": False,
    }
    data.update(overrides)
    return data


def correct_output(inputs):
    return write_sql_query(**inputs)


def test_verify_valid_input():
    assert verify_input(
        Tool.WRITE_SQL_QUERY,
        base_input(),
    ) is None


def test_verify_invalid_tool():
    assert verify_input(
        "unknown_tool",
        base_input(),
    ) == "unknown tool"


@pytest.mark.parametrize(
    "table",
    ["unknown", "", " ", "BOOKS"],
)
def test_verify_invalid_table(table):
    result = verify_input(
        Tool.WRITE_SQL_QUERY,
        base_input(table=table),
    )

    assert result == "unknown or invalid table"


def test_verify_unknown_column():
    result = verify_input(
        Tool.WRITE_SQL_QUERY,
        base_input(columns=["not_a_column"]),
    )

    assert result == "unknown selected column"


def test_verify_empty_columns():
    result = verify_input(
        Tool.WRITE_SQL_QUERY,
        base_input(columns=[]),
    )

    assert result == "columns must be a nonempty list"


def test_verify_invalid_operator():
    result = verify_input(
        Tool.WRITE_SQL_QUERY,
        base_input(
            filters=[
                {
                    "column": "price",
                    "operator": "INJECT",
                    "value": 10,
                }
            ]
        ),
    )

    assert result == "unsupported filter operator"


def test_verify_invalid_limit():
    result = verify_input(
        Tool.WRITE_SQL_QUERY,
        base_input(limit=1001),
    )

    assert result == "limit must be an integer from 1 through 1000"


def test_verify_boolean_limit():
    result = verify_input(
        Tool.WRITE_SQL_QUERY,
        base_input(limit=True),
    )

    assert result == "limit must be an integer from 1 through 1000"


def test_verify_invalid_distinct():
    result = verify_input(
        Tool.WRITE_SQL_QUERY,
        base_input(distinct=1),
    )

    assert result == "distinct must be a boolean"


def test_verify_missing_input_field():
    inputs = base_input()
    del inputs["table"]

    result = verify_input(Tool.WRITE_SQL_QUERY, inputs)

    assert result == "missing input field: table"


def test_verify_correct_output():
    inputs = base_input()
    output = correct_output(inputs)

    assert verify_output(
        Tool.WRITE_SQL_QUERY,
        inputs,
        output,
        None,
    ) is None


@pytest.mark.parametrize(
    ("field", "wrong_value"),
    [
        ("sql", "SELECT * FROM authors"),
        ("parameters", [999]),
        ("table", "authors"),
        ("columns", ["id"]),
    ],
)
def test_verify_wrong_output_field(field, wrong_value):
    inputs = base_input()
    output = correct_output(inputs)
    output[field] = wrong_value

    result = verify_output(
        Tool.WRITE_SQL_QUERY,
        inputs,
        output,
        None,
    )

    assert result is not None
    assert result.startswith(f"{field}:")


@pytest.mark.parametrize(
    "field",
    ["sql", "parameters", "table", "columns"],
)
def test_verify_missing_output_field(field):
    inputs = base_input()
    output = correct_output(inputs)
    del output[field]

    result = verify_output(
        Tool.WRITE_SQL_QUERY,
        inputs,
        output,
        None,
    )

    assert result == f"missing field: {field}"


def test_verify_missing_output_object():
    result = verify_output(
        Tool.WRITE_SQL_QUERY,
        base_input(),
        None,
        None,
    )

    assert result == "output must be an object"


def test_verify_wrong_sql_type():
    inputs = base_input()
    output = correct_output(inputs)
    output["sql"] = 123

    assert verify_output(
        Tool.WRITE_SQL_QUERY,
        inputs,
        output,
        None,
    ) == "sql must be a string"


def test_verify_wrong_parameters_type():
    inputs = base_input()
    output = correct_output(inputs)
    output["parameters"] = "not a list"

    assert verify_output(
        Tool.WRITE_SQL_QUERY,
        inputs,
        output,
        None,
    ) == "parameters must be a list"


def test_verify_wrong_table_type():
    inputs = base_input()
    output = correct_output(inputs)
    output["table"] = 123

    assert verify_output(
        Tool.WRITE_SQL_QUERY,
        inputs,
        output,
        None,
    ) == "table must be a string"


def test_verify_wrong_columns_type():
    inputs = base_input()
    output = correct_output(inputs)
    output["columns"] = "title"

    assert verify_output(
        Tool.WRITE_SQL_QUERY,
        inputs,
        output,
        None,
    ) == "columns must be a list"


def test_verify_task_with_string_tool():
    inputs = base_input()
    output = correct_output(inputs)

    assert verify_task(
        Task.WRITE_SQL_QUERY,
        "write_sql_query",
        inputs,
        output,
        None,
    ) is None


def test_verify_task_with_tool_list():
    inputs = base_input()
    output = correct_output(inputs)

    assert verify_task(
        Task.WRITE_SQL_QUERY,
        ["write_sql_query"],
        inputs,
        output,
        None,
    ) is None


def test_verify_task_missing_tool():
    inputs = base_input()
    output = correct_output(inputs)

    assert verify_task(
        Task.WRITE_SQL_QUERY,
        [],
        inputs,
        output,
        None,
    ) == "required tool is missing"


def test_verify_unknown_task():
    assert verify_task(
        "unknown-task",
        ["write_sql_query"],
        base_input(),
        {},
        None,
    ) == "unknown task"


def test_verify_task_rejects_wrong_output():
    inputs = base_input()
    output = correct_output(inputs)
    output["table"] = "authors"

    result = verify_task(
        Task.WRITE_SQL_QUERY,
        ["write_sql_query"],
        inputs,
        output,
        None,
    )

    assert result.startswith("table:")


def test_verify_null_optional_limit():
    inputs = base_input(limit=None)
    output = correct_output(inputs)

    assert verify_output(
        Tool.WRITE_SQL_QUERY,
        inputs,
        output,
        None,
    ) is None


def test_verify_boundary_limit_one():
    inputs = base_input(limit=1)
    output = correct_output(inputs)

    assert verify_output(
        Tool.WRITE_SQL_QUERY,
        inputs,
        output,
        None,
    ) is None


def test_verify_boundary_limit_maximum():
    inputs = base_input(limit=1000)
    output = correct_output(inputs)

    assert verify_output(
        Tool.WRITE_SQL_QUERY,
        inputs,
        output,
        None,
    ) is None


def test_verify_boundary_limit_exceeded():
    inputs = base_input(limit=1001)

    assert verify_input(
        Tool.WRITE_SQL_QUERY,
        inputs,
    ) is not None


def test_verify_invalid_filter_shape():
    inputs = base_input(filters=[{"column": "price"}])

    assert verify_input(
        Tool.WRITE_SQL_QUERY,
        inputs,
    ) == "filter must contain column, operator, and value"


def test_verify_invalid_filter_value():
    inputs = base_input(
        filters=[
            {
                "column": "price",
                "operator": ">",
                "value": True,
            }
        ]
    )

    assert verify_input(
        Tool.WRITE_SQL_QUERY,
        inputs,
    ) == "filter value must be a finite scalar or null"


def test_verify_null_operator():
    inputs = base_input(
        filters=[
            {
                "column": "price",
                "operator": "IS NULL",
                "value": None,
            }
        ]
    )

    output = correct_output(inputs)

    assert verify_output(
        Tool.WRITE_SQL_QUERY,
        inputs,
        output,
        None,
    ) is None


def test_verify_unknown_sort_direction():
    inputs = base_input(
        order_by=[
            {
                "column": "price",
                "direction": "UP",
            }
        ]
    )

    assert verify_input(
        Tool.WRITE_SQL_QUERY,
        inputs,
    ) == "unsupported sorting direction"


def test_verify_invalid_sort_column():
    inputs = base_input(
        order_by=[
            {
                "column": "unknown",
                "direction": "ASC",
            }
        ]
    )

    assert verify_input(
        Tool.WRITE_SQL_QUERY,
        inputs,
    ) == "unknown sorting column"