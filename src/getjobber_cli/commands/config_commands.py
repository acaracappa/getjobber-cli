"""Configuration commands for GetJobber CLI."""

import typer
from typing_extensions import Annotated

from getjobber_cli.utils.config import Config
from getjobber_cli.utils.formatters import print_error, print_info, print_success


def set_config(
    key: Annotated[str, typer.Argument(help="Configuration key")],
    value: Annotated[str, typer.Argument(help="Configuration value")],
):
    """Set a configuration value."""
    try:
        config = Config()
        config.set(key, value)
        print_success(f"Configuration updated: {key}")

    except Exception as e:
        print_error(f"Failed to set configuration: {str(e)}")
        raise typer.Exit(1)


def get_config(
    key: Annotated[str, typer.Argument(help="Configuration key")],
):
    """Get a configuration value."""
    try:
        config = Config()
        value = config.get(key)

        if value is None:
            print_error(f"Configuration key not found: {key}")
            raise typer.Exit(1)

        # Mask sensitive values
        if key == "client_secret" and value:
            masked_value = f"{'*' * (len(value) - 4)}{value[-4:]}" if len(value) > 4 else "****"
            print_info(f"{key}: {masked_value}")
        else:
            print_info(f"{key}: {value}")

    except Exception as e:
        print_error(f"Failed to get configuration: {str(e)}")
        raise typer.Exit(1)


def list_config():
    """List all configuration values."""
    try:
        config = Config()
        all_config = config.get_all()

        if not all_config:
            print_info("No configuration found")
            return

        print_info("Configuration:\n")
        for key, value in all_config.items():
            # Mask sensitive values
            if key == "client_secret" and value:
                masked_value = f"{'*' * (len(value) - 4)}{value[-4:]}" if len(value) > 4 else "****"
                typer.echo(f"  {key}: {masked_value}")
            else:
                typer.echo(f"  {key}: {value}")

    except Exception as e:
        print_error(f"Failed to list configuration: {str(e)}")
        raise typer.Exit(1)


def reset_config():
    """Reset configuration to defaults."""
    try:
        confirm = typer.confirm("Are you sure you want to reset all configuration to defaults?")
        if not confirm:
            print_info("Reset cancelled.")
            raise typer.Exit(0)

        config = Config()
        config.reset()
        print_success("Configuration reset to defaults")

    except Exception as e:
        print_error(f"Failed to reset configuration: {str(e)}")
        raise typer.Exit(1)
