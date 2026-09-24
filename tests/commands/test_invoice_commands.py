"""Tests for invoice management commands."""

from unittest.mock import MagicMock

import pytest
import typer
from typer.testing import CliRunner

from getjobber_cli.commands import invoice_commands
from getjobber_cli.utils.errors import NotAuthenticatedError

runner = CliRunner()


def _build_app():
    app = typer.Typer()
    app.command(name="list")(invoice_commands.list_invoices)
    app.command(name="get")(invoice_commands.get_invoice)
    app.command(name="create")(invoice_commands.create_invoice)
    app.command(name="mark-sent")(invoice_commands.mark_invoice_sent)
    return app


@pytest.fixture
def app():
    return _build_app()


@pytest.fixture
def fake_client(monkeypatch):
    mock_gql = MagicMock()
    mock_gql.query.return_value = {}
    mock_gql.mutate.return_value = {}
    monkeypatch.setattr(invoice_commands, "get_authenticated_client", lambda: mock_gql)
    return mock_gql


@pytest.fixture
def unauthenticated(monkeypatch):
    def _unauthenticated():
        raise NotAuthenticatedError()

    monkeypatch.setattr(invoice_commands, "get_authenticated_client", _unauthenticated)


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
        gql = fake_client
        gql.query.return_value = {"invoices": {"nodes": [_invoice(1, 200.0)]}}
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

    def test_unpaid_flag_filters_client_side(self, app, fake_client):
        # --unpaid no longer sends a server status filter; it filters by balance.
        gql = fake_client
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
        gql = fake_client
        gql.query.return_value = {"invoices": {"nodes": []}}
        result = runner.invoke(app, ["list", "--status", "paid"])
        assert result.exit_code == 0
        _, kwargs = gql.query.call_args
        assert kwargs["variables"]["status"] == "paid"

    def test_json_format(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {"invoices": {"nodes": []}}
        result = runner.invoke(app, ["list", "--format", "json"])
        assert result.exit_code == 0

    def test_unauthenticated(self, app, unauthenticated):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 1


class TestGetInvoice:
    def test_happy_path(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {"invoice": {"id": "1"}}
        result = runner.invoke(app, ["get", "1"])
        assert result.exit_code == 0

    def test_not_found(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {"invoice": {}}
        result = runner.invoke(app, ["get", "missing"])
        assert result.exit_code == 1


class TestCreateInvoice:
    def _created(self, gql):
        gql.mutate.return_value = {"invoiceCreate": {"invoice": {"id": "i1"}, "userErrors": []}}

    def test_sends_required_input(self, app, fake_client):
        gql = fake_client
        self._created(gql)

        result = runner.invoke(
            app,
            [
                "create",
                "--client-id=c1",
                "--subject=S",
                "--line-item=Cleanup:1:200",
                "--net-days=30",
            ],
        )

        assert result.exit_code == 0
        sent = gql.mutate.call_args.kwargs["variables"]["input"]
        assert sent["clientId"] == "c1"
        assert sent["dueDetails"] == {"invoiceNet": 30}
        assert sent["tax"] == {"taxCalculationMethod": "EXCLUSIVE"}
        assert sent["lineItems"] == [{"name": "Cleanup", "quantity": 1.0, "unitPrice": 200.0}]

    def test_tax_method_is_selectable(self, app, fake_client):
        gql = fake_client
        self._created(gql)
        result = runner.invoke(
            app,
            ["create", "--client-id=c1", "--subject=S", "--line-item=X", "--tax-method=INCLUSIVE"],
        )
        assert result.exit_code == 0
        assert gql.mutate.call_args.kwargs["variables"]["input"]["tax"] == {
            "taxCalculationMethod": "INCLUSIVE"
        }

    def test_line_items_are_required(self, app, fake_client):
        result = runner.invoke(app, ["create", "--client-id=c1", "--subject=S"])
        assert result.exit_code == 1
        fake_client.mutate.assert_not_called()


class TestMarkInvoiceSent:
    def test_marks_with_force(self, app, fake_client):
        gql = fake_client
        gql.mutate.return_value = {"invoiceMarkAsSent": {"invoice": {"id": "i1"}, "userErrors": []}}
        result = runner.invoke(app, ["mark-sent", "i1", "--force"])
        assert result.exit_code == 0
        assert gql.mutate.call_args.kwargs["variables"] == {"id": "i1"}

    def test_warns_that_nothing_is_emailed(self, app, fake_client):
        result = runner.invoke(app, ["mark-sent", "i1"], input="n\n")
        assert result.exit_code == 0
        assert "does not email" in result.output
        fake_client.mutate.assert_not_called()


class TestCancelledConfirmationExitsZero:
    """A declined prompt is not a failure.

    Every handler used to catch its own typer.Exit, so answering "n" exited 1
    and printed "Unexpected error: 0".
    """

    def test_mark_sent_declined(self, app, fake_client):
        result = runner.invoke(app, ["mark-sent", "i1"], input="n\n")
        assert result.exit_code == 0
        assert "Unexpected error" not in result.output
