#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "click>=8.1.0",
# ]
# ///
"""Interactive setup for Confluence credentials."""

import sys
from pathlib import Path

import click

DEFAULT_ENV_FILE = Path.home() / ".env.confluence"


@click.command()
@click.option('--env-file', type=click.Path(), default=str(DEFAULT_ENV_FILE),
              help=f'Environment file path (default: {DEFAULT_ENV_FILE})')
def setup(env_file: str):
    """Interactive Confluence credential setup.

    Creates or updates ~/.env.confluence with your credentials.

    Supports two authentication modes:
    - Cloud: Username (email) + API Token
    - Server/Data Center: Personal Access Token (PAT)

    Examples:

      confluence-setup.py

      confluence-setup.py --env-file /path/to/.env.confluence
    """
    env_path = Path(env_file)
    
    click.echo("\n" + "=" * 60)
    click.echo("Confluence Credential Setup")
    click.echo("=" * 60)
    
    # Get Confluence URL
    click.echo("\nStep 1: Confluence URL")
    click.echo("  Example: https://wiki.example.com or https://company.atlassian.net/wiki")
    url = click.prompt("  Enter your Confluence URL")
    url = url.rstrip('/')
    
    # Determine auth type
    click.echo("\nStep 2: Authentication Type")
    click.echo("  1. Cloud (Atlassian Cloud) - uses email + API token")
    click.echo("  2. Server/Data Center (self-hosted) - uses Personal Access Token")
    
    auth_type = click.prompt("  Select authentication type", type=click.Choice(['1', '2']))
    
    config_lines = [
        "# Confluence configuration",
        f"CONFLUENCE_URL={url}",
    ]
    
    if auth_type == '1':
        # Cloud authentication
        click.echo("\nStep 3: Cloud Credentials")
        click.echo("  Get your API token from: https://id.atlassian.com/manage-profile/security/api-tokens")
        
        username = click.prompt("  Enter your email address")
        api_token = click.prompt("  Enter your API token", hide_input=True)
        
        config_lines.extend([
            f"CONFLUENCE_USERNAME={username}",
            f"CONFLUENCE_API_TOKEN={api_token}",
            "CONFLUENCE_CLOUD=true",
        ])
    else:
        # Server/DC authentication with PAT
        click.echo("\nStep 3: Personal Access Token (PAT)")
        click.echo("  Create a PAT in Confluence: Profile → Personal Access Tokens → Create token")
        
        pat = click.prompt("  Enter your Personal Access Token", hide_input=True)
        
        config_lines.extend([
            f"CONFLUENCE_PERSONAL_TOKEN={pat}",
            "CONFLUENCE_CLOUD=false",
        ])
    
    # Write config file
    config_content = "\n".join(config_lines) + "\n"
    
    click.echo(f"\nWriting configuration to: {env_path}")
    
    try:
        env_path.write_text(config_content)
        env_path.chmod(0o600)  # Restrict permissions
        
        click.echo("\n" + "=" * 60)
        click.echo("✓ Configuration saved successfully!")
        click.echo("=" * 60)
        click.echo("\nNext steps:")
        click.echo("  1. Test your connection:")
        click.echo("     uv run scripts/core/confluence-validate.py --verbose")
        click.echo("  2. Get a page:")
        click.echo("     uv run scripts/core/confluence-page.py get --id PAGE_ID")
        
    except Exception as e:
        click.echo(f"\n✗ Failed to write configuration: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    setup()
