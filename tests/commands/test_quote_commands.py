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


class TestCreateQuote:
    def _created(self, gql):
        gql.mutate.return_value = {"quoteCreate": {"quote": {"id": "q1"}, "userErrors": []}}

    def test_sends_required_attributes(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {"client": {"id": "c1", "properties": [{"id": "p1"}]}}
        self._created(gql)

        result = runner.invoke(
            app, ["create", "--client-id=c1", "--title=T", "--line-item=Trim:2:150"]
        )

        assert result.exit_code == 0
        sent = gql.mutate.call_args.kwargs["variables"]["attributes"]
        assert sent["clientId"] == "c1"
        assert sent["propertyId"] == "p1"
        assert sent["lineItems"] == [
            {
                "name": "Trim",
                "quantity": 2.0,
                "unitPrice": 150.0,
                "saveToProductsAndServices": False,
            }
        ]

    def test_line_items_are_required(self, app, fake_client):
        result = runner.invoke(app, ["create", "--client-id=c1", "--title=T"])
        assert result.exit_code == 1
        fake_client.mutate.assert_not_called()

    def test_bad_line_item_is_rejected(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {"client": {"id": "c1", "properties": [{"id": "p1"}]}}
        result = runner.invoke(
            app, ["create", "--client-id=c1", "--title=T", "--line-item=Trim:lots"]
        )
        assert result.exit_code == 1
        gql.mutate.assert_not_called()


class TestRemovedCommands:
    """quotes send/approve were removed: Jobber exposes no mutation for either.

    Searching the schema for send/approve/deliver/email/message/submit returns
    nothing, so these cannot be rebuilt. See docs/write-redesign.md.
    """

    @pytest.mark.parametrize("fn_name", ["send_quote", "approve_quote"])
    def test_command_is_gone(self, fn_name):
        assert not hasattr(quote_commands, fn_name)

    @pytest.mark.parametrize("const", ["SEND_QUOTE", "APPROVE_QUOTE"])
    def test_mutation_is_gone(self, const):
        from getjobber_cli.api import mutations

        assert not hasattr(mutations, const)

    def test_not_registered_on_the_cli(self):
        from typer.main import get_command

        from getjobber_cli.cli import app

        quotes = get_command(app).commands["quotes"].commands
        assert "send" not in quotes and "approve" not in quotes
