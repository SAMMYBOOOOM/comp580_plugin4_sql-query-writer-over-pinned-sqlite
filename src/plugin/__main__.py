from mcp.server.fastmcp import FastMCP

from .write_sql_query import write_sql_query


mcp = FastMCP("sqlite-query-writer")

IMPLEMENTATIONS = {
    "write_sql_query": write_sql_query,
}

for implementation in IMPLEMENTATIONS.values():
    mcp.tool()(implementation)


if __name__ == "__main__":
    mcp.run(transport="stdio")