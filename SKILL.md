---
name: confluence-integration
description: >
  Confluence API operations via Python CLI scripts. AUTOMATICALLY TRIGGER when user
  mentions Confluence URLs (https://wiki.*/pages/*, https://*.atlassian.net/wiki/*),
  page IDs, or asks about Confluence pages/spaces. Use when Claude needs to:
  (1) Get page content by ID or title, (2) Search pages with CQL,
  (3) List spaces, (4) Get page tree/children, (5) Create or update pages.
  If authentication fails, offer interactive credential setup via confluence-setup.py.
  Supports both Confluence Cloud and Server/Data Center with automatic auth detection.
---

# Confluence Integration

CLI scripts for Confluence operations using `uv run`. All scripts support `--help`, `--json`, `--quiet`, `--debug`.

## Auto-Trigger

Trigger when user mentions:
- **Confluence URLs**: `https://wiki.*/pages/*`, `https://*.atlassian.net/wiki/*`
- **Page IDs**: `pageId=123456`

When triggered by URL → extract page ID → run `confluence-page.py get --id 123456`

## Auth Failure Handling

When auth fails, offer: `uv run scripts/core/confluence-setup.py` (interactive credential setup)

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/core/confluence-setup.py` | Interactive credential config |
| `scripts/core/confluence-validate.py` | Verify connection |
| `scripts/core/confluence-page.py` | Get/create/update pages |
| `scripts/core/confluence-search.py` | Search with CQL |
| `scripts/core/confluence-space.py` | List spaces |

## Critical: Flag Ordering

Global flags **MUST** come **before** subcommand:
```bash
# Correct:  uv run scripts/core/confluence-page.py --json get --id 123456
# Wrong:    uv run scripts/core/confluence-page.py get --id 123456 --json
```

## Quick Examples

```bash
# Validate connection
uv run scripts/core/confluence-validate.py --verbose

# Get page by ID
uv run scripts/core/confluence-page.py get --id 229400379

# Get page by title and space
uv run scripts/core/confluence-page.py get --space MYSPACE --title "Page Title"

# Search pages
uv run scripts/core/confluence-search.py query "text ~ 'keyword'"

# List spaces
uv run scripts/core/confluence-space.py list
```

## Authentication

**Cloud**: `CONFLUENCE_URL` + `CONFLUENCE_USERNAME` + `CONFLUENCE_API_TOKEN`
**Server/DC**: `CONFLUENCE_URL` + `CONFLUENCE_PERSONAL_TOKEN`

Config via `~/.env.confluence` or env vars. Run `confluence-validate.py --verbose` to verify.

## CQL Quick Reference

```
# Search by text
text ~ "search term"

# Search in specific space
space = MYSPACE AND text ~ "term"

# Recently modified
lastModified >= now("-7d")

# By label
label = "important"

# By type
type = page
type = blogpost

# Combine conditions
space = DEV AND label = "architecture" AND text ~ "design"
```
