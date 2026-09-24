"""Job management commands for GetJobber CLI."""

from enum import Enum

from typing import Any, Dict, Optional

import typer
from typing_extensions import Annotated

from getjobber_cli.api.client import get_authenticated_client
from getjobber_cli.api.mutations import CLOSE_JOB, CREATE_JOB, UPDATE_JOB
from getjobber_cli.api.queries import GET_CLIENT_PROPERTIES, GET_JOB, LIST_JOBS
from getjobber_cli.constants import DEFAULT_ITEMS_PER_PAGE, OUTPUT_FORMAT_TABLE
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


class InvoicingType(str, Enum):
    """BillingStrategy. How the job is priced."""

    FIXED_PRICE = "FIXED_PRICE"
    VISIT_BASED = "VISIT_BASED"


class InvoicingSchedule(str, Enum):
    """BillingFrequencyEnum. When the job is billed."""

    ON_COMPLETION = "ON_COMPLETION"
    PERIODIC = "PERIODIC"
    PER_VISIT = "PER_VISIT"
    NEVER = "NEVER"


class IncompleteVisits(str, Enum):
    """What jobClose does with visits that have not happened yet."""

    DESTROY_ALL = "DESTROY_ALL"
    COMPLETE_PAST_DESTROY_FUTURE = "COMPLETE_PAST_DESTROY_FUTURE"


def _resolve_property_id(gql_client, client_id: str) -> str:
    """Find the property to attach a new job to.

    Jobs belong to a property, not to a client. Most clients have exactly one,
    so it can be resolved; when there are several the caller has to choose,
    because picking one silently would put the job at the wrong address.
    """
    result = gql_client.query(GET_CLIENT_PROPERTIES, variables={"id": client_id})
    client = result.get("client") or {}
    properties = client.get("properties") or []

    if not properties:
        print_error(f"Client {client_id} has no properties; a job needs one.")
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


def list_jobs(
    limit: Annotated[int, typer.Option(help="Number of jobs to retrieve")] = DEFAULT_ITEMS_PER_PAGE,
    status: Annotated[Optional[str], typer.Option(help="Filter by status")] = None,
    format: Annotated[
        str, typer.Option(help="Output format (table, json, csv, yaml)")
    ] = OUTPUT_FORMAT_TABLE,
):
    """List all jobs."""
    try:
        client = get_authenticated_client()

        # Execute query
        variables: Dict[str, Any] = {"first": limit}
        if status:
            variables["status"] = status

        result = client.query(LIST_JOBS, variables=variables)

        # Extract job list
        jobs = extract_list_data(result, "jobs")

        if format == OUTPUT_FORMAT_TABLE:
            # Simplified view for table
            simplified = [
                {
                    "ID": j.get("id", ""),
                    "Number": j.get("jobNumber", ""),
                    "Title": j.get("title", ""),
                    "Status": j.get("jobStatus", ""),
                    "Client": j.get("client", {}).get("companyName")
                    or f"{j.get('client', {}).get('firstName', '')} {j.get('client', {}).get('lastName', '')}".strip(),
                }
                for j in jobs
            ]
            format_table(simplified)
        else:
            output = format_output(jobs, format)
            typer.echo(output)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to list jobs: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        # Without this, the handler below catches our own Exit(0) from a
        # declined confirmation and turns it into a failure.
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def get_job(
    job_id: Annotated[str, typer.Argument(help="Job ID")],
):
    """Get detailed job information."""
    try:
        client = get_authenticated_client()

        # Execute query
        result = client.query(GET_JOB, variables={"id": job_id})

        # Extract job data
        job_data = extract_single_data(result, "job")

        if not job_data:
            print_error(f"Job not found: {job_id}")
            raise typer.Exit(1)

        # Display detailed view
        format_single_item(job_data)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to get job: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        # Without this, the handler below catches our own Exit(0) from a
        # declined confirmation and turns it into a failure.
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def create_job(
    client_id: Annotated[str, typer.Option(help="Client ID (required)")],
    property_id: Annotated[
        Optional[str],
        typer.Option(help="Property ID; resolved from the client when it has only one"),
    ] = None,
    title: Annotated[Optional[str], typer.Option(help="Job title")] = None,
    instructions: Annotated[Optional[str], typer.Option(help="Job instructions")] = None,
    invoicing_type: Annotated[
        InvoicingType, typer.Option(help="How the job is priced")
    ] = InvoicingType.FIXED_PRICE,
    invoicing_schedule: Annotated[
        InvoicingSchedule, typer.Option(help="When the job is billed")
    ] = InvoicingSchedule.ON_COMPLETION,
):
    """Create a new job."""
    try:
        # Interactive mode if title not provided
        if not title:
            typer.echo("Create New Job\n")
            title = typer.prompt("Job title")
            instructions = typer.prompt("Instructions (optional)", default="")

        gql_client = get_authenticated_client()

        if property_id is None:
            property_id = _resolve_property_id(gql_client, client_id)

        # propertyId and invoicing are both required by JobCreateAttributes.
        job_input: Dict[str, Any] = {
            "propertyId": property_id,
            "invoicing": {
                "invoicingType": invoicing_type.value,
                "invoicingSchedule": invoicing_schedule.value,
            },
        }
        if title:
            job_input["title"] = title
        if instructions:
            job_input["instructions"] = instructions

        typer.echo(f"Billing: {invoicing_type.value}, {invoicing_schedule.value}")

        result = gql_client.mutate(CREATE_JOB, variables={"input": job_input})

        # Check for errors
        if "jobCreate" in result:
            user_errors = result["jobCreate"].get("userErrors", [])
            if user_errors:
                for error in user_errors:
                    print_error(f"{error.get('path', '')}: {error.get('message', '')}")
                raise typer.Exit(1)

            created_job = result["jobCreate"].get("job")
            if created_job:
                print_success(f"Job created successfully! ID: {created_job.get('id')}")
                format_single_item(created_job)
            else:
                print_error("Failed to create job")
                raise typer.Exit(1)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to create job: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        # Without this, the handler below catches our own Exit(0) from a
        # declined confirmation and turns it into a failure.
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def update_job(
    job_id: Annotated[str, typer.Argument(help="Job ID")],
    title: Annotated[Optional[str], typer.Option(help="Job title")] = None,
    instructions: Annotated[Optional[str], typer.Option(help="Job instructions")] = None,
):
    """Update an existing job.

    Job status is not editable here; use `jobs close` and the Jobber web app.
    """
    try:
        # Build input
        job_input: Dict[str, Any] = {}
        if title is not None:
            job_input["title"] = title
        if instructions is not None:
            job_input["instructions"] = instructions

        if not job_input:
            print_error("No update fields provided")
            raise typer.Exit(1)

        # Execute mutation
        gql_client = get_authenticated_client()
        result = gql_client.mutate(UPDATE_JOB, variables={"jobId": job_id, "input": job_input})

        # Check for errors
        if "jobEdit" in result:
            user_errors = result["jobEdit"].get("userErrors", [])
            if user_errors:
                for error in user_errors:
                    print_error(f"{error.get('path', '')}: {error.get('message', '')}")
                raise typer.Exit(1)

            updated_job = result["jobEdit"].get("job")
            if updated_job:
                print_success(f"Job updated successfully!")
                format_single_item(updated_job)
            else:
                print_error("Failed to update job")
                raise typer.Exit(1)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to update job: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        # Without this, the handler below catches our own Exit(0) from a
        # declined confirmation and turns it into a failure.
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def close_job(
    job_id: Annotated[str, typer.Argument(help="Job ID")],
    incomplete_visits: Annotated[
        IncompleteVisits,
        typer.Option(help="What to do with visits that have not happened yet (required)"),
    ],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """Close a job.

    Replaces the old `complete` command: Jobber removed jobComplete, and
    jobClose requires deciding what happens to outstanding visits. There is no
    default, because one of the options deletes visit records.
    """
    try:
        if incomplete_visits is IncompleteVisits.DESTROY_ALL and not force:
            typer.echo(
                "DESTROY_ALL deletes every incomplete visit on this job, " "past and future."
            )
            if not typer.confirm(f"Close job {job_id} and delete those visits?"):
                typer.echo("Close cancelled.")
                raise typer.Exit(0)

        # Execute mutation
        gql_client = get_authenticated_client()
        result = gql_client.mutate(
            CLOSE_JOB,
            variables={
                "jobId": job_id,
                "input": {"modifyIncompleteVisitsBy": incomplete_visits.value},
            },
        )

        # Check for errors
        if "jobClose" in result:
            user_errors = result["jobClose"].get("userErrors", [])
            if user_errors:
                for error in user_errors:
                    print_error(f"{error.get('path', '')}: {error.get('message', '')}")
                raise typer.Exit(1)

            closed_job = result["jobClose"].get("job")
            if closed_job:
                print_success(f"Job {job_id} closed.")
                format_single_item(closed_job)
            else:
                print_error("Failed to close job")
                raise typer.Exit(1)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to close job: {str(e)}")
        raise typer.Exit(1)
    except typer.Exit:
        # Without this, the handler below catches our own Exit(0) from a
        # declined confirmation and turns it into a failure.
        raise
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)
