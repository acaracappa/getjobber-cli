"""Client management commands for GetJobber CLI."""

from typing import Any, Dict, List, Optional

import typer
from typing_extensions import Annotated

from getjobber_cli.api.client import get_authenticated_client
from getjobber_cli.api.mutations import ARCHIVE_CLIENT, CREATE_CLIENT, UPDATE_CLIENT
from getjobber_cli.api.queries import (
    GET_CLIENT,
    GET_CLIENT_CONTACT_METHODS,
    LIST_CLIENTS,
    SEARCH_CLIENTS,
)
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


def _primary_or_first(items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Pick the primary contact method, falling back to the first one."""
    for item in items:
        if item.get("primary"):
            return item
    return items[0] if items else None


def _contact_method_edits(
    gql_client, client_id: str, email: Optional[str], phone: Optional[str]
) -> Dict[str, Any]:
    """Translate --email/--phone into ClientEditInput's differential shape.

    clientEdit cannot set an email; it adds one, or edits an existing one by its
    id. So an update has to read what is there first, or it silently creates
    duplicates instead of changing the address.
    """
    if email is None and phone is None:
        return {}

    current = gql_client.query(GET_CLIENT_CONTACT_METHODS, variables={"id": client_id})
    client = current.get("client") or {}
    edits: Dict[str, Any] = {}

    if email is not None:
        existing = _primary_or_first(client.get("emails") or [])
        if existing:
            edits["emailsToEdit"] = [{"id": existing["id"], "address": email, "primary": True}]
        else:
            edits["emailsToAdd"] = [{"address": email, "primary": True}]

    if phone is not None:
        existing = _primary_or_first(client.get("phones") or [])
        if existing:
            edits["phonesToEdit"] = [{"id": existing["id"], "number": phone, "primary": True}]
        else:
            edits["phonesToAdd"] = [{"number": phone, "primary": True}]

    return edits


def list_clients(
    limit: Annotated[
        int, typer.Option(help="Number of clients to retrieve")
    ] = DEFAULT_ITEMS_PER_PAGE,
    format: Annotated[
        str, typer.Option(help="Output format (table, json, csv, yaml)")
    ] = OUTPUT_FORMAT_TABLE,
):
    """List all clients."""
    try:
        client = get_authenticated_client()

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
                    "Phone": c.get("phone", ""),
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
        client = get_authenticated_client()

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

        # Build input. Emails and phones are lists of objects on
        # ClientCreateInput, not scalars.
        client_input: Dict[str, Any] = {}
        if first_name:
            client_input["firstName"] = first_name
        if last_name:
            client_input["lastName"] = last_name
        if company_name:
            client_input["companyName"] = company_name
        if email:
            client_input["emails"] = [{"address": email, "primary": True}]
        if phone:
            client_input["phones"] = [{"number": phone, "primary": True}]

        # Execute mutation
        gql_client = get_authenticated_client()
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
        client_input: Dict[str, Any] = {}
        if first_name is not None:
            client_input["firstName"] = first_name
        if last_name is not None:
            client_input["lastName"] = last_name
        if company_name is not None:
            client_input["companyName"] = company_name

        if not client_input and email is None and phone is None:
            print_error("No update fields provided")
            raise typer.Exit(1)

        gql_client = get_authenticated_client()
        client_input.update(_contact_method_edits(gql_client, client_id, email, phone))

        result = gql_client.mutate(
            UPDATE_CLIENT, variables={"clientId": client_id, "input": client_input}
        )

        # Check for errors
        if "clientEdit" in result:
            user_errors = result["clientEdit"].get("userErrors", [])
            if user_errors:
                for error in user_errors:
                    print_error(f"{error.get('path', '')}: {error.get('message', '')}")
                raise typer.Exit(1)

            updated_client = result["clientEdit"].get("client")
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


def archive_client(
    client_id: Annotated[str, typer.Argument(help="Client ID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """Archive a client.

    Jobber has no client deletion; archiving is reversible in the Jobber web app.
    """
    try:
        if not force:
            confirm = typer.confirm(f"Archive client {client_id}?")
            if not confirm:
                typer.echo("Archive cancelled.")
                raise typer.Exit(0)

        # Execute mutation
        gql_client = get_authenticated_client()
        result = gql_client.mutate(ARCHIVE_CLIENT, variables={"clientId": client_id})

        # Check for errors
        if "clientArchive" in result:
            user_errors = result["clientArchive"].get("userErrors", [])
            if user_errors:
                for error in user_errors:
                    print_error(f"{error.get('path', '')}: {error.get('message', '')}")
                raise typer.Exit(1)

            print_success(f"Client {client_id} archived.")

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to archive client: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def search_clients(
    query: Annotated[str, typer.Argument(help="Search query")],
    limit: Annotated[int, typer.Option(help="Number of results")] = DEFAULT_ITEMS_PER_PAGE,
    format: Annotated[
        str, typer.Option(help="Output format (table, json, csv, yaml)")
    ] = OUTPUT_FORMAT_TABLE,
):
    """Search for clients."""
    try:
        client = get_authenticated_client()

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
                    "Phone": c.get("phone", ""),
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
