"""Tests for quote management commands."""

from unittest.mock import MagicMock

import pytest
import typer
from typer.testing import CliRunner

from getjobber_cli.commands import quote_commands
from getjobber_cli.utils.errors import NotAuthenticatedError

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
    monkeypatch.setattr(quote_commands, "get_authenticated_client", lambda: mock_gql)
    return mock_gql


@pytest.fixture
def unauthenticated(monkeypatch):
    def _unauthenticated():
        raise NotAuthenticatedError()

    monkeypatch.setattr(quote_commands, "get_authenticated_client", _unauthenticated)


class TestListQuotes:
    def test_happy_path(self, app, fake_client):
        gql = fake_client
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
        gql = fake_client
        gql.query.return_value = {"quotes": {"nodes": []}}
        result = runner.invoke(app, ["list", "--status", "draft"])
        assert result.exit_code == 0
        _, kwargs = gql.query.call_args
        assert kwargs["variables"]["status"] == "draft"

    def test_json_format(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {"quotes": {"nodes": []}}
        result = runner.invoke(app, ["list", "--format", "json"])
        assert result.exit_code == 0

    def test_unauthenticated(self, app, unauthenticated):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 1


class TestGetQuote:
    def test_happy_path(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {"quote": {"id": "1", "title": "T"}}
        result = runner.invoke(app, ["get", "1"])
        assert result.exit_code == 0

    def test_not_found(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {"quote": {}}
        result = runner.invoke(app, ["get", "missing"])
        assert result.exit_code == 1


class TestWriteCommandsGated:
    """Write commands are gated pending the v1.2.0 write redesign."""

    @pytest.mark.parametrize("fn_name", ["create_quote", "send_quote", "approve_quote"])
    def test_gated(self, fn_name):
        fn = getattr(quote_commands, fn_name)
        with pytest.raises(typer.Exit) as exc:
            fn()
        assert exc.value.exit_code == 2
