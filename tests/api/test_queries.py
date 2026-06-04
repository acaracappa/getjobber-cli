"""Tests that pre-built GraphQL queries are syntactically valid."""

import pytest
from gql import gql

from getjobber_cli.api import queries


QUERY_CONSTANTS = [
    name
    for name in dir(queries)
    if name.isupper() and isinstance(getattr(queries, name), str)
]


@pytest.mark.parametrize("query_name", QUERY_CONSTANTS)
def test_query_is_valid_graphql(query_name):
    """Each query constant parses cleanly with gql()."""
    query_str = getattr(queries, query_name)
    parsed = gql(query_str)
    assert parsed is not None


def test_at_least_one_query_exists():
    """Sanity check: we found query constants to parameterize over."""
    assert len(QUERY_CONSTANTS) > 0


def test_known_queries_present():
    """Ensure the queries the rest of the codebase imports are defined."""
    expected = [
        "LIST_CLIENTS",
        "GET_CLIENT",
        "SEARCH_CLIENTS",
        "LIST_JOBS",
        "GET_JOB",
        "LIST_QUOTES",
        "GET_QUOTE",
        "LIST_INVOICES",
        "GET_INVOICE",
    ]
    for name in expected:
        assert hasattr(queries, name), f"missing query constant {name}"
