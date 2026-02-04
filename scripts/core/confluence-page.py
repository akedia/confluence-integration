#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "atlassian-python-api>=3.41.0",
#     "click>=8.1.0",
#     "markdownify>=0.11.0",
# ]
# ///
"""Confluence page operations - get, create, update pages."""

import sys
import re
from pathlib import Path

_script_dir = Path(__file__).parent
_lib_path = _script_dir.parent / "lib"
if _lib_path.exists():
    sys.path.insert(0, str(_lib_path.parent))

import click
from lib.client import get_confluence_client
from lib.output import format_output, success, error, warning


@click.group()
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--quiet', '-q', is_flag=True, help='Minimal output')
@click.option('--env-file', type=click.Path(), help='Environment file path')
@click.option('--debug', is_flag=True, help='Show debug information on errors')
@click.pass_context
def cli(ctx, output_json: bool, quiet: bool, env_file: str | None, debug: bool):
    """Confluence page operations.

    Get, create, and update Confluence pages.
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
@click.option('--id', 'page_id', help='Page ID')
@click.option('--space', help='Space key (required with --title)')
@click.option('--title', help='Page title (requires --space)')
@click.option('--format', 'output_format', type=click.Choice(['html', 'markdown', 'text']),
              default='markdown', help='Output format for content')
@click.option('--expand', '-e', help='Fields to expand (body.storage,body.view,history,space,version)')
@click.option('--json', 'cmd_json', is_flag=True, help='Output as JSON')
@click.option('--quiet', '-q', 'cmd_quiet', is_flag=True, help='Minimal output')
@click.pass_context
def get(ctx, page_id: str | None, space: str | None, title: str | None,
        output_format: str, expand: str | None, cmd_json: bool, cmd_quiet: bool):
    """Get page content.

    Retrieve a Confluence page by ID or by space key + title.

    Examples:

      # Get by page ID
      confluence-page get --id 229400379

      # Get by space and title
      confluence-page get --space DEV --title "Design Doc"

      # Get as HTML
      confluence-page get --id 229400379 --format html

      # Get with metadata
      confluence-page --json get --id 229400379 --expand history,version
    """
    client = ctx.obj['client']
    use_json = cmd_json or ctx.obj['json']
    use_quiet = cmd_quiet or ctx.obj['quiet']

    if not page_id and not (space and title):
        error("Must provide either --id or both --space and --title")
        sys.exit(1)

    try:
        # Get page
        if page_id:
            # Default expand to include body content
            if not expand:
                expand = 'body.storage,body.view,space,version'
            page = client.get_page_by_id(page_id, expand=expand)
        else:
            page = client.get_page_by_title(space, title, expand=expand or 'body.storage,body.view,space,version')
            if not page:
                error(f"Page not found: {title} in space {space}")
                sys.exit(1)

        if use_json:
            format_output(page, as_json=True)
        elif use_quiet:
            print(page.get('id', ''))
        else:
            _print_page(page, output_format)

    except Exception as e:
        if ctx.obj['debug']:
            raise
        error(f"Failed to get page: {e}")
        sys.exit(1)


def _html_to_markdown(html: str) -> str:
    """Convert HTML to Markdown."""
    try:
        from markdownify import markdownify as md
        return md(html, heading_style="ATX", strip=['script', 'style'])
    except ImportError:
        warning("markdownify not installed, returning HTML")
        return html


def _html_to_text(html: str) -> str:
    """Convert HTML to plain text."""
    # Simple HTML tag removal
    text = re.sub(r'<[^>]+>', '', html)
    # Decode common entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    # Clean up whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()


def _print_page(page: dict, output_format: str) -> None:
    """Pretty print page details."""
    title = page.get('title', 'Untitled')
    page_id = page.get('id', 'Unknown')
    space = page.get('space', {}).get('key', 'Unknown')
    version = page.get('version', {}).get('number', '?')
    
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}")
    print(f"ID: {page_id} | Space: {space} | Version: {version}")
    
    # Get body content
    body = page.get('body', {})
    html_content = body.get('storage', {}).get('value', '') or body.get('view', {}).get('value', '')
    
    if html_content:
        print(f"\n{'-' * 60}")
        print("CONTENT")
        print(f"{'-' * 60}\n")
        
        if output_format == 'html':
            print(html_content)
        elif output_format == 'markdown':
            print(_html_to_markdown(html_content))
        else:  # text
            print(_html_to_text(html_content))
    
    # Links
    links = page.get('_links', {})
    webui = links.get('webui', '')
    base = links.get('base', '')
    if webui and base:
        print(f"\n{'-' * 60}")
        print(f"URL: {base}{webui}")
    
    print()


@cli.command()
@click.option('--space', required=True, help='Space key')
@click.option('--title', required=True, help='Page title')
@click.option('--body', help='Page body content (HTML)')
@click.option('--body-file', type=click.Path(exists=True), help='File containing page body')
@click.option('--parent-id', help='Parent page ID')
@click.option('--dry-run', is_flag=True, help='Show what would be created')
@click.pass_context
def create(ctx, space: str, title: str, body: str | None, body_file: str | None,
           parent_id: str | None, dry_run: bool):
    """Create a new page.

    Examples:

      confluence-page create --space DEV --title "New Page" --body "<p>Hello</p>"

      confluence-page create --space DEV --title "New Page" --body-file content.html

      confluence-page create --space DEV --title "Child Page" --parent-id 123456
    """
    client = ctx.obj['client']

    # Get body content
    if body_file:
        body = Path(body_file).read_text()
    elif not body:
        body = "<p></p>"  # Empty page

    if dry_run:
        warning("DRY RUN - No changes will be made")
        print(f"\nWould create page:")
        print(f"  Space: {space}")
        print(f"  Title: {title}")
        print(f"  Parent ID: {parent_id or 'None (root level)'}")
        print(f"  Body length: {len(body)} chars")
        return

    try:
        result = client.create_page(
            space=space,
            title=title,
            body=body,
            parent_id=parent_id
        )
        
        if ctx.obj['json']:
            format_output(result, as_json=True)
        elif ctx.obj['quiet']:
            print(result.get('id', ''))
        else:
            success(f"Created page: {title}")
            print(f"  ID: {result.get('id')}")
            links = result.get('_links', {})
            if links.get('webui') and links.get('base'):
                print(f"  URL: {links['base']}{links['webui']}")

    except Exception as e:
        if ctx.obj['debug']:
            raise
        error(f"Failed to create page: {e}")
        sys.exit(1)


@cli.command()
@click.argument('page_id')
@click.option('--title', help='New title')
@click.option('--body', help='New body content (HTML)')
@click.option('--body-file', type=click.Path(exists=True), help='File containing new body')
@click.option('--dry-run', is_flag=True, help='Show what would be updated')
@click.pass_context
def update(ctx, page_id: str, title: str | None, body: str | None,
           body_file: str | None, dry_run: bool):
    """Update an existing page.

    PAGE_ID: The Confluence page ID

    Examples:

      confluence-page update 123456 --title "New Title"

      confluence-page update 123456 --body "<p>Updated content</p>"

      confluence-page update 123456 --body-file updated.html
    """
    client = ctx.obj['client']

    if not title and not body and not body_file:
        error("Must provide --title, --body, or --body-file")
        sys.exit(1)

    if body_file:
        body = Path(body_file).read_text()

    if dry_run:
        warning("DRY RUN - No changes will be made")
        print(f"\nWould update page {page_id}:")
        if title:
            print(f"  New title: {title}")
        if body:
            print(f"  New body length: {len(body)} chars")
        return

    try:
        # Get current page info for version
        current = client.get_page_by_id(page_id, expand='version,body.storage')
        current_title = current.get('title')
        current_body = current.get('body', {}).get('storage', {}).get('value', '')
        
        result = client.update_page(
            page_id=page_id,
            title=title or current_title,
            body=body or current_body
        )

        if ctx.obj['json']:
            format_output(result, as_json=True)
        elif ctx.obj['quiet']:
            print(page_id)
        else:
            success(f"Updated page {page_id}")
            if title:
                print(f"  ✓ title")
            if body:
                print(f"  ✓ body")

    except Exception as e:
        if ctx.obj['debug']:
            raise
        error(f"Failed to update page: {e}")
        sys.exit(1)


@cli.command()
@click.argument('page_id')
@click.option('--recursive', '-r', is_flag=True, help='Include all descendants')
@click.pass_context
def children(ctx, page_id: str, recursive: bool):
    """List child pages.

    PAGE_ID: The parent page ID

    Examples:

      confluence-page children 123456

      confluence-page children 123456 --recursive
    """
    client = ctx.obj['client']

    try:
        if recursive:
            # Get all descendants
            result = client.get_page_child_by_type(page_id, type='page', start=0, limit=100)
        else:
            result = client.get_page_child_by_type(page_id, type='page', start=0, limit=100)

        pages = result.get('results', []) if isinstance(result, dict) else result

        if ctx.obj['json']:
            format_output(pages, as_json=True)
        elif ctx.obj['quiet']:
            for page in pages:
                print(page.get('id', ''))
        else:
            if not pages:
                print("No child pages found")
            else:
                print(f"\nChild pages of {page_id}:")
                print("-" * 60)
                for page in pages:
                    print(f"  {page.get('id')}: {page.get('title')}")
                print(f"\n({len(pages)} pages)")

    except Exception as e:
        if ctx.obj['debug']:
            raise
        error(f"Failed to get children: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli()
