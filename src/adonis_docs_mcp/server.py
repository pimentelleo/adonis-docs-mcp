"""AdonisJS Docs MCP Server — exposes AdonisJS documentation to AI agents via MCP."""

from __future__ import annotations

import httpx
from mcp.server.fastmcp import FastMCP

from . import cache
from .fetcher import (
    fetch_doc_page,
    find_page_by_permalink,
    get_all_pages,
    get_section_structure,
)
from .models import VERSIONS, ADONIS_VERSIONS

mcp = FastMCP(
    "AdonisJS Docs",
    instructions=(
        "Provides access to AdonisJS framework documentation (v5, v6, v7) and "
        "Edge.js template engine documentation. "
        "Use list_versions to see available AdonisJS versions, list_sections to browse "
        "the doc structure, get_doc to read a specific page, and search_docs "
        "to find relevant documentation. "
        "For Edge.js templates, use edge_list_sections, edge_get_doc, and edge_search_docs."
    ),
)


def _get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers={"User-Agent": "adonis-docs-mcp/0.2.0"},
        follow_redirects=True,
    )


@mcp.tool()
async def list_versions() -> str:
    """List all available AdonisJS documentation versions.

    Returns a formatted list of supported AdonisJS versions with their labels.
    Use the version key (v5, v6, v7) in other tools.
    """
    lines = ["Available AdonisJS documentation versions:", ""]
    for key in ADONIS_VERSIONS:
        info = VERSIONS[key]
        sections = ", ".join(info["sections"])
        lines.append(f"  • {key}: {info['label']} (sections: {sections})")
    return "\n".join(lines)


@mcp.tool()
async def list_sections(version: str = "v7") -> str:
    """List all documentation sections and pages for a given AdonisJS version.

    Args:
        version: AdonisJS version — "v5", "v6", or "v7" (default: "v7")

    Returns a structured list of all categories and page titles with their permalinks.
    """
    version = version.lower().strip()
    vinfo = VERSIONS.get(version)
    if not vinfo:
        return f"Unknown version '{version}'. Available: {', '.join(VERSIONS.keys())}"

    lines = [f"Documentation structure for {vinfo['label']}:", ""]

    async with _get_client() as client:
        for section_name in vinfo["sections"]:
            section = await get_section_structure(client, version, section_name)
            if not section:
                lines.append(f"## {section_name} (unavailable)")
                continue

            lines.append(f"## {section_name.upper()}")
            for cat in section.categories:
                lines.append(f"  ### {cat.name}")
                for page in cat.pages:
                    lines.append(f"    - {page.title} → {page.permalink}")
            lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def get_doc(permalink: str, version: str = "v7") -> str:
    """Get the full content of a specific AdonisJS documentation page.

    Args:
        permalink: The page permalink (e.g., "guides/basics/routing", "installation").
                   Use list_sections to find available permalinks.
        version: AdonisJS version — "v5", "v6", or "v7" (default: "v7")

    Returns the raw markdown content of the documentation page.
    """
    version = version.lower().strip()
    vinfo = VERSIONS.get(version)
    if not vinfo:
        return f"Unknown version '{version}'. Available: {', '.join(VERSIONS.keys())}"

    async with _get_client() as client:
        page = await find_page_by_permalink(client, version, permalink)
        if not page:
            return (
                f"Page '{permalink}' not found in {version}. "
                "Use list_sections to see available pages."
            )

        content = await fetch_doc_page(client, version, page.section, page.content_path)
        if not content:
            return f"Failed to fetch content for '{permalink}' from GitHub."

        header = (
            f"# {page.title}\n"
            f"**Version:** {version} | **Section:** {page.section} | "
            f"**Category:** {page.category}\n"
            f"**Permalink:** {page.permalink}\n\n---\n\n"
        )
        return header + content


@mcp.tool()
async def search_docs(query: str, version: str = "v7") -> str:
    """Search AdonisJS documentation by keyword.

    Searches through page titles and content for matching terms.

    Args:
        query: Search terms (case-insensitive)
        version: AdonisJS version — "v5", "v6", or "v7" (default: "v7").
                 Use "all" to search across all versions.

    Returns matching documentation pages with snippets.
    """
    query_lower = query.lower().strip()
    if not query_lower:
        return "Please provide a search query."

    versions_to_search = (
        list(ADONIS_VERSIONS) if version.lower().strip() == "all"
        else [version.lower().strip()]
    )

    results = []

    async with _get_client() as client:
        for ver in versions_to_search:
            vinfo = VERSIONS.get(ver)
            if not vinfo:
                continue

            pages = await get_all_pages(client, ver)

            for page in pages:
                # Title match
                title_match = query_lower in page.title.lower()

                # Permalink match
                permalink_match = query_lower in page.permalink.lower()

                # Content match (fetch only if title/permalink don't match)
                content_snippet = ""
                if title_match or permalink_match:
                    content = await fetch_doc_page(
                        client, ver, page.section, page.content_path
                    )
                    if content:
                        snippet_idx = content.lower().find(query_lower)
                        if snippet_idx >= 0:
                            start = max(0, snippet_idx - 80)
                            end = min(len(content), snippet_idx + len(query_lower) + 80)
                            content_snippet = "..." + content[start:end].replace("\n", " ") + "..."
                        else:
                            content_snippet = content[:160].replace("\n", " ") + "..."
                    results.append({
                        "title": page.title,
                        "permalink": page.permalink,
                        "version": ver,
                        "section": page.section,
                        "category": page.category,
                        "snippet": content_snippet,
                        "match_type": "title" if title_match else "permalink",
                    })
                else:
                    # Try content search
                    content = await fetch_doc_page(
                        client, ver, page.section, page.content_path
                    )
                    if content and query_lower in content.lower():
                        snippet_idx = content.lower().find(query_lower)
                        start = max(0, snippet_idx - 80)
                        end = min(len(content), snippet_idx + len(query_lower) + 80)
                        content_snippet = "..." + content[start:end].replace("\n", " ") + "..."
                        results.append({
                            "title": page.title,
                            "permalink": page.permalink,
                            "version": ver,
                            "section": page.section,
                            "category": page.category,
                            "snippet": content_snippet,
                            "match_type": "content",
                        })

    if not results:
        return f"No results found for '{query}' in {version}."

    lines = [f"Found {len(results)} result(s) for '{query}':", ""]
    for r in results[:20]:  # Limit to 20 results
        lines.append(f"  📄 **{r['title']}** [{r['version']}]")
        lines.append(f"     Permalink: {r['permalink']}")
        lines.append(f"     Section: {r['section']} > {r['category']}")
        if r["snippet"]:
            lines.append(f"     Snippet: {r['snippet']}")
        lines.append("")

    if len(results) > 20:
        lines.append(f"  ... and {len(results) - 20} more results. Refine your query for better results.")

    return "\n".join(lines)


@mcp.tool()
async def edge_list_sections() -> str:
    """List all Edge.js template engine documentation sections and pages.

    Returns a structured list of all categories and page titles with their permalinks.
    """
    lines = [f"Documentation structure for {VERSIONS['edge']['label']}:", ""]

    async with _get_client() as client:
        for section_name in VERSIONS["edge"]["sections"]:
            section = await get_section_structure(client, "edge", section_name)
            if not section:
                lines.append(f"## {section_name} (unavailable)")
                continue

            for cat in section.categories:
                lines.append(f"  ### {cat.name}")
                for page in cat.pages:
                    lines.append(f"    - {page.title} → {page.permalink}")
                lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def edge_get_doc(permalink: str) -> str:
    """Get the full content of a specific Edge.js documentation page.

    Args:
        permalink: The page permalink (e.g., "introduction", "components/slots").
                   Use edge_list_sections to find available permalinks.

    Returns the raw markdown content of the documentation page.
    """
    async with _get_client() as client:
        page = await find_page_by_permalink(client, "edge", permalink)
        if not page:
            return (
                f"Page '{permalink}' not found in Edge.js docs. "
                "Use edge_list_sections to see available pages."
            )

        content = await fetch_doc_page(client, "edge", page.section, page.content_path)
        if not content:
            return f"Failed to fetch content for '{permalink}' from GitHub."

        header = (
            f"# {page.title}\n"
            f"**Source:** Edge.js | **Category:** {page.category}\n"
            f"**Permalink:** {page.permalink}\n\n---\n\n"
        )
        return header + content


@mcp.tool()
async def edge_search_docs(query: str) -> str:
    """Search Edge.js template engine documentation by keyword.

    Searches through page titles and content for matching terms.

    Args:
        query: Search terms (case-insensitive)

    Returns matching documentation pages with snippets.
    """
    query_lower = query.lower().strip()
    if not query_lower:
        return "Please provide a search query."

    results = []

    async with _get_client() as client:
        pages = await get_all_pages(client, "edge")

        for page in pages:
            title_match = query_lower in page.title.lower()
            permalink_match = query_lower in page.permalink.lower()

            content_snippet = ""
            if title_match or permalink_match:
                content = await fetch_doc_page(
                    client, "edge", page.section, page.content_path
                )
                if content:
                    snippet_idx = content.lower().find(query_lower)
                    if snippet_idx >= 0:
                        start = max(0, snippet_idx - 80)
                        end = min(len(content), snippet_idx + len(query_lower) + 80)
                        content_snippet = "..." + content[start:end].replace("\n", " ") + "..."
                    else:
                        content_snippet = content[:160].replace("\n", " ") + "..."
                results.append({
                    "title": page.title,
                    "permalink": page.permalink,
                    "category": page.category,
                    "snippet": content_snippet,
                    "match_type": "title" if title_match else "permalink",
                })
            else:
                content = await fetch_doc_page(
                    client, "edge", page.section, page.content_path
                )
                if content and query_lower in content.lower():
                    snippet_idx = content.lower().find(query_lower)
                    start = max(0, snippet_idx - 80)
                    end = min(len(content), snippet_idx + len(query_lower) + 80)
                    content_snippet = "..." + content[start:end].replace("\n", " ") + "..."
                    results.append({
                        "title": page.title,
                        "permalink": page.permalink,
                        "category": page.category,
                        "snippet": content_snippet,
                        "match_type": "content",
                    })

    if not results:
        return f"No results found for '{query}' in Edge.js docs."

    lines = [f"Found {len(results)} result(s) for '{query}' in Edge.js docs:", ""]
    for r in results[:20]:
        lines.append(f"  📄 **{r['title']}**")
        lines.append(f"     Permalink: {r['permalink']}")
        lines.append(f"     Category: {r['category']}")
        if r["snippet"]:
            lines.append(f"     Snippet: {r['snippet']}")
        lines.append("")

    if len(results) > 20:
        lines.append(f"  ... and {len(results) - 20} more results. Refine your query for better results.")

    return "\n".join(lines)


@mcp.tool()
async def clear_cache() -> str:
    """Clear the local documentation cache.

    Use this if you want to force-refresh documentation from GitHub.
    """
    count = cache.clear()
    return f"Cleared {count} cached file(s)."


def main():
    """Entry point for the MCP server (stdio transport)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
