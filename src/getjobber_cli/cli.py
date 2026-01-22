"""Main CLI application for GetJobber CLI."""

import typer
from typing_extensions import Annotated

from getjobber_cli.constants import APP_DESCRIPTION, APP_NAME, APP_VERSION

# Create main app
app = typer.Typer(
    name=APP_NAME,
    help=APP_DESCRIPTION,
    no_args_is_help=True,
    add_completion=False,
)


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        typer.echo(f"{APP_NAME} version {APP_VERSION}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", "-v", callback=version_callback, is_eager=True, help="Show version"),
    ] = False,
):
    """GetJobber CLI - Terminal access to GetJobber CRM API."""
    pass


# Import and register command modules
# These will be imported after they are created
def register_commands():
    """Register all command modules."""
    try:
        from getjobber_cli.commands import auth_commands
        from getjobber_cli.commands import client_commands
        from getjobber_cli.commands import config_commands
        from getjobber_cli.commands import invoice_commands
        from getjobber_cli.commands import job_commands
        from getjobber_cli.commands import query_commands
        from getjobber_cli.commands import quote_commands

        # Register auth commands (login, logout)
        app.command(name="login")(auth_commands.login)
        app.command(name="logout")(auth_commands.logout)

        # Register auth subcommands
        auth_app = typer.Typer(name="auth", help="Authentication commands")
        auth_app.command(name="status")(auth_commands.status)
        auth_app.command(name="refresh")(auth_commands.refresh)
        app.add_typer(auth_app)

        # Register config commands
        config_app = typer.Typer(name="config", help="Configuration commands")
        config_app.command(name="set")(config_commands.set_config)
        config_app.command(name="get")(config_commands.get_config)
        config_app.command(name="list")(config_commands.list_config)
        config_app.command(name="reset")(config_commands.reset_config)
        app.add_typer(config_app)

        # Register client commands
        clients_app = typer.Typer(name="clients", help="Client management commands")
        clients_app.command(name="list")(client_commands.list_clients)
        clients_app.command(name="get")(client_commands.get_client)
        clients_app.command(name="create")(client_commands.create_client)
        clients_app.command(name="update")(client_commands.update_client)
        clients_app.command(name="delete")(client_commands.delete_client)
        clients_app.command(name="search")(client_commands.search_clients)
        app.add_typer(clients_app)

        # Register job commands
        jobs_app = typer.Typer(name="jobs", help="Job management commands")
        jobs_app.command(name="list")(job_commands.list_jobs)
        jobs_app.command(name="get")(job_commands.get_job)
        jobs_app.command(name="create")(job_commands.create_job)
        jobs_app.command(name="update")(job_commands.update_job)
        jobs_app.command(name="complete")(job_commands.complete_job)
        app.add_typer(jobs_app)

        # Register quote commands
        quotes_app = typer.Typer(name="quotes", help="Quote management commands")
        quotes_app.command(name="list")(quote_commands.list_quotes)
        quotes_app.command(name="get")(quote_commands.get_quote)
        quotes_app.command(name="create")(quote_commands.create_quote)
        quotes_app.command(name="send")(quote_commands.send_quote)
        quotes_app.command(name="approve")(quote_commands.approve_quote)
        app.add_typer(quotes_app)

        # Register invoice commands
        invoices_app = typer.Typer(name="invoices", help="Invoice management commands")
        invoices_app.command(name="list")(invoice_commands.list_invoices)
        invoices_app.command(name="get")(invoice_commands.get_invoice)
        invoices_app.command(name="create")(invoice_commands.create_invoice)
        invoices_app.command(name="send")(invoice_commands.send_invoice)
        app.add_typer(invoices_app)

        # Register query command
        app.command(name="query")(query_commands.execute_query)

    except ImportError as e:
        # Commands not yet created, will be registered later
        pass


# Register commands
register_commands()


if __name__ == "__main__":
    app()
