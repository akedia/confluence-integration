#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "atlassian-python-api>=3.41.0",
#     "click>=8.1.0",
# ]
# ///
"""Validate Confluence connection and credentials."""

import sys
from pathlib import Path

_script_dir = Path(__file__).parent
_lib_path = _script_dir.parent / "lib"
if _lib_path.exists():
    sys.path.insert(0, str(_lib_path.parent))

import click
from lib.client import get_confluence_client
from lib.config import load_env, get_auth_mode
from lib.output import success, error


@click.command()
@click.option('--env-file', type=click.Path(), help='Environment file path')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
def validate(env_file: str | None, verbose: bool):
    """Validate Confluence connection and credentials.

    Tests the connection to Confluence using your configured credentials.

    Examples:

      confluence-validate.py

      confluence-validate.py --verbose

      confluence-validate.py --env-file /path/to/.env.confluence
    """
    try:
        config = load_env(env_file)
        url = config.get('CONFLUENCE_URL', 'Not configured')
        auth_mode = get_auth_mode(config)
        
        if verbose:
            click.echo("\n" + "=" * 60)
            click.echo("Confluence Connection Validation")
            click.echo("=" * 60)
            click.echo(f"\nURL: {url}")
            click.echo(f"Auth Mode: {'Personal Access Token' if auth_mode == 'pat' else 'Cloud (username + API token)'}")
            click.echo("\nConnecting...")
        
        client = get_confluence_client(env_file)
        
        # Test connection by getting server info or current user
        try:
            # Try to get spaces (lightweight check)
            spaces = client.get_all_spaces(start=0, limit=1)
            
            if verbose:
                click.echo(f"\n✓ Successfully connected to Confluence")
                if spaces and 'results' in spaces:
                    click.echo(f"  Found {spaces.get('size', 0)} spaces (showing 1)")
                click.echo("\n" + "=" * 60)
            
            success(f"Connected to {url}")
            
        except Exception as api_error:
            error(f"API call failed: {api_error}")
            sys.exit(1)
            
    except FileNotFoundError as e:
        error(str(e))
        click.echo("\nRun 'uv run scripts/core/confluence-setup.py' to configure credentials.")
        sys.exit(1)
    except ValueError as e:
        error(str(e))
        sys.exit(1)
    except ConnectionError as e:
        error(str(e))
        sys.exit(1)
    except Exception as e:
        error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    validate()
