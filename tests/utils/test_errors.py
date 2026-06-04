"""Tests for custom exception classes."""

import pytest

from getjobber_cli.utils.errors import (
    ConfigurationError,
    GraphQLError,
    JobberAPIError,
    JobberCLIError,
    NotAuthenticatedError,
    OAuthError,
    RateLimitError,
    TokenExpiredError,
    TokenStorageError,
    ValidationError,
)


class TestExceptionHierarchy:
    """Verify the exception class hierarchy is set up correctly."""

    def test_all_exceptions_inherit_from_base(self):
        """All custom exceptions inherit from JobberCLIError."""
        assert issubclass(NotAuthenticatedError, JobberCLIError)
        assert issubclass(JobberAPIError, JobberCLIError)
        assert issubclass(ConfigurationError, JobberCLIError)
        assert issubclass(OAuthError, JobberCLIError)
        assert issubclass(TokenStorageError, JobberCLIError)
        assert issubclass(ValidationError, JobberCLIError)

    def test_rate_limit_inherits_from_api_error(self):
        """RateLimitError is a JobberAPIError."""
        assert issubclass(RateLimitError, JobberAPIError)

    def test_graphql_inherits_from_api_error(self):
        """GraphQLError is a JobberAPIError."""
        assert issubclass(GraphQLError, JobberAPIError)

    def test_token_expired_inherits_from_not_authenticated(self):
        """TokenExpiredError is a NotAuthenticatedError."""
        assert issubclass(TokenExpiredError, NotAuthenticatedError)

    def test_base_exception_is_exception(self):
        """JobberCLIError inherits from built-in Exception."""
        assert issubclass(JobberCLIError, Exception)


class TestNotAuthenticatedError:
    def test_default_message(self):
        err = NotAuthenticatedError()
        assert "Not authenticated" in str(err)

    def test_custom_message(self):
        err = NotAuthenticatedError("Custom message")
        assert "Custom message" in str(err)


class TestJobberAPIError:
    def test_message_without_status_code(self):
        err = JobberAPIError("Something broke")
        assert str(err) == "API Error: Something broke"

    def test_message_with_status_code(self):
        err = JobberAPIError("Server error", status_code=500)
        assert "500" in str(err)
        assert err.status_code == 500

    def test_stores_response_data(self):
        data = {"errors": ["x"]}
        err = JobberAPIError("Err", status_code=400, response_data=data)
        assert err.response_data == data


class TestRateLimitError:
    def test_default(self):
        err = RateLimitError()
        assert err.status_code == 429
        assert "rate limit" in str(err).lower()

    def test_with_retry_after(self):
        err = RateLimitError(retry_after=60)
        assert err.retry_after == 60
        assert "60" in str(err)


class TestOAuthError:
    def test_message_only(self):
        err = OAuthError("bad token")
        assert str(err) == "OAuth Error: bad token"

    def test_message_with_error_code(self):
        err = OAuthError("invalid", error_code="invalid_grant")
        assert "invalid_grant" in str(err)
        assert err.error_code == "invalid_grant"


class TestValidationError:
    def test_message_only(self):
        err = ValidationError("required")
        assert str(err) == "Validation Error: required"

    def test_message_with_field(self):
        err = ValidationError("required", field="email")
        assert "email" in str(err)
        assert err.field == "email"


class TestGraphQLError:
    def test_no_errors_list(self):
        err = GraphQLError("oops")
        assert "GraphQL Error" in str(err)

    def test_with_errors_list(self):
        errs = [{"message": "field missing"}, {"message": "id required"}]
        err = GraphQLError("failed", errors=errs)
        assert "field missing" in str(err)
        assert "id required" in str(err)
        assert err.errors == errs


class TestTokenExpiredError:
    def test_default_message(self):
        err = TokenExpiredError()
        assert "expired" in str(err).lower()

    def test_is_caught_as_not_authenticated(self):
        with pytest.raises(NotAuthenticatedError):
            raise TokenExpiredError()


class TestConfigurationError:
    def test_message(self):
        err = ConfigurationError("missing client_id")
        assert "missing client_id" in str(err)


class TestTokenStorageError:
    def test_message(self):
        err = TokenStorageError("keychain locked")
        assert "keychain locked" in str(err)
