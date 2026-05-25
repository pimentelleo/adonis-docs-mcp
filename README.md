# adonis-docs-mcp

MCP server that gives AI agents fast access to **AdonisJS documentation** (v5, v6, v7) and **Edge.js template engine** documentation.

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

## Available Prompts

| Prompt | Description |
|--------|-------------|
| `adonisjs_stack` | Anti-AI-slop development guidelines for AdonisJS v7 + Edge.js monolithic projects. Covers architecture constraints, Edge template conventions, controller patterns, form handling, asset management, and 10 strict anti-slop rules. |

## Available Tools

### AdonisJS

| Tool | Description |
|------|-------------|
| `list_versions` | List all available AdonisJS doc versions (v5, v6, v7) |
| `list_sections` | Browse the documentation structure for a version |
| `get_doc` | Fetch the full markdown content of a specific page |
| `search_docs` | Search docs by keyword across titles and content |
| `clear_cache` | Clear the local documentation cache |

### Edge.js Templates

| Tool | Description |
|------|-------------|
| `edge_list_sections` | Browse the Edge.js documentation structure |
| `edge_get_doc` | Fetch the full markdown content of an Edge.js doc page |
| `edge_search_docs` | Search Edge.js docs by keyword |

### Development Guidelines

| Tool | Description |
|------|-------------|
| `get_backend_guidelines` | AdonisJS v7 backend rules: architecture, Edge templates, controllers, forms, models, assets |
| `get_frontend_guidelines` | Frontend anti-slop rules: semantic HTML, typography, color, layout, spacing, accessibility |
| `get_code_quality_guidelines` | Code quality anti-slop rules: surgical changes, no comment spam, no bloat, domain naming |

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

# Browse Edge.js template docs
edge_list_sections()

# Read Edge.js components docs
edge_get_doc(permalink="components/introduction")

# Search Edge.js docs
edge_search_docs(query="slots")

# Load guidelines before working on a project
get_backend_guidelines()
get_frontend_guidelines()
get_code_quality_guidelines()
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
| Edge.js | [edge-js/edgejs.dev](https://github.com/edge-js/edgejs.dev) | Template engine |

## Development

```bash
# Clone and install
git clone https://github.com/pimentelleo/adonis-docs-mcp.git
cd adonis-docs-mcp
uv sync

# Run locally
uv run adonis-docs-mcp

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run adonis-docs-mcp
```

## Publishing (maintainers)

This project uses [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) via GitHub Actions.

### One-time setup

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new **pending publisher**:
   - **Project name:** `adonis-docs-mcp`
   - **Owner:** `pimentelleo`
   - **Repository:** `adonis-docs-mcp`
   - **Workflow name:** `publish.yml`
   - **Environment name:** `pypi`
3. Save

### Releasing a new version

1. Update `version` in `pyproject.toml` and `src/adonis_docs_mcp/__init__.py`
2. Commit and push
3. Create a GitHub release (tag format: `v0.1.0`)
4. The publish workflow will automatically build and upload to PyPI

## License

MIT
