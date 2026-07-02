"""Invoice management commands for GetJobber CLI."""

from typing import Optional

import typer
from typing_extensions import Annotated

from getjobber_cli.api.client import GraphQLClient
from getjobber_cli.api.mutations import CREATE_INVOICE, SEND_INVOICE
from getjobber_cli.api.queries import GET_INVOICE, LIST_INVOICES
from getjobber_cli.auth.token_manager import get_token_manager
from getjobber_cli.constants import DEFAULT_ITEMS_PER_PAGE, OUTPUT_FORMAT_TABLE
from getjobber_cli.utils.errors import GraphQLError, NotAuthenticatedError
from getjobber_cli.utils.gating import write_command_pending
from getjobber_cli.utils.formatters import (
    extract_list_data,
    extract_single_data,
    format_output,
    format_single_item,
    format_table,
    print_error,
    print_success,
)


def _get_authenticated_client() -> GraphQLClient:
    """Get authenticated GraphQL client."""
    token_manager = get_token_manager()
    if not token_manager.is_authenticated():
        raise NotAuthenticatedError()

    access_token = token_manager.get_access_token()
    return GraphQLClient(access_token)


def list_invoices(
    limit: Annotated[int, typer.Option(help="Number of invoices to retrieve")] = DEFAULT_ITEMS_PER_PAGE,
    status: Annotated[Optional[str], typer.Option(help="Filter by status")] = None,
    unpaid: Annotated[bool, typer.Option(help="Show only unpaid invoices")] = False,
    format: Annotated[str, typer.Option(help="Output format (table, json, csv, yaml)")] = OUTPUT_FORMAT_TABLE,
):
    """List all invoices."""
    try:
        client = _get_authenticated_client()

        variables = {"first": limit}
        # `status` maps to InvoiceStatusTypeEnum (draft, awaiting_payment, paid,
        # past_due, bad_debt, sent_not_due). There is no single "unpaid" status,
        # so --unpaid is applied client-side by outstanding balance.
        if status:
            variables["status"] = status

        result = client.query(LIST_INVOICES, variables=variables)
        invoices = extract_list_data(result, "invoices")

        if unpaid:
            invoices = [i for i in invoices if ((i.get("amounts") or {}).get("invoiceBalance") or 0) > 0]

        if format == OUTPUT_FORMAT_TABLE:
            simplified = [
                {
                    "ID": i.get("id", ""),
                    "Number": i.get("invoiceNumber", ""),
                    "Subject": i.get("subject", ""),
                    "Status": i.get("invoiceStatus", ""),
                    "Total": (i.get("amounts") or {}).get("total", ""),
                    "Balance": (i.get("amounts") or {}).get("invoiceBalance", ""),
                }
                for i in invoices
            ]
            format_table(simplified)
        else:
            output = format_output(invoices, format)
            typer.echo(output)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to list invoices: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def get_invoice(invoice_id: Annotated[str, typer.Argument(help="Invoice ID")]):
    """Get detailed invoice information."""
    try:
        client = _get_authenticated_client()
        result = client.query(GET_INVOICE, variables={"id": invoice_id})
        invoice_data = extract_single_data(result, "invoice")

        if not invoice_data:
            print_error(f"Invoice not found: {invoice_id}")
            raise typer.Exit(1)

        format_single_item(invoice_data)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to get invoice: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@write_command_pending
def create_invoice(
    job_id: Annotated[Optional[str], typer.Option(help="Job ID")] = None,
    client_id: Annotated[Optional[str], typer.Option(help="Client ID")] = None,
    subject: Annotated[Optional[str], typer.Option(help="Invoice subject")] = None,
):
    """Create a new invoice."""
    try:
        if not job_id and not client_id:
            print_error("Either --job-id or --client-id is required")
            raise typer.Exit(1)

        if not subject:
            subject = typer.prompt("Invoice subject")

        invoice_input = {"subject": subject}
        if job_id:
            invoice_input["jobId"] = job_id
        if client_id:
            invoice_input["clientId"] = client_id

        gql_client = _get_authenticated_client()
        result = gql_client.mutate(CREATE_INVOICE, variables={"input": invoice_input})

        if "invoiceCreate" in result:
            user_errors = result["invoiceCreate"].get("userErrors", [])
            if user_errors:
                for error in user_errors:
                    print_error(f"{error.get('path', '')}: {error.get('message', '')}")
                raise typer.Exit(1)

            created_invoice = result["invoiceCreate"].get("invoice")
            if created_invoice:
                print_success(f"Invoice created successfully! ID: {created_invoice.get('id')}")
                format_single_item(created_invoice)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to create invoice: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@write_command_pending
def send_invoice(
    invoice_id: Annotated[str, typer.Argument(help="Invoice ID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """Send an invoice to the client."""
    try:
        if not force:
            confirm = typer.confirm(f"Are you sure you want to send invoice {invoice_id}?")
            if not confirm:
                typer.echo("Send cancelled.")
                raise typer.Exit(0)

        gql_client = _get_authenticated_client()
        result = gql_client.mutate(SEND_INVOICE, variables={"id": invoice_id})

        if "invoiceSend" in result:
            user_errors = result["invoiceSend"].get("userErrors", [])
            if user_errors:
                for error in user_errors:
                    print_error(f"{error.get('path', '')}: {error.get('message', '')}")
                raise typer.Exit(1)

            print_success(f"Invoice {invoice_id} sent successfully!")

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to send invoice: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)
