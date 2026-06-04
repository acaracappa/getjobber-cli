"""Tests for invoice management commands."""

from unittest.mock import MagicMock

import pytest
import typer
from typer.testing import CliRunner

from getjobber_cli.commands import invoice_commands

runner = CliRunner()


def _build_app():
    app = typer.Typer()
    app.command(name="list")(invoice_commands.list_invoices)
    app.command(name="get")(invoice_commands.get_invoice)
    app.command(name="create")(invoice_commands.create_invoice)
    app.command(name="send")(invoice_commands.send_invoice)
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
    monkeypatch.setattr(invoice_commands, "GraphQLClient", lambda *a, **kw: mock_gql)
    monkeypatch.setattr(invoice_commands, "get_token_manager", lambda: mock_tm)
    return mock_gql, mock_tm


@pytest.fixture
def unauthenticated(monkeypatch):
    mock_tm = MagicMock()
    mock_tm.is_authenticated.return_value = False
    monkeypatch.setattr(invoice_commands, "get_token_manager", lambda: mock_tm)
    return mock_tm


class TestListInvoices:
    def test_happy_path(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {
            "invoices": {
                "nodes": [
                    {
                        "id": "i1",
                        "invoiceNumber": "INV-1",
                        "subject": "S",
                        "status": "unpaid",
                        "totalAmount": "200",
                        "balance": "200",
                    }
                ]
            }
        }
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

    def test_unpaid_flag(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"invoices": {"nodes": []}}
        result = runner.invoke(app, ["list", "--unpaid"])
        assert result.exit_code == 0
        _, kwargs = gql.query.call_args
        assert kwargs["variables"]["status"] == "UNPAID"

    def test_status_filter(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"invoices": {"nodes": []}}
        result = runner.invoke(app, ["list", "--status", "PAID"])
        assert result.exit_code == 0
        _, kwargs = gql.query.call_args
        assert kwargs["variables"]["status"] == "PAID"

    def test_json_format(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"invoices": {"nodes": []}}
        result = runner.invoke(app, ["list", "--format", "json"])
        assert result.exit_code == 0

    def test_unauthenticated(self, app, unauthenticated):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 1


class TestGetInvoice:
    def test_happy_path(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"invoice": {"id": "1"}}
        result = runner.invoke(app, ["get", "1"])
        assert result.exit_code == 0

    def test_not_found(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"invoice": {}}
        result = runner.invoke(app, ["get", "missing"])
        assert result.exit_code == 1


class TestCreateInvoice:
    def test_from_job(self, app, fake_client):
        gql, _ = fake_client
        gql.mutate.return_value = {
            "invoiceCreate": {"invoice": {"id": "1"}, "userErrors": []}
        }
        result = runner.invoke(
            app, ["create", "--job-id", "j1", "--subject", "S"]
        )
        assert result.exit_code == 0
        _, kwargs = gql.mutate.call_args
        assert kwargs["variables"]["input"]["jobId"] == "j1"

    def test_from_client(self, app, fake_client):
        gql, _ = fake_client
        gql.mutate.return_value = {
            "invoiceCreate": {"invoice": {"id": "1"}, "userErrors": []}
        }
        result = runner.invoke(
            app, ["create", "--client-id", "c1", "--subject", "S"]
        )
        assert result.exit_code == 0
        _, kwargs = gql.mutate.call_args
        assert kwargs["variables"]["input"]["clientId"] == "c1"

    def test_missing_both_ids_fails(self, app, fake_client):
        result = runner.invoke(app, ["create", "--subject", "S"])
        assert result.exit_code == 1

    def test_user_errors(self, app, fake_client):
        gql, _ = fake_client
        gql.mutate.return_value = {
            "invoiceCreate": {
                "invoice": None,
                "userErrors": [{"path": "subject", "message": "required"}],
            }
        }
        result = runner.invoke(
            app, ["create", "--job-id", "j1", "--subject", "x"]
        )
        assert result.exit_code == 1


class TestSendInvoice:
    def test_happy_path_force(self, app, fake_client):
        gql, _ = fake_client
        gql.mutate.return_value = {
            "invoiceSend": {"invoice": {"id": "1"}, "userErrors": []}
        }
        result = runner.invoke(app, ["send", "1", "--force"])
        assert result.exit_code == 0

    def test_cancel_without_force(self, app, fake_client):
        gql, _ = fake_client
        result = runner.invoke(app, ["send", "1"], input="n\n")
        assert result.exit_code == 0
        gql.mutate.assert_not_called()

    def test_user_errors(self, app, fake_client):
        gql, _ = fake_client
        gql.mutate.return_value = {
            "invoiceSend": {
                "invoice": None,
                "userErrors": [{"path": "id", "message": "bad"}],
            }
        }
        result = runner.invoke(app, ["send", "1", "--force"])
        assert result.exit_code == 1
