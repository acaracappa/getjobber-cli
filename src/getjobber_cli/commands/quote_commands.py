"""Quote management commands for GetJobber CLI."""

from typing import Any, Dict, List, Optional

import typer
from typing_extensions import Annotated

from getjobber_cli.api.client import get_authenticated_client
from getjobber_cli.api.mutations import CREATE_QUOTE
from getjobber_cli.api.queries import GET_QUOTE, LIST_QUOTES
from getjobber_cli.constants import DEFAULT_ITEMS_PER_PAGE, OUTPUT_FORMAT_TABLE
from getjobber_cli.utils.errors import GraphQLError, NotAuthenticatedError
from getjobber_cli.utils.resolvers import parse_line_items, resolve_property_id
from getjobber_cli.utils.formatters import (
    extract_list_data,
    extract_single_data,
    format_output,
    format_single_item,
    format_table,
    print_error,
    print_success,
)


def list_quotes(
    limit: Annotated[
        int, typer.Option(help="Number of quotes to retrieve")
    ] = DEFAULT_ITEMS_PER_PAGE,
    status: Annotated[Optional[str], typer.Option(help="Filter by status")] = None,
    format: Annotated[
        str, typer.Option(help="Output format (table, json, csv, yaml)")
    ] = OUTPUT_FORMAT_TABLE,
):
    """List all quotes."""
    try:
        client = get_authenticated_client()

        variables: Dict[str, Any] = {"first": limit}
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
        client = get_authenticated_client()
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


def create_quote(
    client_id: Annotated[str, typer.Option(help="Client ID (required)")],
    line_item: Annotated[
        List[str],
        typer.Option(help="Line item as name[:quantity[:unit_price]]; repeat for more (required)"),
    ] = [],
    property_id: Annotated[
        Optional[str],
        typer.Option(help="Property ID; resolved from the client when it has only one"),
    ] = None,
    title: Annotated[Optional[str], typer.Option(help="Quote title")] = None,
    save_to_products: Annotated[
        bool,
        typer.Option(help="Also save these line items to Products & Services"),
    ] = False,
):
    """Create a new quote."""
    try:
        if not line_item:
            print_error("At least one --line-item is required, as name[:quantity[:unit_price]].")
            raise typer.Exit(1)

        if not title:
            title = typer.prompt("Quote title")

        gql_client = get_authenticated_client()

        if property_id is None:
            property_id = resolve_property_id(gql_client, client_id)

        # QuoteCreateAttributes requires clientId, propertyId and line items;
        # each line item requires saveToProductsAndServices.
        quote_input: Dict[str, Any] = {
            "clientId": client_id,
            "propertyId": property_id,
            "lineItems": parse_line_items(
                line_item, extra={"saveToProductsAndServices": save_to_products}
            ),
        }
        if title:
            quote_input["title"] = title

        result = gql_client.mutate(CREATE_QUOTE, variables={"attributes": quote_input})

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
