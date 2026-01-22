"""Raw GraphQL query commands for GetJobber CLI."""

from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from getjobber_cli.api.client import GraphQLClient
from getjobber_cli.auth.token_manager import get_token_manager
from getjobber_cli.utils.errors import GraphQLError, NotAuthenticatedError
from getjobber_cli.utils.formatters import format_output, print_error


def _get_authenticated_client() -> GraphQLClient:
    """Get authenticated GraphQL client."""
    token_manager = get_token_manager()
    if not token_manager.is_authenticated():
        raise NotAuthenticatedError()

    access_token = token_manager.get_access_token()
    return GraphQLClient(access_token)


def execute_query(
    query_string: Annotated[Optional[str], typer.Argument(help="GraphQL query string")] = None,
    file: Annotated[Optional[Path], typer.Option(help="Read query from file")] = None,
    interactive: Annotated[bool, typer.Option(help="Open editor for query input")] = False,
):
    """Execute a raw GraphQL query."""
    try:
        # Determine query source
        if interactive:
            # Open editor for interactive query input
            query = typer.edit("\n# Enter your GraphQL query here\n")
            if not query:
                print_error("No query provided")
                raise typer.Exit(1)
            # Remove comment lines
            query = "\n".join([line for line in query.split("\n") if not line.strip().startswith("#")])
        elif file:
            # Read from file
            if not file.exists():
                print_error(f"File not found: {file}")
                raise typer.Exit(1)
            query = file.read_text()
        elif query_string:
            # Use provided query string
            query = query_string
        else:
            print_error("No query provided. Use a query string, --file, or --interactive")
            raise typer.Exit(1)

        # Execute query
        client = _get_authenticated_client()
        result = client.query(query)

        # Output result as JSON
        output = format_output(result, "json")
        typer.echo(output)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Query failed: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)
