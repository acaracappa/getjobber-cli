"""Quote management commands for GetJobber CLI."""

from typing import Optional

import typer
from typing_extensions import Annotated

from getjobber_cli.api.client import GraphQLClient
from getjobber_cli.api.mutations import APPROVE_QUOTE, CREATE_QUOTE, SEND_QUOTE
from getjobber_cli.api.queries import GET_QUOTE, LIST_QUOTES
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


def list_quotes(
    limit: Annotated[int, typer.Option(help="Number of quotes to retrieve")] = DEFAULT_ITEMS_PER_PAGE,
    status: Annotated[Optional[str], typer.Option(help="Filter by status")] = None,
    format: Annotated[str, typer.Option(help="Output format (table, json, csv, yaml)")] = OUTPUT_FORMAT_TABLE,
):
    """List all quotes."""
    try:
        client = _get_authenticated_client()

        variables = {"first": limit}
        if status:
            variables["status"] = status

        result = client.query(LIST_QUOTES, variables=variables)
        quotes = extract_list_data(result, "quotes")

        if format == OUTPUT_FORMAT_TABLE:
            simplified = [
                {
                    "ID": q.get("id", ""),
                    "Number": q.get("quoteNumber", ""),
                    "Title": q.get("title", ""),
                    "Status": q.get("quoteStatus", ""),
                    "Amount": (q.get("amounts") or {}).get("total", ""),
                }
                for q in quotes
            ]
            format_table(simplified)
        else:
            output = format_output(quotes, format)
            typer.echo(output)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to list quotes: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def get_quote(quote_id: Annotated[str, typer.Argument(help="Quote ID")]):
    """Get detailed quote information."""
    try:
        client = _get_authenticated_client()
        result = client.query(GET_QUOTE, variables={"id": quote_id})
        quote_data = extract_single_data(result, "quote")

        if not quote_data:
            print_error(f"Quote not found: {quote_id}")
            raise typer.Exit(1)

        format_single_item(quote_data)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to get quote: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@write_command_pending
def create_quote(
    client_id: Annotated[str, typer.Option(help="Client ID (required)")],
    title: Annotated[Optional[str], typer.Option(help="Quote title")] = None,
):
    """Create a new quote."""
    try:
        if not title:
            title = typer.prompt("Quote title")

        quote_input = {"clientId": client_id, "title": title}

        gql_client = _get_authenticated_client()
        result = gql_client.mutate(CREATE_QUOTE, variables={"input": quote_input})

        if "quoteCreate" in result:
            user_errors = result["quoteCreate"].get("userErrors", [])
            if user_errors:
                for error in user_errors:
                    print_error(f"{error.get('path', '')}: {error.get('message', '')}")
                raise typer.Exit(1)

            created_quote = result["quoteCreate"].get("quote")
            if created_quote:
                print_success(f"Quote created successfully! ID: {created_quote.get('id')}")
                format_single_item(created_quote)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to create quote: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@write_command_pending
def send_quote(
    quote_id: Annotated[str, typer.Argument(help="Quote ID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """Send a quote to the client."""
    try:
        if not force:
            confirm = typer.confirm(f"Are you sure you want to send quote {quote_id}?")
            if not confirm:
                typer.echo("Send cancelled.")
                raise typer.Exit(0)

        gql_client = _get_authenticated_client()
        result = gql_client.mutate(SEND_QUOTE, variables={"id": quote_id})

        if "quoteSend" in result:
            user_errors = result["quoteSend"].get("userErrors", [])
            if user_errors:
                for error in user_errors:
                    print_error(f"{error.get('path', '')}: {error.get('message', '')}")
                raise typer.Exit(1)

            print_success(f"Quote {quote_id} sent successfully!")

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to send quote: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@write_command_pending
def approve_quote(
    quote_id: Annotated[str, typer.Argument(help="Quote ID")],
):
    """Approve a quote."""
    try:
        gql_client = _get_authenticated_client()
        result = gql_client.mutate(APPROVE_QUOTE, variables={"id": quote_id})

        if "quoteApprove" in result:
            user_errors = result["quoteApprove"].get("userErrors", [])
            if user_errors:
                for error in user_errors:
                    print_error(f"{error.get('path', '')}: {error.get('message', '')}")
                raise typer.Exit(1)

            print_success(f"Quote {quote_id} approved successfully!")

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to approve quote: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)
