"""Constants for GetJobber CLI."""

# API URLs
API_BASE_URL = "https://api.getjobber.com/api/graphql"
OAUTH_AUTHORIZE_URL = "https://api.getjobber.com/api/oauth/authorize"
OAUTH_TOKEN_URL = "https://api.getjobber.com/api/oauth/token"

# OAuth Configuration
DEFAULT_REDIRECT_URI = "http://localhost:8888/callback"
CALLBACK_HOST = "localhost"
CALLBACK_PORT = 8888
CALLBACK_PATH = "/callback"
CALLBACK_TIMEOUT = 300  # 5 minutes in seconds

# Token Configuration
TOKEN_EXPIRY_BUFFER = 300  # 5 minutes in seconds (refresh before expiry)
DEFAULT_TOKEN_EXPIRY = 3600  # 1 hour in seconds

# Keyring Configuration
KEYRING_SERVICE_NAME = "getjobber-cli"
KEYRING_USERNAME = "default"

# Configuration
CONFIG_DIR_NAME = ".getjobber"
CONFIG_FILE_NAME = "config.json"
CREDENTIALS_FILE_NAME = "credentials.enc"

# Default Configuration Values
DEFAULT_OUTPUT_FORMAT = "table"
DEFAULT_ITEMS_PER_PAGE = 20

# API Rate Limiting
DEFAULT_RATE_LIMIT_CALLS = 100
DEFAULT_RATE_LIMIT_PERIOD = 60  # seconds

# HTTP Configuration
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_RETRIES = 3

# Output Formats
OUTPUT_FORMAT_TABLE = "table"
OUTPUT_FORMAT_JSON = "json"
OUTPUT_FORMAT_CSV = "csv"
OUTPUT_FORMAT_YAML = "yaml"

VALID_OUTPUT_FORMATS = [
    OUTPUT_FORMAT_TABLE,
    OUTPUT_FORMAT_JSON,
    OUTPUT_FORMAT_CSV,
    OUTPUT_FORMAT_YAML,
]

# CLI Metadata
APP_NAME = "getjobber-cli"
APP_VERSION = "1.1.1"
APP_DESCRIPTION = "CLI tool for accessing the GetJobber CRM GraphQL API"
