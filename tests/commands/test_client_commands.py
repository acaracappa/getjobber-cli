"""Tests for client management commands."""

from unittest.mock import MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner

from getjobber_cli.commands import client_commands

runner = CliRunner()


def _build_app():
    """Build a Typer app exposing the client commands."""
    app = typer.Typer()
    app.command(name="list")(client_commands.list_clients)
    app.command(name="get")(client_commands.get_client)
    app.command(name="create")(client_commands.create_client)
    app.command(name="update")(client_commands.update_client)
    app.command(name="delete")(client_commands.delete_client)
    app.command(name="search")(client_commands.search_clients)
    return app


@pytest.fixture
def app():
    return _build_app()


@pytest.fixture
def fake_client(monkeypatch):
    """Patch GraphQLClient + token_manager in client_commands."""
    mock_gql = MagicMock()
    mock_gql.query.return_value = {}
    mock_gql.mutate.return_value = {}

    mock_tm = MagicMock()
    mock_tm.is_authenticated.return_value = True
    mock_tm.get_access_token.return_value = "tok"

    monkeypatch.setattr(client_commands, "GraphQLClient", lambda *a, **kw: mock_gql)
    monkeypatch.setattr(client_commands, "get_token_manager", lambda: mock_tm)
    return mock_gql, mock_tm


@pytest.fixture
def unauthenticated(monkeypatch):
    mock_tm = MagicMock()
    mock_tm.is_authenticated.return_value = False
    monkeypatch.setattr(client_commands, "get_token_manager", lambda: mock_tm)
    return mock_tm


class TestListClients:
    def test_happy_path_table(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {
            "clients": {
                "nodes": [
                    {
                        "id": "1",
                        "firstName": "John",
                        "lastName": "Doe",
                        "email": "j@x.com",
                        "phoneNumber": "555",
                    }
                ]
            }
        }
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

    def test_json_format(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"clients": {"nodes": [{"id": "1"}]}}
        result = runner.invoke(app, ["list", "--format", "json"])
        assert result.exit_code == 0
        assert "1" in result.stdout

    def test_unauthenticated_fails(self, app, unauthenticated):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 1

    def test_graphql_error(self, app, fake_client):
        from getjobber_cli.utils.errors import GraphQLError

        gql, _ = fake_client
        gql.query.side_effect = GraphQLError("boom")
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 1


class TestGetClient:
    def test_happy_path(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {
            "client": {"id": "1", "firstName": "John", "lastName": "Doe"}
        }
        result = runner.invoke(app, ["get", "1"])
        assert result.exit_code == 0

    def test_not_found(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"client": {}}
        result = runner.invoke(app, ["get", "999"])
        assert result.exit_code == 1


class TestSearchClients:
    def test_happy_path(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {
            "clients": {
                "nodes": [
                    {
                        "id": "1",
                        "firstName": "John",
                        "lastName": "Doe",
                        "email": "j@x.com",
                        "phoneNumber": "555",
                    }
                ]
            }
        }
        result = runner.invoke(app, ["search", "John"])
        assert result.exit_code == 0

    def test_no_results_exits(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"clients": {"nodes": []}}
        result = runner.invoke(app, ["search", "nobody"])
        assert result.exit_code == 0


class TestWriteCommandsGated:
    """Write commands are gated pending the v1.2.0 write redesign."""

    @pytest.mark.parametrize("fn_name", ['create_client', 'update_client', 'delete_client'])
    def test_gated(self, fn_name):
        fn = getattr(client_commands, fn_name)
        with pytest.raises(typer.Exit) as exc:
            fn()
        assert exc.value.exit_code == 2
