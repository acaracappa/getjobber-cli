"""Shared input resolution for write commands."""

from typing import Any, Dict, List, Optional

import typer

from getjobber_cli.api.queries import GET_CLIENT_PROPERTIES
from getjobber_cli.utils.formatters import print_error


def resolve_property_id(gql_client, client_id: str) -> str:
    """Find the property to attach a new record to.

    Jobs and quotes belong to a property, not directly to a client. Most
    clients have exactly one, so it can be resolved; when there are several the
    caller has to choose, because picking one silently would put the work at
    the wrong address.
    """
    result = gql_client.query(GET_CLIENT_PROPERTIES, variables={"id": client_id})
    client = result.get("client") or {}
    properties = client.get("properties") or []

    if not properties:
        print_error(f"Client {client_id} has no properties; one is required.")
        raise typer.Exit(1)
    if len(properties) > 1:
        print_error(
            f"Client {client_id} has {len(properties)} properties. "
            "Pass --property-id to choose one:"
        )
        for prop in properties:
            address = prop.get("address") or {}
            where = ", ".join(
                part for part in (address.get("street1"), address.get("city")) if part
            )
            typer.echo(f"  {prop['id']}  {where}")
        raise typer.Exit(1)
    return str(properties[0]["id"])


def parse_line_items(
    specs: Optional[List[str]], extra: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Parse repeated --line-item values into mutation input.

    Accepts `name`, `name:quantity` or `name:quantity:unit_price`. Quotes and
    invoices both require a non-empty line item list, and both take at least a
    name per item.
    """
    items: List[Dict[str, Any]] = []
    for spec in specs or []:
        parts = spec.split(":")
        name = parts[0].strip()
        if not name:
            print_error(f"Line item {spec!r} has no name.")
            raise typer.Exit(1)

        item: Dict[str, Any] = {"name": name}
        try:
            if len(parts) > 1 and parts[1].strip():
                item["quantity"] = float(parts[1])
            if len(parts) > 2 and parts[2].strip():
                item["unitPrice"] = float(parts[2])
        except ValueError:
            print_error(
                f"Line item {spec!r} has a non-numeric quantity or price. "
                "Expected name[:quantity[:unit_price]]."
            )
            raise typer.Exit(1)

        if extra:
            item.update(extra)
        items.append(item)
    return items
