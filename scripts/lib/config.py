"""Environment configuration handling for Confluence CLI scripts."""

import os
from pathlib import Path
from typing import Optional

# === INLINE_START: config ===

# confluence-integration root directory
CONFLUENCE_INTEGRATION_DIR = Path(__file__).parent.parent.parent
SKILL_ENV_FILE = CONFLUENCE_INTEGRATION_DIR / ".env.confluence"
DEFAULT_ENV_FILE = Path.home() / ".env.confluence"

# Cloud authentication: CONFLUENCE_USERNAME + CONFLUENCE_API_TOKEN
# Server/DC authentication: CONFLUENCE_PERSONAL_TOKEN (PAT)
REQUIRED_URL = 'CONFLUENCE_URL'
CLOUD_VARS = ['CONFLUENCE_USERNAME', 'CONFLUENCE_API_TOKEN']
SERVER_VARS = ['CONFLUENCE_PERSONAL_TOKEN']
OPTIONAL_VARS = ['CONFLUENCE_CLOUD']
ALL_VARS = [REQUIRED_URL] + CLOUD_VARS + SERVER_VARS + OPTIONAL_VARS


def _load_env_file(path: Path) -> dict:
    """Load environment variables from a file."""
    config = {}
    if path.exists():
        with open(path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    config[key.strip()] = value.strip().strip('"').strip("'")
    return config


def load_env(env_file: Optional[str] = None) -> dict:
    """Load configuration from file with environment variable fallback.

    Priority order:
    1. Explicit env_file parameter (must exist if specified)
    2. ~/.env.confluence (user home directory)
    3. skill_dir/.env.confluence (skill directory)
    4. Environment variables (fallback for missing values)

    Supports two authentication modes:
    - Cloud: CONFLUENCE_URL + CONFLUENCE_USERNAME + CONFLUENCE_API_TOKEN
    - Server/DC: CONFLUENCE_URL + CONFLUENCE_PERSONAL_TOKEN

    Args:
        env_file: Path to environment file. If specified, file must exist.

    Returns:
        Dictionary of configuration values

    Raises:
        FileNotFoundError: If explicit env_file doesn't exist
    """
    config = {}

    # If explicit env_file is specified, it must exist
    if env_file:
        path = Path(env_file)
        if not path.exists():
            raise FileNotFoundError(f"Environment file not found: {path}")
        config = _load_env_file(path)
    else:
        # Try config files in priority order (first found wins)
        # 1. ~/.env.confluence (user config, highest priority)
        # 2. skill_dir/.env.confluence (shared default config)
        for path in [DEFAULT_ENV_FILE, SKILL_ENV_FILE]:
            file_config = _load_env_file(path)
            for key, value in file_config.items():
                if key not in config:
                    config[key] = value

    # Fill in missing values from environment variables
    for var in ALL_VARS:
        if var not in config and var in os.environ:
            config[var] = os.environ[var]

    return config


def validate_config(config: dict) -> list:
    """Validate configuration has all required variables.

    Supports two authentication modes:
    - Cloud: CONFLUENCE_URL + CONFLUENCE_USERNAME + CONFLUENCE_API_TOKEN
    - Server/DC: CONFLUENCE_URL + CONFLUENCE_PERSONAL_TOKEN

    Args:
        config: Configuration dictionary

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # CONFLUENCE_URL is always required
    if REQUIRED_URL not in config or not config[REQUIRED_URL]:
        errors.append(f"Missing required variable: {REQUIRED_URL}")

    # Validate URL format
    if REQUIRED_URL in config and config[REQUIRED_URL]:
        url = config[REQUIRED_URL]
        if not url.startswith(('http://', 'https://')):
            errors.append(f"CONFLUENCE_URL must start with http:// or https://: {url}")

    # Check for valid authentication configuration
    has_cloud_auth = all(config.get(var) for var in CLOUD_VARS)
    has_server_auth = config.get('CONFLUENCE_PERSONAL_TOKEN')

    if not has_cloud_auth and not has_server_auth:
        errors.append(
            "Missing authentication credentials. Provide either:\n"
            "    - CONFLUENCE_USERNAME + CONFLUENCE_API_TOKEN (for Cloud)\n"
            "    - CONFLUENCE_PERSONAL_TOKEN (for Server/DC)"
        )

    return errors


def get_auth_mode(config: dict) -> str:
    """Determine authentication mode from config.

    Args:
        config: Configuration dictionary

    Returns:
        'cloud' for Cloud auth, 'pat' for Personal Access Token
    """
    if config.get('CONFLUENCE_PERSONAL_TOKEN'):
        return 'pat'
    return 'cloud'

# === INLINE_END: config ===
