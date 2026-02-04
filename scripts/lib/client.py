"""Confluence client initialization for CLI scripts."""

from typing import Optional
from atlassian import Confluence
from requests import Response

from .config import load_env, validate_config, get_auth_mode

# === INLINE_START: client ===


class CaptchaError(Exception):
    """Error raised when Confluence requires CAPTCHA resolution."""

    def __init__(self, message: str, login_url: str):
        super().__init__(message)
        self.login_url = login_url


def _check_captcha_challenge(response: Response, confluence_url: str) -> None:
    """Check response for CAPTCHA challenge and raise exception if found."""
    header_name = "X-Authentication-Denied-Reason"
    if header_name not in response.headers:
        return

    header_value = response.headers[header_name]
    if "CAPTCHA_CHALLENGE" not in header_value:
        return

    login_url = f"{confluence_url}/login.action"
    if "; login-url=" in header_value:
        login_url = header_value.split("; login-url=")[1].strip()

    raise CaptchaError(
        f"CAPTCHA challenge detected!\n\n"
        f"  Confluence requires you to solve a CAPTCHA before API access is allowed.\n\n"
        f"  To resolve:\n"
        f"    1. Open {login_url} in your web browser\n"
        f"    2. Log in and complete the CAPTCHA challenge\n"
        f"    3. Retry this command\n\n"
        f"  This typically happens after several failed login attempts.",
        login_url=login_url
    )


def _patch_session_for_captcha(client: Confluence, confluence_url: str) -> None:
    """Patch the Confluence client session to detect CAPTCHA challenges."""
    original_request = client._session.request

    def patched_request(method: str, url: str, **kwargs) -> Response:
        response = original_request(method, url, **kwargs)
        _check_captcha_challenge(response, confluence_url)
        return response

    client._session.request = patched_request


def get_confluence_client(env_file: Optional[str] = None) -> Confluence:
    """Initialize and return a Confluence client.

    Supports two authentication modes:
    - Cloud: CONFLUENCE_USERNAME + CONFLUENCE_API_TOKEN
    - Server/DC: CONFLUENCE_PERSONAL_TOKEN (Personal Access Token)

    Args:
        env_file: Optional path to environment file

    Returns:
        Configured Confluence client instance

    Raises:
        FileNotFoundError: If env file doesn't exist
        ValueError: If configuration is invalid
        ConnectionError: If cannot connect to Confluence
    """
    config = load_env(env_file)

    errors = validate_config(config)
    if errors:
        raise ValueError("Configuration errors:\n  " + "\n  ".join(errors))

    url = config['CONFLUENCE_URL']
    auth_mode = get_auth_mode(config)

    # Determine if Cloud or Server/DC
    is_cloud = config.get('CONFLUENCE_CLOUD', '').lower() == 'true'

    # Auto-detect if not specified
    if 'CONFLUENCE_CLOUD' not in config:
        from urllib.parse import urlparse
        netloc = urlparse(url).netloc.lower()
        is_cloud = netloc == 'atlassian.net' or netloc.endswith('.atlassian.net')

    try:
        if auth_mode == 'pat':
            # Server/DC with Personal Access Token
            client = Confluence(
                url=url,
                token=config['CONFLUENCE_PERSONAL_TOKEN'],
                cloud=is_cloud
            )
        else:
            # Cloud with username + API token
            client = Confluence(
                url=url,
                username=config['CONFLUENCE_USERNAME'],
                password=config['CONFLUENCE_API_TOKEN'],
                cloud=is_cloud
            )

        # Patch session to detect CAPTCHA challenges (primarily for Server/DC)
        _patch_session_for_captcha(client, url)

        return client
    except CaptchaError:
        raise
    except Exception as e:
        if auth_mode == 'pat':
            raise ConnectionError(
                f"Failed to connect to Confluence at {url}\n\n"
                f"  Error: {e}\n\n"
                f"  Please verify:\n"
                f"    - CONFLUENCE_URL is correct\n"
                f"    - CONFLUENCE_PERSONAL_TOKEN is a valid Personal Access Token\n"
            )
        else:
            raise ConnectionError(
                f"Failed to connect to Confluence at {url}\n\n"
                f"  Error: {e}\n\n"
                f"  Please verify:\n"
                f"    - CONFLUENCE_URL is correct\n"
                f"    - CONFLUENCE_USERNAME is your email (Cloud) or username (Server/DC)\n"
                f"    - CONFLUENCE_API_TOKEN is valid\n"
            )

# === INLINE_END: client ===
