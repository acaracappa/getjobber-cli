"""Client management commands for GetJobber CLI."""

from typing import Optional

import typer
from typing_extensions import Annotated

from getjobber_cli.api.client import GraphQLClient
from getjobber_cli.api.mutations import CREATE_CLIENT, DELETE_CLIENT, UPDATE_CLIENT
from getjobber_cli.api.queries import GET_CLIENT, LIST_CLIENTS, SEARCH_CLIENTS
from getjobber_cli.auth.token_manager import get_token_manager
from getjobber_cli.constants import DEFAULT_ITEMS_PER_PAGE, OUTPUT_FORMAT_TABLE
from getjobber_cli.utils.config import get_config
from getjobber_cli.utils.errors import GraphQLError, NotAuthenticatedError
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
    """Get authenticated GraphQL client.

    Returns:
        GraphQLClient instance.

    Raises:
        NotAuthenticatedError: If not authenticated.
    """
    token_manager = get_token_manager()
    if not token_manager.is_authenticated():
        raise NotAuthenticatedError()

    access_token = token_manager.get_access_token()
    return GraphQLClient(access_token)


def list_clients(
    limit: Annotated[int, typer.Option(help="Number of clients to retrieve")] = DEFAULT_ITEMS_PER_PAGE,
    format: Annotated[str, typer.Option(help="Output format (table, json, csv, yaml)")] = OUTPUT_FORMAT_TABLE,
):
    """List all clients."""
    try:
        client = _get_authenticated_client()

        # Execute query
        result = client.query(LIST_CLIENTS, variables={"first": limit})

        # Extract client list
        clients = extract_list_data(result, "clients")

        if format == OUTPUT_FORMAT_TABLE:
            # Simplified view for table
            simplified = [
                {
                    "ID": c.get("id", ""),
                    "Name": f"{c.get('firstName', '')} {c.get('lastName', '')}".strip()
                    or c.get("companyName", ""),
                    "Email": c.get("email", ""),
                    "Phone": c.get("phoneNumber", ""),
                }
                for c in clients
            ]
            format_table(simplified)
        else:
            output = format_output(clients, format)
            typer.echo(output)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to list clients: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def get_client(
    client_id: Annotated[str, typer.Argument(help="Client ID")],
):
    """Get detailed client information."""
    try:
        client = _get_authenticated_client()

        # Execute query
        result = client.query(GET_CLIENT, variables={"id": client_id})

        # Extract client data
        client_data = extract_single_data(result, "client")

        if not client_data:
            print_error(f"Client not found: {client_id}")
            raise typer.Exit(1)

        # Display detailed view
        format_single_item(client_data)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to get client: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def create_client(
    first_name: Annotated[Optional[str], typer.Option(help="First name")] = None,
    last_name: Annotated[Optional[str], typer.Option(help="Last name")] = None,
    company_name: Annotated[Optional[str], typer.Option(help="Company name")] = None,
    email: Annotated[Optional[str], typer.Option(help="Email address")] = None,
    phone: Annotated[Optional[str], typer.Option(help="Phone number")] = None,
):
    """Create a new client."""
    try:
        # Interactive mode if no options provided
        if not any([first_name, last_name, company_name]):
            typer.echo("Create New Client\n")
            first_name = typer.prompt("First name", default="")
            last_name = typer.prompt("Last name", default="")
            company_name = typer.prompt("Company name (optional)", default="")
            email = typer.prompt("Email (optional)", default="")
            phone = typer.prompt("Phone (optional)", default="")

        # Validate that at least name or company is provided
        if not any([first_name, last_name, company_name]):
            print_error("At least one of first_name, last_name, or company_name is required")
            raise typer.Exit(1)

        # Build input
        client_input = {}
        if first_name:
            client_input["firstName"] = first_name
        if last_name:
            client_input["lastName"] = last_name
        if company_name:
            client_input["companyName"] = company_name
        if email:
            client_input["email"] = email
        if phone:
            client_input["phoneNumber"] = phone

        # Execute mutation
        gql_client = _get_authenticated_client()
        result = gql_client.mutate(CREATE_CLIENT, variables={"input": client_input})

        # Check for errors
        if "clientCreate" in result:
            user_errors = result["clientCreate"].get("userErrors", [])
            if user_errors:
                for error in user_errors:
                    print_error(f"{error.get('path', '')}: {error.get('message', '')}")
                raise typer.Exit(1)

            created_client = result["clientCreate"].get("client")
            if created_client:
                print_success(f"Client created successfully! ID: {created_client.get('id')}")
                format_single_item(created_client)
            else:
                print_error("Failed to create client")
                raise typer.Exit(1)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to create client: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def update_client(
    client_id: Annotated[str, typer.Argument(help="Client ID")],
    first_name: Annotated[Optional[str], typer.Option(help="First name")] = None,
    last_name: Annotated[Optional[str], typer.Option(help="Last name")] = None,
    company_name: Annotated[Optional[str], typer.Option(help="Company name")] = None,
    email: Annotated[Optional[str], typer.Option(help="Email address")] = None,
    phone: Annotated[Optional[str], typer.Option(help="Phone number")] = None,
):
    """Update an existing client."""
    try:
        # Build input
        client_input = {}
        if first_name is not None:
            client_input["firstName"] = first_name
        if last_name is not None:
            client_input["lastName"] = last_name
        if company_name is not None:
            client_input["companyName"] = company_name
        if email is not None:
            client_input["email"] = email
        if phone is not None:
            client_input["phoneNumber"] = phone

        if not client_input:
            print_error("No update fields provided")
            raise typer.Exit(1)

        # Execute mutation
        gql_client = _get_authenticated_client()
        result = gql_client.mutate(UPDATE_CLIENT, variables={"id": client_id, "input": client_input})

        # Check for errors
        if "clientUpdate" in result:
            user_errors = result["clientUpdate"].get("userErrors", [])
            if user_errors:
                for error in user_errors:
                    print_error(f"{error.get('path', '')}: {error.get('message', '')}")
                raise typer.Exit(1)

            updated_client = result["clientUpdate"].get("client")
            if updated_client:
                print_success(f"Client updated successfully!")
                format_single_item(updated_client)
            else:
                print_error("Failed to update client")
                raise typer.Exit(1)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to update client: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def delete_client(
    client_id: Annotated[str, typer.Argument(help="Client ID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """Delete (archive) a client."""
    try:
        # Confirm deletion
        if not force:
            confirm = typer.confirm(f"Are you sure you want to delete client {client_id}?")
            if not confirm:
                typer.echo("Deletion cancelled.")
                raise typer.Exit(0)

        # Execute mutation
        gql_client = _get_authenticated_client()
        result = gql_client.mutate(DELETE_CLIENT, variables={"id": client_id})

        # Check for errors
        if "clientArchive" in result:
            user_errors = result["clientArchive"].get("userErrors", [])
            if user_errors:
                for error in user_errors:
                    print_error(f"{error.get('path', '')}: {error.get('message', '')}")
                raise typer.Exit(1)

            print_success(f"Client {client_id} deleted successfully!")

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to delete client: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def search_clients(
    query: Annotated[str, typer.Argument(help="Search query")],
    limit: Annotated[int, typer.Option(help="Number of results")] = DEFAULT_ITEMS_PER_PAGE,
    format: Annotated[str, typer.Option(help="Output format (table, json, csv, yaml)")] = OUTPUT_FORMAT_TABLE,
):
    """Search for clients."""
    try:
        client = _get_authenticated_client()

        # Execute query
        result = client.query(SEARCH_CLIENTS, variables={"query": query, "first": limit})

        # Extract client list
        clients = extract_list_data(result, "clients")

        if not clients:
            typer.echo(f"No clients found matching '{query}'")
            raise typer.Exit(0)

        if format == OUTPUT_FORMAT_TABLE:
            # Simplified view for table
            simplified = [
                {
                    "ID": c.get("id", ""),
                    "Name": f"{c.get('firstName', '')} {c.get('lastName', '')}".strip()
                    or c.get("companyName", ""),
                    "Email": c.get("email", ""),
                    "Phone": c.get("phoneNumber", ""),
                }
                for c in clients
            ]
            format_table(simplified)
        else:
            output = format_output(clients, format)
            typer.echo(output)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to search clients: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)
