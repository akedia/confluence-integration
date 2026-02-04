#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "atlassian-python-api>=3.41.0",
#     "click>=8.1.0",
# ]
# ///
"""Confluence search operations - query pages using CQL."""

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
@click.option('--quiet', '-q', is_flag=True, help='Minimal output (IDs only)')
@click.option('--env-file', type=click.Path(), help='Environment file path')
@click.option('--debug', is_flag=True, help='Show debug information on errors')
@click.pass_context
def cli(ctx, output_json: bool, quiet: bool, env_file: str | None, debug: bool):
    """Confluence search operations.

    Query Confluence pages using CQL (Confluence Query Language).
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
@click.argument('cql')
@click.option('--max-results', '-n', default=25, help='Maximum results to return')
@click.option('--expand', '-e', help='Fields to expand')
@click.pass_context
def query(ctx, cql: str, max_results: int, expand: str | None):
    """Search pages using CQL.

    CQL: Confluence Query Language query string

    Examples:

      # Search by text
      confluence-search query "text ~ 'keyword'"

      # Search in specific space
      confluence-search query "space = DEV AND text ~ 'design'"

      # Recently modified pages
      confluence-search query "lastModified >= now('-7d')"

      # By label
      confluence-search query "label = 'important'"

      # Combine conditions
      confluence-search query "space = PROJ AND type = page AND text ~ 'api'"

    Common CQL patterns:

      text ~ "search term"              # Full text search
      space = MYSPACE                   # In specific space
      label = "labelname"               # Has label
      type = page                       # Only pages (not blogposts)
      type = blogpost                   # Only blog posts
      lastModified >= now("-7d")        # Modified in last 7 days
      creator = "username"              # Created by user
      title ~ "keyword"                 # Title contains
    """
    client = ctx.obj['client']

    try:
        # Execute search
        results = client.cql(cql, limit=max_results, expand=expand)
        
        pages = results.get('results', [])

        if ctx.obj['json']:
            format_output(pages, as_json=True)
        elif ctx.obj['quiet']:
            for page in pages:
                content = page.get('content', page)
                print(content.get('id', ''))
        else:
            if not pages:
                print("No results found")
            else:
                _print_results(pages)
                print(f"\n({len(pages)} result{'s' if len(pages) != 1 else ''} found)")

    except Exception as e:
        if ctx.obj['debug']:
            raise
        error(f"Search failed: {e}")
        sys.exit(1)


def _print_results(results: list) -> None:
    """Print search results as a table."""
    rows = []
    for item in results:
        # CQL results have content nested
        content = item.get('content', item)
        
        row = {
            'id': content.get('id', ''),
            'title': content.get('title', '')[:50],
            'space': content.get('space', {}).get('key', '') if isinstance(content.get('space'), dict) else '',
            'type': content.get('type', ''),
        }
        rows.append(row)

    if rows:
        print(format_table(rows, ['id', 'title', 'space', 'type']))


@cli.command()
@click.argument('text')
@click.option('--space', '-s', help='Limit to specific space')
@click.option('--max-results', '-n', default=25, help='Maximum results')
@click.pass_context
def text(ctx, text: str, space: str | None, max_results: int):
    """Simple text search (convenience wrapper).

    TEXT: Search text

    Examples:

      confluence-search text "api documentation"

      confluence-search text "design" --space DEV

    This is equivalent to:
      confluence-search query "text ~ 'search text'"
    """
    # Build CQL
    cql = f'text ~ "{text}"'
    if space:
        cql = f'space = {space} AND {cql}'
    
    # Delegate to query command
    ctx.invoke(query, cql=cql, max_results=max_results)


if __name__ == '__main__':
    cli()
