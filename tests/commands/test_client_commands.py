"""Tests for client management commands."""

from unittest.mock import MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner

from getjobber_cli.commands import client_commands
from getjobber_cli.utils.errors import NotAuthenticatedError

runner = CliRunner()


def _build_app():
    """Build a Typer app exposing the client commands."""
    app = typer.Typer()
    app.command(name="list")(client_commands.list_clients)
    app.command(name="get")(client_commands.get_client)
    app.command(name="create")(client_commands.create_client)
    app.command(name="update")(client_commands.update_client)
    app.command(name="archive")(client_commands.archive_client)
    app.command(name="search")(client_commands.search_clients)
    return app


@pytest.fixture
def app():
    return _build_app()


@pytest.fixture
def fake_client(monkeypatch):
    """Patch the shared authenticated-client helper in client_commands."""
    mock_gql = MagicMock()
    mock_gql.query.return_value = {}
    mock_gql.mutate.return_value = {}

    monkeypatch.setattr(client_commands, "get_authenticated_client", lambda: mock_gql)
    return mock_gql


@pytest.fixture
def unauthenticated(monkeypatch):
    def _unauthenticated():
        raise NotAuthenticatedError()

    monkeypatch.setattr(client_commands, "get_authenticated_client", _unauthenticated)


class TestListClients:
    def test_happy_path_table(self, app, fake_client):
        gql = fake_client
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
        gql = fake_client
        gql.query.return_value = {"clients": {"nodes": [{"id": "1"}]}}
        result = runner.invoke(app, ["list", "--format", "json"])
        assert result.exit_code == 0
        assert "1" in result.stdout

    def test_unauthenticated_fails(self, app, unauthenticated):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 1

    def test_graphql_error(self, app, fake_client):
        from getjobber_cli.utils.errors import GraphQLError

        gql = fake_client
        gql.query.side_effect = GraphQLError("boom")
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 1


class TestGetClient:
    def test_happy_path(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {"client": {"id": "1", "firstName": "John", "lastName": "Doe"}}
        result = runner.invoke(app, ["get", "1"])
        assert result.exit_code == 0

    def test_not_found(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {"client": {}}
        result = runner.invoke(app, ["get", "999"])
        assert result.exit_code == 1


class TestSearchClients:
    def test_happy_path(self, app, fake_client):
        gql = fake_client
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
        gql = fake_client
        gql.query.return_value = {"clients": {"nodes": []}}
        result = runner.invoke(app, ["search", "nobody"])
        assert result.exit_code == 0


class TestCreateClient:
    def test_sends_contact_methods_as_lists(self, app, fake_client):
        gql = fake_client
        gql.mutate.return_value = {
            "clientCreate": {"client": {"id": "c1", "firstName": "Ada"}, "userErrors": []}
        }
        result = runner.invoke(
            app, ["create", "--first-name=Ada", "--email=a@example.com", "--phone=555"]
        )
        assert result.exit_code == 0
        sent = gql.mutate.call_args.kwargs["variables"]["input"]
        # ClientCreateInput takes lists of objects, not scalar email/phoneNumber.
        assert sent["emails"] == [{"address": "a@example.com", "primary": True}]
        assert sent["phones"] == [{"number": "555", "primary": True}]
        assert "email" not in sent and "phoneNumber" not in sent

    def test_user_errors_exit_nonzero(self, app, fake_client):
        fake_client.mutate.return_value = {
            "clientCreate": {"client": None, "userErrors": [{"message": "bad", "path": "x"}]}
        }
        result = runner.invoke(app, ["create", "--first-name=Ada"])
        assert result.exit_code == 1

    def test_requires_a_name(self, app, fake_client):
        result = runner.invoke(app, ["create", "--email=a@example.com"], input="\n\n\n\n\n")
        assert result.exit_code == 1


class TestUpdateClient:
    def _edit_ok(self, gql):
        gql.mutate.return_value = {"clientEdit": {"client": {"id": "c1"}, "userErrors": []}}

    def test_edits_existing_email_by_id(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {
            "client": {
                "id": "c1",
                "emails": [{"id": "e1", "address": "old@example.com", "primary": True}],
                "phones": [],
            }
        }
        self._edit_ok(gql)
        result = runner.invoke(app, ["update", "c1", "--email=new@example.com"])
        assert result.exit_code == 0
        sent = gql.mutate.call_args.kwargs["variables"]
        assert sent["clientId"] == "c1"
        # Editing, not adding: otherwise the client ends up with two addresses.
        assert sent["input"]["emailsToEdit"] == [
            {"id": "e1", "address": "new@example.com", "primary": True}
        ]
        assert "emailsToAdd" not in sent["input"]

    def test_adds_email_when_none_exists(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {"client": {"id": "c1", "emails": [], "phones": []}}
        self._edit_ok(gql)
        result = runner.invoke(app, ["update", "c1", "--email=new@example.com"])
        assert result.exit_code == 0
        sent = gql.mutate.call_args.kwargs["variables"]["input"]
        assert sent["emailsToAdd"] == [{"address": "new@example.com", "primary": True}]
        assert "emailsToEdit" not in sent

    def test_name_only_update_skips_the_lookup(self, app, fake_client):
        gql = fake_client
        self._edit_ok(gql)
        result = runner.invoke(app, ["update", "c1", "--first-name=Grace"])
        assert result.exit_code == 0
        gql.query.assert_not_called()
        assert gql.mutate.call_args.kwargs["variables"]["input"] == {"firstName": "Grace"}

    def test_no_fields_exits_nonzero(self, app, fake_client):
        result = runner.invoke(app, ["update", "c1"])
        assert result.exit_code == 1


class TestArchiveClient:
    def test_archives_with_force(self, app, fake_client):
        gql = fake_client
        gql.mutate.return_value = {"clientArchive": {"client": {"id": "c1"}, "userErrors": []}}
        result = runner.invoke(app, ["archive", "c1", "--force"])
        assert result.exit_code == 0
        assert gql.mutate.call_args.kwargs["variables"] == {"clientId": "c1"}

    def test_declining_confirmation_does_not_call_the_api(self, app, fake_client):
        result = runner.invoke(app, ["archive", "c1"], input="n\n")
        assert result.exit_code == 0
        fake_client.mutate.assert_not_called()
