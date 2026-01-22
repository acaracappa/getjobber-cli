"""Job management commands for GetJobber CLI."""

from typing import Optional

import typer
from typing_extensions import Annotated

from getjobber_cli.api.client import GraphQLClient
from getjobber_cli.api.mutations import COMPLETE_JOB, CREATE_JOB, UPDATE_JOB
from getjobber_cli.api.queries import GET_JOB, LIST_JOBS
from getjobber_cli.auth.token_manager import get_token_manager
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


def _get_authenticated_client() -> GraphQLClient:
    """Get authenticated GraphQL client."""
    token_manager = get_token_manager()
    if not token_manager.is_authenticated():
        raise NotAuthenticatedError()

    access_token = token_manager.get_access_token()
    return GraphQLClient(access_token)


def list_jobs(
    limit: Annotated[int, typer.Option(help="Number of jobs to retrieve")] = DEFAULT_ITEMS_PER_PAGE,
    status: Annotated[Optional[str], typer.Option(help="Filter by status")] = None,
    format: Annotated[str, typer.Option(help="Output format (table, json, csv, yaml)")] = OUTPUT_FORMAT_TABLE,
):
    """List all jobs."""
    try:
        client = _get_authenticated_client()

        # Execute query
        variables = {"first": limit}
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
                    "Status": j.get("status", ""),
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
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def get_job(
    job_id: Annotated[str, typer.Argument(help="Job ID")],
):
    """Get detailed job information."""
    try:
        client = _get_authenticated_client()

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
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def create_job(
    client_id: Annotated[str, typer.Option(help="Client ID (required)")],
    title: Annotated[Optional[str], typer.Option(help="Job title")] = None,
    description: Annotated[Optional[str], typer.Option(help="Job description")] = None,
):
    """Create a new job."""
    try:
        # Interactive mode if title not provided
        if not title:
            typer.echo("Create New Job\n")
            title = typer.prompt("Job title")
            description = typer.prompt("Description (optional)", default="")

        # Build input
        job_input = {"clientId": client_id}
        if title:
            job_input["title"] = title
        if description:
            job_input["description"] = description

        # Execute mutation
        gql_client = _get_authenticated_client()
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
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def update_job(
    job_id: Annotated[str, typer.Argument(help="Job ID")],
    title: Annotated[Optional[str], typer.Option(help="Job title")] = None,
    description: Annotated[Optional[str], typer.Option(help="Job description")] = None,
    status: Annotated[Optional[str], typer.Option(help="Job status")] = None,
):
    """Update an existing job."""
    try:
        # Build input
        job_input = {}
        if title is not None:
            job_input["title"] = title
        if description is not None:
            job_input["description"] = description
        if status is not None:
            job_input["status"] = status

        if not job_input:
            print_error("No update fields provided")
            raise typer.Exit(1)

        # Execute mutation
        gql_client = _get_authenticated_client()
        result = gql_client.mutate(UPDATE_JOB, variables={"id": job_id, "input": job_input})

        # Check for errors
        if "jobUpdate" in result:
            user_errors = result["jobUpdate"].get("userErrors", [])
            if user_errors:
                for error in user_errors:
                    print_error(f"{error.get('path', '')}: {error.get('message', '')}")
                raise typer.Exit(1)

            updated_job = result["jobUpdate"].get("job")
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
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def complete_job(
    job_id: Annotated[str, typer.Argument(help="Job ID")],
):
    """Mark a job as complete."""
    try:
        # Execute mutation
        gql_client = _get_authenticated_client()
        result = gql_client.mutate(COMPLETE_JOB, variables={"id": job_id})

        # Check for errors
        if "jobComplete" in result:
            user_errors = result["jobComplete"].get("userErrors", [])
            if user_errors:
                for error in user_errors:
                    print_error(f"{error.get('path', '')}: {error.get('message', '')}")
                raise typer.Exit(1)

            completed_job = result["jobComplete"].get("job")
            if completed_job:
                print_success(f"Job {job_id} marked as complete!")
                format_single_item(completed_job)
            else:
                print_error("Failed to complete job")
                raise typer.Exit(1)

    except NotAuthenticatedError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GraphQLError as e:
        print_error(f"Failed to complete job: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)
