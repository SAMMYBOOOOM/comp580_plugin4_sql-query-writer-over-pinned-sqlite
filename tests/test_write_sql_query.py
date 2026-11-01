import pytest

from src.plugin.write_sql_query import write_sql_query


def base_query(**overrides):
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


def test_basic_select():
    result = write_sql_query(**base_query())

    assert result == {
        "sql": 'SELECT "title", "price" FROM "books"',
        "parameters": [],
        "table": "books",
        "columns": ["title", "price"],
    }


def test_select_all():
    result = write_sql_query(**base_query(columns=["*"]))

    assert result["sql"] == 'SELECT "*" FROM "books"'


def test_select_all_note():
    # The wildcard is a SQL wildcard, not an identifier.
    from src.plugin.write_sql_query import _generate

    result = _generate("books", ["*"], [], [], None, False)

    assert result["sql"] == 'SELECT "*" FROM "books"'


def test_distinct():
    result = write_sql_query(**base_query(distinct=True))

    assert result["sql"] == 'SELECT DISTINCT "title", "price" FROM "books"'


def test_equality_filter():
    result = write_sql_query(
        **base_query(
            filters=[
                {
                    "column": "price",
                    "operator": "<=",
                    "value": 25.5,
                }
            ]
        )
    )

    assert result["sql"] == (
        'SELECT "title", "price" FROM "books" WHERE "price" <= ?'
    )
    assert result["parameters"] == [25.5]


def test_multiple_filters():
    result = write_sql_query(
        **base_query(
            filters=[
                {
                    "column": "price",
                    "operator": ">",
                    "value": 10,
                },
                {
                    "column": "stock",
                    "operator": ">=",
                    "value": 1,
                },
            ]
        )
    )

    assert result["parameters"] == [10, 1]
    assert " AND " in result["sql"]


def test_like_filter():
    result = write_sql_query(
        **base_query(
            filters=[
                {
                    "column": "title",
                    "operator": "LIKE",
                    "value": "%Python%",
                }
            ]
        )
    )

    assert result["parameters"] == ["%Python%"]


@pytest.mark.parametrize(
    "operator",
    ["IS NULL", "IS NOT NULL"],
)
def test_null_operators(operator):
    result = write_sql_query(
        **base_query(
            filters=[
                {
                    "column": "price",
                    "operator": operator,
                    "value": None,
                }
            ]
        )
    )

    assert operator in result["sql"]
    assert result["parameters"] == []


def test_order_by():
    result = write_sql_query(
        **base_query(
            order_by=[
                {"column": "price", "direction": "ASC"},
                {"column": "title", "direction": "DESC"},
            ]
        )
    )

    assert result["sql"].endswith(
        'ORDER BY "price" ASC, "title" DESC'
    )


def test_limit():
    result = write_sql_query(**base_query(limit=10))

    assert result["sql"].endswith("LIMIT ?")
    assert result["parameters"] == [10]


def test_complete_query():
    result = write_sql_query(
        **base_query(
            distinct=True,
            filters=[
                {
                    "column": "price",
                    "operator": ">=",
                    "value": 10,
                },
                {
                    "column": "stock",
                    "operator": ">",
                    "value": 0,
                },
            ],
            order_by=[
                {"column": "price", "direction": "DESC"},
            ],
            limit=20,
        )
    )

    assert result["sql"] == (
        'SELECT DISTINCT "title", "price" FROM "books" '
        'WHERE "price" >= ? AND "stock" > ? '
        'ORDER BY "price" DESC LIMIT ?'
    )
    assert result["parameters"] == [10, 0, 20]


@pytest.mark.parametrize(
    "table",
    ["unknown", "", " ", "BOOKS"],
)
def test_invalid_table(table):
    with pytest.raises(ValueError):
        write_sql_query(**base_query(table=table))


@pytest.mark.parametrize(
    "column",
    ["unknown", "", " ", "Title"],
)
def test_invalid_column(column):
    with pytest.raises(ValueError):
        write_sql_query(**base_query(columns=[column]))


@pytest.mark.parametrize(
    "operator",
    ["DROP", "IN", "BETWEEN", "LIKE OR 1=1", ""],
)
def test_invalid_operator(operator):
    with pytest.raises(ValueError):
        write_sql_query(
            **base_query(
                filters=[
                    {
                        "column": "price",
                        "operator": operator,
                        "value": 10,
                    }
                ]
            )
        )


@pytest.mark.parametrize(
    "limit",
    [0, -1, 1001, True, 1.5, "10"],
)
def test_invalid_limit(limit):
    with pytest.raises(ValueError):
        write_sql_query(**base_query(limit=limit))


@pytest.mark.parametrize(
    "limit",
    [1, 1000],
)
def test_limit_boundaries(limit):
    result = write_sql_query(**base_query(limit=limit))

    assert result["parameters"] == [limit]


def test_boolean_is_not_a_numeric_filter():
    with pytest.raises(ValueError):
        write_sql_query(
            **base_query(
                filters=[
                    {
                        "column": "stock",
                        "operator": "=",
                        "value": True,
                    }
                ]
            )
        )


def test_injection_string_is_parameterized():
    malicious = "' OR 1=1 --"

    result = write_sql_query(
        **base_query(
            filters=[
                {
                    "column": "title",
                    "operator": "=",
                    "value": malicious,
                }
            ]
        )
    )

    assert malicious not in result["sql"]
    assert result["parameters"] == [malicious]


def test_invalid_wildcard_combination():
    with pytest.raises(ValueError):
        write_sql_query(**base_query(columns=["*", "title"]))


def test_duplicate_columns():
    with pytest.raises(ValueError):
        write_sql_query(**base_query(columns=["title", "title"]))


def test_invalid_sort_direction():
    with pytest.raises(ValueError):
        write_sql_query(
            **base_query(
                order_by=[
                    {"column": "price", "direction": "SIDEWAYS"}
                ]
            )
        )


def test_null_comparison_rejected():
    with pytest.raises(ValueError):
        write_sql_query(
            **base_query(
                filters=[
                    {
                        "column": "price",
                        "operator": "=",
                        "value": None,
                    }
                ]
            )
        )


def test_like_requires_string():
    with pytest.raises(ValueError):
        write_sql_query(
            **base_query(
                filters=[
                    {
                        "column": "title",
                        "operator": "LIKE",
                        "value": 123,
                    }
                ]
            )
        )


def test_nan_rejected():
    with pytest.raises(ValueError):
        write_sql_query(
            **base_query(
                filters=[
                    {
                        "column": "price",
                        "operator": ">",
                        "value": float("nan"),
                    }
                ]
            )
        )


def test_infinite_value_rejected():
    with pytest.raises(ValueError):
        write_sql_query(
            **base_query(
                filters=[
                    {
                        "column": "price",
                        "operator": ">",
                        "value": float("inf"),
                    }
                ]
            )
        )