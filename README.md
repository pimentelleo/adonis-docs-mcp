# adonis-docs-mcp

MCP server that gives AI agents fast access to **AdonisJS documentation** (v5, v6, v7).

Fetches raw markdown directly from the official GitHub repos and caches locally for speed.

## Quick Start

```bash
# Run with uvx (no install needed)
uvx adonis-docs-mcp
```

## Integration

### Claude Desktop / Claude Code

Add to your MCP settings:

```json
{
  "mcpServers": {
    "adonis-docs": {
      "command": "uvx",
      "args": ["adonis-docs-mcp"]
    }
  }
}
```

### VS Code / GitHub Copilot

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "adonis-docs": {
      "command": "uvx",
      "args": ["adonis-docs-mcp"]
    }
  }
}
```

### Cursor

Add to your MCP config:

```json
{
  "mcpServers": {
    "adonis-docs": {
      "command": "uvx",
      "args": ["adonis-docs-mcp"]
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_versions` | List all available AdonisJS doc versions (v5, v6, v7) |
| `list_sections` | Browse the documentation structure for a version |
| `get_doc` | Fetch the full markdown content of a specific page |
| `search_docs` | Search docs by keyword across titles and content |
| `clear_cache` | Clear the local documentation cache |

## Examples

```
# List what's available
list_versions()

# Browse v7 docs structure
list_sections(version="v7")

# Read the routing guide
get_doc(permalink="guides/basics/routing", version="v7")

# Search for authentication docs
search_docs(query="authentication", version="v7")

# Search across all versions
search_docs(query="middleware", version="all")
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `ADONIS_DOCS_CACHE_TTL` | `3600` | Cache TTL in seconds (default: 1 hour) |
| `ADONIS_DOCS_CACHE_DIR` | `~/.cache/adonis-docs-mcp` | Cache directory path |

## Documentation Sources

| Version | GitHub Repo | Status |
|---------|------------|--------|
| v7 | [adonisjs/v7-docs](https://github.com/adonisjs/v7-docs) | Latest (default) |
| v6 | [adonisjs/v6-docs](https://github.com/adonisjs/v6-docs) | Stable |
| v5 | [adonisjs/v5-docs](https://github.com/adonisjs/v5-docs) | Legacy |

## Development

```bash
# Clone and install
git clone <repo-url>
cd adonis-docs-mcp
uv sync

# Run locally
uv run adonis-docs-mcp

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run adonis-docs-mcp
```

## License

MIT
