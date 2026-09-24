"""Invoice management commands for GetJobber CLI."""

from enum import Enum

from typing import Any, Dict, List, Optional

import typer
from typing_extensions import Annotated

from getjobber_cli.api.client import get_authenticated_client
from getjobber_cli.api.mutations import CREATE_INVOICE, MARK_INVOICE_SENT
from getjobber_cli.api.queries import GET_INVOICE, LIST_INVOICES
from getjobber_cli.constants import DEFAULT_ITEMS_PER_PAGE, OUTPUT_FORMAT_TABLE
from getjobber_cli.utils.errors import GraphQLError, NotAuthenticatedError
from getjobber_cli.utils.resolvers import parse_line_items
from getjobber_cli.utils.formatters import (
    extract_list_data,
    extract_single_data,
    format_output,
    format_single_item,
    format_table,
    print_error,
    print_success,
)


class TaxMethod(str, Enum):
    """TaxCalculationMethodType. Whether prices already include tax."""

    EXCLUSIVE = "EXCLUSIVE"
    INCLUSIVE = "INCLUSIVE"


def list_invoices(
    limit: Annotated[
        int, typer.Option(help="Number of invoices to retrieve")
    ] = DEFAULT_ITEMS_PER_PAGE,
    status: Annotated[Optional[str], typer.Option(help="Filter by status")] = None,
    unpaid: Annotated[bool, typer.Option(help="Show only unpaid invoices")] = False,
    format: Annotated[
        str, typer.Option(help="Output format (table, json, csv, yaml)")
    ] = OUTPUT_FORMAT_TABLE,
):
    """List all invoices."""
    try:
        client = get_authenticated_client()

        variables: Dict[str, Any] = {"first": limit}
        # `status` maps to InvoiceStatusTypeEnum (draft, awaiting_payment, paid,
        # past_due, bad_debt, sent_not_due). There is no single "unpaid" status,
        # so --unpaid is applied client-side by outstanding balance.
        if status:
            variables["status"] = status

        result = client.query(LIST_INVOICES, variables=variables)
        invoices = extract_list_data(result, "invoices")

        if unpaid:
            invoices = [
                i for i in invoices if ((i.get("amounts") or {}).get("invoiceBalance") or 0) > 0
            ]

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
        client = get_authenticated_client()
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


def create_invoice(
    client_id: Annotated[str, typer.Option(help="Client ID (required)")],
    line_item: Annotated[
        List[str],
        typer.Option(help="Line item as name[:quantity[:unit_price]]; repeat for more (required)"),
    ] = [],
    job_id: Annotated[Optional[str], typer.Option(help="Job this invoice is for")] = None,
    subject: Annotated[Optional[str], typer.Option(help="Invoice subject")] = None,
    due_date: Annotated[Optional[str], typer.Option(help="Due date, YYYY-MM-DD")] = None,
    net_days: Annotated[
        Optional[int], typer.Option(help="Payment terms in days, e.g. 30 for net 30")
    ] = None,
    tax_method: Annotated[
        TaxMethod, typer.Option(help="Whether line item prices already include tax")
    ] = TaxMethod.EXCLUSIVE,
):
    """Create a new invoice."""
    try:
        if not line_item:
            print_error("At least one --line-item is required, as name[:quantity[:unit_price]].")
            raise typer.Exit(1)

        if not subject:
            subject = typer.prompt("Invoice subject")

        due_details: Dict[str, Any] = {}
        if due_date:
            due_details["dueDate"] = due_date
        if net_days is not None:
            due_details["invoiceNet"] = net_days

        # InvoiceCreateInput requires clientId, dueDetails, tax and line items.
        invoice_input: Dict[str, Any] = {
            "clientId": client_id,
            "dueDetails": due_details,
            "tax": {"taxCalculationMethod": tax_method.value},
            "lineItems": parse_line_items(line_item),
        }
        if subject:
            invoice_input["subject"] = subject
        if job_id:
            invoice_input["jobId"] = job_id

        gql_client = get_authenticated_client()
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


def mark_invoice_sent(
    invoice_id: Annotated[str, typer.Argument(help="Invoice ID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """Mark an invoice as sent.

    This flags the record only. Jobber removed invoiceSend, and nothing in the
    current API emails an invoice to a client — send it from the Jobber web app.
    """
    try:
        if not force:
            typer.echo("This marks the invoice as sent. It does not email the client.")
            if not typer.confirm(f"Mark invoice {invoice_id} as sent?"):
                typer.echo("Cancelled.")
                raise typer.Exit(0)

        gql_client = get_authenticated_client()
        result = gql_client.mutate(MARK_INVOICE_SENT, variables={"id": invoice_id})

        if "invoiceMarkAsSent" in result:
            user_errors = result["invoiceMarkAsSent"].get("userErrors", [])
            if user_errors:
                for error in user_errors:
                    print_error(f"{error.get('path', '')}: {error.get('message', '')}")
                raise typer.Exit(1)

            print_success(f"Invoice {invoice_id} marked as sent.")

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to mark invoice as sent: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)
