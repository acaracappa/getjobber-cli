"""Tests for quote management commands."""

from unittest.mock import MagicMock

import pytest
import typer
from typer.testing import CliRunner

from getjobber_cli.commands import quote_commands

runner = CliRunner()


def _build_app():
    app = typer.Typer()
    app.command(name="list")(quote_commands.list_quotes)
    app.command(name="get")(quote_commands.get_quote)
    app.command(name="create")(quote_commands.create_quote)
    app.command(name="send")(quote_commands.send_quote)
    app.command(name="approve")(quote_commands.approve_quote)
    return app


@pytest.fixture
def app():
    return _build_app()


@pytest.fixture
def fake_client(monkeypatch):
    mock_gql = MagicMock()
    mock_gql.query.return_value = {}
    mock_gql.mutate.return_value = {}
    mock_tm = MagicMock()
    mock_tm.is_authenticated.return_value = True
    mock_tm.get_access_token.return_value = "tok"
    monkeypatch.setattr(quote_commands, "GraphQLClient", lambda *a, **kw: mock_gql)
    monkeypatch.setattr(quote_commands, "get_token_manager", lambda: mock_tm)
    return mock_gql, mock_tm


@pytest.fixture
def unauthenticated(monkeypatch):
    mock_tm = MagicMock()
    mock_tm.is_authenticated.return_value = False
    monkeypatch.setattr(quote_commands, "get_token_manager", lambda: mock_tm)
    return mock_tm


class TestListQuotes:
    def test_happy_path(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {
            "quotes": {
                "nodes": [
                    {
                        "id": "q1",
                        "quoteNumber": "Q1",
                        "title": "T",
                        "status": "draft",
                        "totalAmount": "100",
                    }
                ]
            }
        }
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

    def test_with_status_filter(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"quotes": {"nodes": []}}
        result = runner.invoke(app, ["list", "--status", "draft"])
        assert result.exit_code == 0
        _, kwargs = gql.query.call_args
        assert kwargs["variables"]["status"] == "draft"

    def test_json_format(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"quotes": {"nodes": []}}
        result = runner.invoke(app, ["list", "--format", "json"])
        assert result.exit_code == 0

    def test_unauthenticated(self, app, unauthenticated):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 1


class TestGetQuote:
    def test_happy_path(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"quote": {"id": "1", "title": "T"}}
        result = runner.invoke(app, ["get", "1"])
        assert result.exit_code == 0

    def test_not_found(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"quote": {}}
        result = runner.invoke(app, ["get", "missing"])
        assert result.exit_code == 1


class TestCreateQuote:
    def test_happy_path(self, app, fake_client):
        gql, _ = fake_client
        gql.mutate.return_value = {
            "quoteCreate": {"quote": {"id": "1"}, "userErrors": []}
        }
        result = runner.invoke(
            app, ["create", "--client-id", "c1", "--title", "MyTitle"]
        )
        assert result.exit_code == 0

    def test_user_errors(self, app, fake_client):
        gql, _ = fake_client
        gql.mutate.return_value = {
            "quoteCreate": {
                "quote": None,
                "userErrors": [{"path": "title", "message": "required"}],
            }
        }
        result = runner.invoke(
            app, ["create", "--client-id", "c1", "--title", "x"]
        )
        assert result.exit_code == 1


class TestSendQuote:
    def test_happy_path_force(self, app, fake_client):
        gql, _ = fake_client
        gql.mutate.return_value = {
            "quoteSend": {"quote": {"id": "1"}, "userErrors": []}
        }
        result = runner.invoke(app, ["send", "1", "--force"])
        assert result.exit_code == 0

    def test_cancel_without_force(self, app, fake_client):
        gql, _ = fake_client
        result = runner.invoke(app, ["send", "1"], input="n\n")
        # NOTE: source uses raise typer.Exit(0) inside try/except Exception,
        # which gets re-raised as exit_code=1. This captures actual behavior.
        assert result.exit_code == 1
        gql.mutate.assert_not_called()

    def test_user_errors(self, app, fake_client):
        gql, _ = fake_client
        gql.mutate.return_value = {
            "quoteSend": {"quote": None, "userErrors": [{"path": "id", "message": "bad"}]}
        }
        result = runner.invoke(app, ["send", "1", "--force"])
        assert result.exit_code == 1


class TestApproveQuote:
    def test_happy_path(self, app, fake_client):
        gql, _ = fake_client
        gql.mutate.return_value = {
            "quoteApprove": {"quote": {"id": "1"}, "userErrors": []}
        }
        result = runner.invoke(app, ["approve", "1"])
        assert result.exit_code == 0

    def test_user_errors(self, app, fake_client):
        gql, _ = fake_client
        gql.mutate.return_value = {
            "quoteApprove": {"quote": None, "userErrors": [{"path": "id", "message": "bad"}]}
        }
        result = runner.invoke(app, ["approve", "1"])
        assert result.exit_code == 1
