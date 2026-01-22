"""Output formatting utilities for GetJobber CLI."""

import csv
import io
import json
from typing import Any, Dict, List

import yaml
from rich.console import Console
from rich.table import Table

from getjobber_cli.constants import (
    OUTPUT_FORMAT_CSV,
    OUTPUT_FORMAT_JSON,
    OUTPUT_FORMAT_TABLE,
    OUTPUT_FORMAT_YAML,
)

console = Console()


def format_output(data: Any, format_type: str = OUTPUT_FORMAT_TABLE) -> str:
    """Format data for output.

    Args:
        data: Data to format.
        format_type: Output format (table, json, csv, yaml).

    Returns:
        Formatted string.
    """
    if format_type == OUTPUT_FORMAT_JSON:
        return format_json(data)
    elif format_type == OUTPUT_FORMAT_CSV:
        return format_csv(data)
    elif format_type == OUTPUT_FORMAT_YAML:
        return format_yaml(data)
    elif format_type == OUTPUT_FORMAT_TABLE:
        return format_table(data)
    else:
        # Default to JSON
        return format_json(data)


def format_json(data: Any, indent: int = 2) -> str:
    """Format data as JSON.

    Args:
        data: Data to format.
        indent: Indentation level.

    Returns:
        JSON string.
    """
    return json.dumps(data, indent=indent, default=str)


def format_yaml(data: Any) -> str:
    """Format data as YAML.

    Args:
        data: Data to format.

    Returns:
        YAML string.
    """
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def format_csv(data: Any) -> str:
    """Format data as CSV.

    Args:
        data: Data to format (should be list of dictionaries).

    Returns:
        CSV string.
    """
    if not data:
        return ""

    # Handle list of dictionaries
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()

    # Handle single dictionary
    if isinstance(data, dict):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data.keys())
        writer.writeheader()
        writer.writerow(data)
        return output.getvalue()

    # Fallback to JSON if can't convert to CSV
    return format_json(data)


def format_table(data: Any) -> None:
    """Format data as rich table and print to console.

    Args:
        data: Data to format (should be list of dictionaries).
    """
    if not data:
        console.print("[yellow]No data to display[/yellow]")
        return

    # Handle list of dictionaries
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        table = Table(show_header=True, header_style="bold magenta")

        # Add columns based on first item
        for key in data[0].keys():
            table.add_column(str(key).replace("_", " ").title())

        # Add rows
        for item in data:
            table.add_row(*[str(v) if v is not None else "" for v in item.values()])

        console.print(table)
        return

    # Handle single dictionary (detailed view)
    if isinstance(data, dict):
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Field")
        table.add_column("Value")

        for key, value in data.items():
            field_name = str(key).replace("_", " ").title()
            if isinstance(value, (dict, list)):
                value_str = format_json(value)
            else:
                value_str = str(value) if value is not None else ""
            table.add_row(field_name, value_str)

        console.print(table)
        return

    # Fallback: print as JSON
    console.print_json(format_json(data))


def format_single_item(item: Dict[str, Any]) -> None:
    """Format single item as detailed view.

    Args:
        item: Dictionary with item data.
    """
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value")

    for key, value in item.items():
        field_name = str(key).replace("_", " ").title()
        if isinstance(value, dict):
            # Format nested dictionaries
            value_str = "\n".join([f"{k}: {v}" for k, v in value.items()])
        elif isinstance(value, list):
            # Format lists
            if value and isinstance(value[0], dict):
                value_str = format_json(value)
            else:
                value_str = ", ".join([str(v) for v in value])
        else:
            value_str = str(value) if value is not None else ""

        table.add_row(field_name, value_str)

    console.print(table)


def print_success(message: str) -> None:
    """Print success message.

    Args:
        message: Success message.
    """
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print error message.

    Args:
        message: Error message.
    """
    console.print(f"[red]✗[/red] {message}", style="red")


def print_warning(message: str) -> None:
    """Print warning message.

    Args:
        message: Warning message.
    """
    console.print(f"[yellow]⚠[/yellow] {message}", style="yellow")


def print_info(message: str) -> None:
    """Print info message.

    Args:
        message: Info message.
    """
    console.print(f"[blue]ℹ[/blue] {message}")


def extract_list_data(response: Dict, resource_key: str) -> List[Dict]:
    """Extract list data from GraphQL response.

    Args:
        response: GraphQL response dictionary.
        resource_key: Key for the resource (e.g., 'clients', 'jobs').

    Returns:
        List of items.
    """
    if resource_key in response and "nodes" in response[resource_key]:
        return response[resource_key]["nodes"]
    return []


def extract_single_data(response: Dict, resource_key: str) -> Dict:
    """Extract single item data from GraphQL response.

    Args:
        response: GraphQL response dictionary.
        resource_key: Key for the resource (e.g., 'client', 'job').

    Returns:
        Item dictionary.
    """
    return response.get(resource_key, {})
