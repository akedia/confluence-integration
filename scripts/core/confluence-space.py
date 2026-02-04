#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "atlassian-python-api>=3.41.0",
#     "click>=8.1.0",
# ]
# ///
"""Confluence space operations - list and get space info."""

import sys
from pathlib import Path

_script_dir = Path(__file__).parent
_lib_path = _script_dir.parent / "lib"
if _lib_path.exists():
    sys.path.insert(0, str(_lib_path.parent))

import click
from lib.client import get_confluence_client
from lib.output import format_output, format_table, error


@click.group()
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--quiet', '-q', is_flag=True, help='Minimal output')
@click.option('--env-file', type=click.Path(), help='Environment file path')
@click.option('--debug', is_flag=True, help='Show debug information on errors')
@click.pass_context
def cli(ctx, output_json: bool, quiet: bool, env_file: str | None, debug: bool):
    """Confluence space operations.

    List and get information about Confluence spaces.
    """
    ctx.ensure_object(dict)
    ctx.obj['json'] = output_json
    ctx.obj['quiet'] = quiet
    ctx.obj['debug'] = debug
    try:
        ctx.obj['client'] = get_confluence_client(env_file)
    except Exception as e:
        if debug:
            raise
        error(str(e))
        sys.exit(1)


@cli.command()
@click.option('--max-results', '-n', default=100, help='Maximum spaces to return')
@click.option('--type', 'space_type', type=click.Choice(['global', 'personal', 'all']),
              default='all', help='Filter by space type')
@click.pass_context
def list(ctx, max_results: int, space_type: str):
    """List all spaces.

    Examples:

      confluence-space list

      confluence-space list --type global

      confluence-space --json list
    """
    client = ctx.obj['client']

    try:
        result = client.get_all_spaces(start=0, limit=max_results, space_type=space_type if space_type != 'all' else None)
        spaces = result.get('results', [])

        if ctx.obj['json']:
            format_output(spaces, as_json=True)
        elif ctx.obj['quiet']:
            for space in spaces:
                print(space.get('key', ''))
        else:
            if not spaces:
                print("No spaces found")
            else:
                rows = []
                for space in spaces:
                    rows.append({
                        'key': space.get('key', ''),
                        'name': space.get('name', '')[:40],
                        'type': space.get('type', ''),
                    })
                print(format_table(rows, ['key', 'name', 'type']))
                print(f"\n({len(spaces)} spaces)")

    except Exception as e:
        if ctx.obj['debug']:
            raise
        error(f"Failed to list spaces: {e}")
        sys.exit(1)


@cli.command()
@click.argument('space_key')
@click.option('--expand', '-e', help='Fields to expand (description,homepage)')
@click.pass_context
def get(ctx, space_key: str, expand: str | None):
    """Get space details.

    SPACE_KEY: The space key (e.g., DEV, PROJ)

    Examples:

      confluence-space get DEV

      confluence-space --json get DEV --expand description,homepage
    """
    client = ctx.obj['client']

    try:
        space = client.get_space(space_key, expand=expand or 'description,homepage')

        if ctx.obj['json']:
            format_output(space, as_json=True)
        elif ctx.obj['quiet']:
            print(space.get('key', ''))
        else:
            print(f"\n{'=' * 60}")
            print(f"{space.get('name', 'Unknown')}")
            print(f"{'=' * 60}")
            print(f"Key: {space.get('key', '')}")
            print(f"Type: {space.get('type', '')}")
            
            desc = space.get('description', {})
            if desc and desc.get('plain', {}).get('value'):
                print(f"\nDescription: {desc['plain']['value'][:200]}")
            
            links = space.get('_links', {})
            if links.get('webui') and links.get('base'):
                print(f"\nURL: {links['base']}{links['webui']}")
            
            print()

    except Exception as e:
        if ctx.obj['debug']:
            raise
        error(f"Failed to get space: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli()
