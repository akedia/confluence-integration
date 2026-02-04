# Confluence Integration

Python CLI scripts for interacting with Atlassian Confluence.

## Features

- **Page operations**: Get, create, update pages
- **Search**: Query pages using CQL (Confluence Query Language)
- **Spaces**: List and get space information
- **Multiple auth modes**: Supports Cloud (API token) and Server/DC (PAT)

## Quick Start

1. **Setup credentials**:
   ```bash
   cd skills/confluence-integration
   uv run scripts/core/confluence-setup.py
   ```

2. **Validate connection**:
   ```bash
   uv run scripts/core/confluence-validate.py --verbose
   ```

3. **Get a page**:
   ```bash
   uv run scripts/core/confluence-page.py get --id 123456
   ```

## Authentication

### Confluence Cloud
```
CONFLUENCE_URL=https://yourcompany.atlassian.net/wiki
CONFLUENCE_USERNAME=your.email@company.com
CONFLUENCE_API_TOKEN=your-api-token
CONFLUENCE_CLOUD=true
```

### Confluence Server/Data Center
```
CONFLUENCE_URL=https://wiki.yourcompany.com
CONFLUENCE_PERSONAL_TOKEN=your-pat-token
CONFLUENCE_CLOUD=false
```

## Scripts

| Script | Description |
|--------|-------------|
| `confluence-setup.py` | Interactive credential configuration |
| `confluence-validate.py` | Test connection |
| `confluence-page.py` | Page operations (get/create/update) |
| `confluence-search.py` | Search with CQL |
| `confluence-space.py` | Space operations |

## Usage Examples

```bash
# Get page by ID
uv run scripts/core/confluence-page.py get --id 229400379

# Get page by space + title
uv run scripts/core/confluence-page.py get --space DEV --title "API Design"

# Search pages
uv run scripts/core/confluence-search.py query "space = DEV AND text ~ 'architecture'"

# List spaces
uv run scripts/core/confluence-space.py list

# Create page
uv run scripts/core/confluence-page.py create --space DEV --title "New Page" --body "<p>Content</p>"
```

## Output Formats

All scripts support:
- `--json`: JSON output
- `--quiet`: Minimal output (IDs only)
- `--debug`: Debug info on errors

## Dependencies

Managed by `uv` - dependencies are specified in each script's header.
