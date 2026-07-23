"""Tests for GraphQL client wrapper."""

from unittest.mock import MagicMock, patch

import pytest

from getjobber_cli.api.client import (
    GraphQLClient,
    create_client,
    execute_mutation,
    execute_query,
)
from getjobber_cli.utils.errors import (
    GraphQLError,
    NotAuthenticatedError,
    RateLimitError,
)


class TestCreateClient:
    def test_with_valid_token(self):
        c = create_client("at")
        assert c is not None

    def test_missing_token_raises(self):
        with pytest.raises(NotAuthenticatedError):
            create_client("")

    def test_transport_has_auth_header(self):
        c = create_client("my_token")
        # The transport should carry the Authorization header
        headers = c.transport.headers
        assert headers["Authorization"] == "Bearer my_token"
        assert headers["X-JOBBER-GRAPHQL-VERSION"] == "2025-04-16"
        assert headers["Content-Type"] == "application/json"


class TestExecuteQuery:
    def test_calls_client_execute(self):
        client = MagicMock()
        client.execute.return_value = {"clients": {"nodes": []}}
        result = execute_query(client, "query { clients { nodes { id } } }")
        assert result == {"clients": {"nodes": []}}
        client.execute.assert_called_once()

    def test_passes_variables(self):
        client = MagicMock()
        client.execute.return_value = {"client": {"id": "1"}}
        execute_query(
            client,
            "query Q($id: ID!) { client(id: $id) { id } }",
            variables={"id": "1"},
        )
        _, kwargs = client.execute.call_args
        assert kwargs["variable_values"] == {"id": "1"}

    def test_401_raises_not_authenticated(self):
        client = MagicMock()
        client.execute.side_effect = Exception("Got 401 Unauthorized")
        with pytest.raises(NotAuthenticatedError):
            execute_query(client, "query { __typename }")

    def test_429_raises_rate_limit(self):
        client = MagicMock()
        client.execute.side_effect = Exception("rate limit exceeded 429")
        with pytest.raises(RateLimitError):
            execute_query(client, "query { __typename }")

    def test_throttled_graphql_error_raises_rate_limit(self):
        client = MagicMock()
        exc = Exception("query had problems")
        exc.errors = [
            {
                "message": "Throttled",
                "extensions": {
                    "code": "THROTTLED",
                    "documentation": "https://developer.getjobber.com/docs/using_jobbers_api/api_rate_limits",
                },
            }
        ]
        client.execute.side_effect = exc
        with pytest.raises(RateLimitError):
            execute_query(client, "query { __typename }")

    def test_structured_errors_raise_graphql_error(self):
        client = MagicMock()
        exc = Exception("query had problems")
        exc.errors = [{"message": "x"}, {"message": "y"}]
        client.execute.side_effect = exc
        with pytest.raises(GraphQLError) as info:
            execute_query(client, "query { __typename }")
        assert info.value.errors == [{"message": "x"}, {"message": "y"}]

    def test_generic_error_raises_graphql_error(self):
        client = MagicMock()
        client.execute.side_effect = Exception("Some other failure")
        with pytest.raises(GraphQLError):
            execute_query(client, "query { __typename }")


class TestExecuteMutation:
    def test_delegates_to_execute_query(self):
        client = MagicMock()
        client.execute.return_value = {"clientCreate": {"client": {"id": "1"}}}
        result = execute_mutation(
            client, "mutation { clientCreate(input: {}) { client { id } } }"
        )
        assert result == {"clientCreate": {"client": {"id": "1"}}}


class TestGraphQLClientWrapper:
    def test_query_delegates(self):
        with patch("getjobber_cli.api.client.create_client") as mock_create:
            inner = MagicMock()
            inner.execute.return_value = {"ok": True}
            mock_create.return_value = inner

            client = GraphQLClient("at")
            assert client.query("query { __typename }") == {"ok": True}

    def test_mutate_delegates(self):
        with patch("getjobber_cli.api.client.create_client") as mock_create:
            inner = MagicMock()
            inner.execute.return_value = {"clientCreate": {"client": {"id": "1"}}}
            mock_create.return_value = inner

            client = GraphQLClient("at")
            result = client.mutate("mutation { clientCreate(input: {}) { client { id } } }")
            assert result == {"clientCreate": {"client": {"id": "1"}}}

    def test_initializes_with_token(self):
        with patch("getjobber_cli.api.client.create_client") as mock_create:
            mock_create.return_value = MagicMock()
            GraphQLClient("at")
            mock_create.assert_called_once_with("at")
