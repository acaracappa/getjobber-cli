"""GraphQL client for GetJobber API."""

from typing import Any, Dict, Optional

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from getjobber_cli.constants import API_BASE_URL, DEFAULT_TIMEOUT
from getjobber_cli.utils.errors import GraphQLError, JobberAPIError, NotAuthenticatedError


def create_client(access_token: str, api_url: str = API_BASE_URL) -> Client:
    """Create configured GraphQL client.

    Args:
        access_token: OAuth access token for authentication.
        api_url: API endpoint URL.

    Returns:
        Configured GQL Client instance.

    Raises:
        NotAuthenticatedError: If access token is not provided.
    """
    if not access_token:
        raise NotAuthenticatedError()

    # Configure transport with authentication
    # Note: GetJobber API requires X-API-Version header
    transport = RequestsHTTPTransport(
        url=api_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-API-Version": "2017-01-26",  # GetJobber API version
        },
        timeout=DEFAULT_TIMEOUT,
        verify=True,
        retries=3,
    )

    # Create client with schema introspection
    client = Client(
        transport=transport,
        fetch_schema_from_transport=False,  # Disable for now, can be enabled later
    )

    return client


def execute_query(client: Client, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict:
    """Execute a GraphQL query.

    Args:
        client: GQL Client instance.
        query: GraphQL query string.
        variables: Optional query variables.

    Returns:
        Query result dictionary.

    Raises:
        GraphQLError: If query execution fails.
        JobberAPIError: If API returns an error.
    """
    try:
        # Parse query
        parsed_query = gql(query)

        # Execute query
        result = client.execute(parsed_query, variable_values=variables)
        return result

    except Exception as e:
        error_message = str(e)

        # Check if it's a GraphQL error with structured errors
        if hasattr(e, "errors") and e.errors:
            raise GraphQLError("GraphQL query failed", errors=e.errors)

        # Check for authentication errors
        if "401" in error_message or "Unauthorized" in error_message:
            raise NotAuthenticatedError("Authentication failed. Please login again.")

        # Check for rate limiting
        if "429" in error_message or "rate limit" in error_message.lower():
            from getjobber_cli.utils.errors import RateLimitError

            raise RateLimitError()

        # Generic GraphQL error
        raise GraphQLError(error_message)


def execute_mutation(
    client: Client, mutation: str, variables: Optional[Dict[str, Any]] = None
) -> Dict:
    """Execute a GraphQL mutation.

    Args:
        client: GQL Client instance.
        mutation: GraphQL mutation string.
        variables: Optional mutation variables.

    Returns:
        Mutation result dictionary.

    Raises:
        GraphQLError: If mutation execution fails.
        JobberAPIError: If API returns an error.
    """
    # Mutations use the same execution as queries
    return execute_query(client, mutation, variables)


class GraphQLClient:
    """Wrapper class for GraphQL client operations."""

    def __init__(self, access_token: str):
        """Initialize GraphQL client wrapper.

        Args:
            access_token: OAuth access token.
        """
        self.client = create_client(access_token)

    def query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict:
        """Execute a GraphQL query.

        Args:
            query: GraphQL query string.
            variables: Optional query variables.

        Returns:
            Query result dictionary.
        """
        return execute_query(self.client, query, variables)

    def mutate(self, mutation: str, variables: Optional[Dict[str, Any]] = None) -> Dict:
        """Execute a GraphQL mutation.

        Args:
            mutation: GraphQL mutation string.
            variables: Optional mutation variables.

        Returns:
            Mutation result dictionary.
        """
        return execute_mutation(self.client, mutation, variables)
