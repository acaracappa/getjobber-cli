"""Tests that pre-built GraphQL mutations are syntactically valid."""

import pytest
from gql import gql

from getjobber_cli.api import mutations


MUTATION_CONSTANTS = [
    name
    for name in dir(mutations)
    if name.isupper() and isinstance(getattr(mutations, name), str)
]


@pytest.mark.parametrize("mutation_name", MUTATION_CONSTANTS)
def test_mutation_is_valid_graphql(mutation_name):
    """Each mutation constant parses cleanly with gql()."""
    mutation_str = getattr(mutations, mutation_name)
    parsed = gql(mutation_str)
    assert parsed is not None


def test_at_least_one_mutation_exists():
    assert len(MUTATION_CONSTANTS) > 0


def test_known_mutations_present():
    """Ensure mutations used elsewhere in the codebase are defined."""
    expected = [
        "CREATE_CLIENT",
        "UPDATE_CLIENT",
        "DELETE_CLIENT",
        "CREATE_JOB",
        "UPDATE_JOB",
        "COMPLETE_JOB",
        "CREATE_QUOTE",
        "UPDATE_QUOTE",
        "SEND_QUOTE",
        "APPROVE_QUOTE",
        "CREATE_INVOICE",
        "UPDATE_INVOICE",
        "SEND_INVOICE",
    ]
    for name in expected:
        assert hasattr(mutations, name), f"missing mutation constant {name}"
