"""Custom exceptions for GetJobber CLI."""


class JobberCLIError(Exception):
    """Base exception for all GetJobber CLI errors."""

    pass


class NotAuthenticatedError(JobberCLIError):
    """Raised when user is not authenticated or token is invalid."""

    def __init__(self, message: str = "Not authenticated. Please run 'getjobber-cli login' first."):
        self.message = message
        super().__init__(self.message)


class JobberAPIError(JobberCLIError):
    """Raised when the GetJobber API returns an error."""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"API Error ({self.status_code}): {self.message}"
        return f"API Error: {self.message}"


class RateLimitError(JobberAPIError):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "API rate limit exceeded. Please try again later.",
        retry_after: int = None,
    ):
        self.retry_after = retry_after
        if retry_after:
            message = f"{message} Retry after {retry_after} seconds."
        super().__init__(message, status_code=429)


class ConfigurationError(JobberCLIError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class OAuthError(JobberCLIError):
    """Raised when OAuth authentication flow fails."""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        if self.error_code:
            return f"OAuth Error ({self.error_code}): {self.message}"
        return f"OAuth Error: {self.message}"


class TokenStorageError(JobberCLIError):
    """Raised when token storage/retrieval fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class TokenExpiredError(NotAuthenticatedError):
    """Raised when token has expired and cannot be refreshed."""

    def __init__(
        self,
        message: str = "Authentication token has expired. Please run 'getjobber-cli login' again.",
    ):
        super().__init__(message)


class ValidationError(JobberCLIError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)

    def __str__(self):
        if self.field:
            return f"Validation Error ({self.field}): {self.message}"
        return f"Validation Error: {self.message}"


class GraphQLError(JobberAPIError):
    """Raised when GraphQL query/mutation returns errors."""

    def __init__(self, message: str, errors: list = None):
        self.errors = errors or []
        super().__init__(message)

    def __str__(self):
        if self.errors:
            error_messages = [err.get("message", str(err)) for err in self.errors]
            return f"GraphQL Error: {'; '.join(error_messages)}"
        return f"GraphQL Error: {self.message}"
