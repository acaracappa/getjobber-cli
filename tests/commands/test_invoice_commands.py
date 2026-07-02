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


def _invoice(num, balance, status="awaiting_payment"):
    return {
        "id": f"i{num}",
        "invoiceNumber": f"INV-{num}",
        "subject": "S",
        "invoiceStatus": status,
        "amounts": {"total": 200.0, "paymentsTotal": 200.0 - balance, "invoiceBalance": balance},
    }


class TestListInvoices:
    def test_happy_path(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"invoices": {"nodes": [_invoice(1, 200.0)]}}
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

    def test_unpaid_flag_filters_client_side(self, app, fake_client):
        # --unpaid no longer sends a server status filter; it filters by balance.
        gql, _ = fake_client
        gql.query.return_value = {
            "invoices": {"nodes": [_invoice(1, 0.0, "paid"), _invoice(2, 200.0)]}
        }
        result = runner.invoke(app, ["list", "--unpaid", "--format", "json"])
        assert result.exit_code == 0
        _, kwargs = gql.query.call_args
        # no bogus "UNPAID" status variable is passed to the API
        assert kwargs["variables"].get("status") != "UNPAID"
        # paid invoice (balance 0) filtered out, unpaid kept
        assert "INV-2" in result.output
        assert "INV-1" not in result.output

    def test_status_filter(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"invoices": {"nodes": []}}
        result = runner.invoke(app, ["list", "--status", "paid"])
        assert result.exit_code == 0
        _, kwargs = gql.query.call_args
        assert kwargs["variables"]["status"] == "paid"

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


class TestWriteCommandsGated:
    """Write commands are gated pending the v1.2.0 write redesign."""

    @pytest.mark.parametrize(
        "argv",
        [
            ["create", "--job-id", "j1", "--subject", "S"],
            ["create", "--client-id", "c1", "--subject", "S"],
            ["send", "1", "--force"],
        ],
    )
    def test_gated(self, app, fake_client, argv):
        gql, _ = fake_client
        result = runner.invoke(app, argv)
        assert result.exit_code == 2
        assert "temporarily disabled" in result.output
        # gating short-circuits before any network call
        gql.mutate.assert_not_called()
