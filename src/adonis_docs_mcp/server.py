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
from .packages import get_all_packages, find_package_by_name, get_package_readme
from .prompts.adonisjs_stack import (
    ADONISJS_STACK_GUIDELINES,
    BACKEND_GUIDELINES,
    CODE_QUALITY_GUIDELINES,
    FRONTEND_GUIDELINES,
)

mcp = FastMCP(
    "AdonisJS Docs",
    instructions=(
        "Provides access to AdonisJS framework documentation (v5, v6, v7), "
        "Edge.js template engine documentation, and the AdonisJS community "
        "packages registry. "
        "Use list_versions to see available AdonisJS versions, list_sections to browse "
        "the doc structure, get_doc to read a specific page, and search_docs "
        "to find relevant documentation. "
        "For Edge.js templates, use edge_list_sections, edge_get_doc, and edge_search_docs. "
        "For Lucid ORM (models, queries, migrations, relationships), use "
        "lucid_list_sections, lucid_get_doc, and lucid_search_docs. "
        "To discover community and official packages, use packages_list, packages_search, "
        "and packages_get. "
        "Before starting work on an AdonisJS v7 + Edge.js project, call "
        "get_backend_guidelines, get_frontend_guidelines, and get_code_quality_guidelines "
        "to load development rules and anti-AI-slop conventions."
    ),
)


def _get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers={"User-Agent": "adonis-docs-mcp/0.8.0"},
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
async def lucid_list_sections() -> str:
    """List all Lucid ORM documentation sections and pages.

    Returns a structured list of all categories and page titles with their
    permalinks. Covers guides, query builders, migrations, and models.
    """
    lines = [f"Documentation structure for {VERSIONS['lucid']['label']}:", ""]

    async with _get_client() as client:
        for section_name in VERSIONS["lucid"]["sections"]:
            section = await get_section_structure(client, "lucid", section_name)
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
async def lucid_get_doc(permalink: str) -> str:
    """Get the full content of a specific Lucid ORM documentation page.

    Args:
        permalink: The page permalink (e.g., "introduction", "models",
                   "relationships", "migrations", "select-query-builder").
                   Use lucid_list_sections to find available permalinks.

    Returns the raw markdown content of the documentation page.
    """
    async with _get_client() as client:
        page = await find_page_by_permalink(client, "lucid", permalink)
        if not page:
            return (
                f"Page '{permalink}' not found in Lucid ORM docs. "
                "Use lucid_list_sections to see available pages."
            )

        content = await fetch_doc_page(client, "lucid", page.section, page.content_path)
        if not content:
            return f"Failed to fetch content for '{permalink}' from GitHub."

        header = (
            f"# {page.title}\n"
            f"**Source:** Lucid ORM | **Category:** {page.category}\n"
            f"**Permalink:** {page.permalink}\n\n---\n\n"
        )
        return header + content


@mcp.tool()
async def lucid_search_docs(query: str) -> str:
    """Search Lucid ORM documentation by keyword.

    Searches through page titles and content for matching terms.

    Args:
        query: Search terms (e.g., "relationships", "migrations", "hooks")

    Returns matching documentation pages with snippets.
    """
    query_lower = query.lower().strip()
    if not query_lower:
        return "Please provide a search query."

    results = []

    async with _get_client() as client:
        pages = await get_all_pages(client, "lucid")

        for page in pages:
            title_match = query_lower in page.title.lower()
            permalink_match = query_lower in page.permalink.lower()

            content_snippet = ""
            if title_match or permalink_match:
                content = await fetch_doc_page(
                    client, "lucid", page.section, page.content_path
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
                    client, "lucid", page.section, page.content_path
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
        return f"No results found for '{query}' in Lucid ORM docs."

    lines = [f"Found {len(results)} result(s) for '{query}' in Lucid ORM docs:", ""]
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
async def packages_list(category: str = "") -> str:
    """List available AdonisJS community and official packages.

    Browse the AdonisJS packages registry to discover packages for
    authentication, database, storage, messaging, extensions, and more.

    Args:
        category: Optional category filter (e.g., "Authentication", "Database",
                  "Extensions", "Storage", "Security", "Authorization",
                  "Messaging", "Rendering"). Leave empty to list all.

    Returns a list of packages with name, description, npm package, category,
    and compatibility info.
    """
    async with _get_client() as client:
        packages = await get_all_packages(client)

    if not packages:
        return "Failed to fetch packages from the registry."

    if category:
        cat_lower = category.lower().strip()
        filtered = [p for p in packages if cat_lower in p.category.lower()]
        if not filtered:
            all_cats = sorted({p.category for p in packages})
            return (
                f"No packages found in category '{category}'.\n"
                f"Available categories: {', '.join(all_cats)}"
            )
        packages = filtered

    by_category: dict[str, list] = {}
    for pkg in packages:
        by_category.setdefault(pkg.category, []).append(pkg)

    lines = [f"AdonisJS Packages ({len(packages)} total):", ""]
    for cat_name in sorted(by_category):
        lines.append(f"## {cat_name}")
        for pkg in by_category[cat_name]:
            compat = f" (AdonisJS {pkg.compatibility})" if pkg.compatibility else ""
            badge = " [official]" if pkg.pkg_type == "official" else ""
            lines.append(f"  • {pkg.name}{badge} — {pkg.description}")
            lines.append(f"    npm: {pkg.npm}{compat}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def packages_search(query: str) -> str:
    """Search AdonisJS packages by keyword.

    Searches package names, descriptions, keywords, and categories.

    Args:
        query: Search terms (e.g., "jwt", "queue", "auth", "mail", "cache")

    Returns matching packages with details and install instructions.
    """
    query_lower = query.lower().strip()
    if not query_lower:
        return "Please provide a search query."

    async with _get_client() as client:
        packages = await get_all_packages(client)

    if not packages:
        return "Failed to fetch packages from the registry."

    results = []
    for pkg in packages:
        searchable = " ".join([
            pkg.name.lower(),
            pkg.description.lower(),
            pkg.category.lower(),
            pkg.npm.lower(),
            " ".join(k.lower() for k in pkg.keywords),
        ])
        if query_lower in searchable:
            results.append(pkg)

    if not results:
        return f"No packages found for '{query}'."

    lines = [f"Found {len(results)} package(s) for '{query}':", ""]
    for pkg in results:
        badge = " [official]" if pkg.pkg_type == "official" else ""
        compat = f"AdonisJS {pkg.compatibility}" if pkg.compatibility else "unknown"
        lines.append(f"  📦 **{pkg.name}**{badge}")
        lines.append(f"     {pkg.description}")
        lines.append(f"     npm: {pkg.npm} | Category: {pkg.category} | Compat: {compat}")
        if pkg.github:
            lines.append(f"     GitHub: {pkg.github}")
        lines.append(f"     Install: npm i {pkg.npm}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def packages_get(name: str) -> str:
    """Get detailed information about a specific AdonisJS package.

    Fetches the package metadata and its full README from GitHub, including
    installation instructions, configuration, and usage examples.

    Args:
        name: Package name or npm package name (e.g., "adonisjs-jwt",
              "@adonisjs/cache", "lucid", "ally").

    Returns package details and full README content.
    """
    async with _get_client() as client:
        pkg = await find_package_by_name(client, name)
        if not pkg:
            return (
                f"Package '{name}' not found. "
                "Use packages_search or packages_list to find available packages."
            )

        badge = " [official]" if pkg.pkg_type == "official" else " [3rd-party]"
        compat = f"AdonisJS {pkg.compatibility}" if pkg.compatibility else "unknown"

        lines = [
            f"# {pkg.name}{badge}",
            f"",
            f"**Description:** {pkg.description}",
            f"**Category:** {pkg.category}",
            f"**npm:** {pkg.npm}",
            f"**Compatibility:** {compat}",
            f"**Install:** npm i {pkg.npm}",
        ]
        if pkg.github:
            lines.append(f"**GitHub:** {pkg.github}")
        if pkg.website and pkg.website != pkg.github:
            lines.append(f"**Website:** {pkg.website}")
        if pkg.maintainers:
            lines.append(f"**Maintainers:** {', '.join(pkg.maintainers)}")
        if pkg.keywords:
            lines.append(f"**Keywords:** {', '.join(pkg.keywords)}")

        readme = await get_package_readme(client, pkg)
        if readme:
            lines.append("")
            lines.append("---")
            lines.append("")
            lines.append(readme)
        else:
            lines.append("")
            lines.append("(README not available — check the GitHub link above)")

        return "\n".join(lines)


@mcp.tool()
async def get_backend_guidelines() -> str:
    """Get AdonisJS v7 backend development guidelines.

    Returns architecture rules, Edge template conventions, controller patterns,
    form/validation rules, model/database conventions, and asset handling for
    server-rendered monolithic AdonisJS v7 + Edge.js applications.

    Call this before working on AdonisJS backend code (routes, controllers,
    models, services, validators, Edge views).
    """
    return BACKEND_GUIDELINES


@mcp.tool()
async def get_frontend_guidelines() -> str:
    """Get frontend anti-slop guidelines for HTML, CSS, and UI development.

    Returns rules for writing high-quality frontend code in Edge templates:
    semantic HTML, typography, color, layout, spacing, borders/shadows,
    animation, accessibility, responsive design, icons, and component states.

    These rules prevent the generic "AI-averaged" look that plagues generated
    frontend code. Call this before writing or editing HTML/CSS in Edge templates.
    """
    return FRONTEND_GUIDELINES


@mcp.tool()
async def get_code_quality_guidelines() -> str:
    """Get anti-slop code quality rules for any code changes.

    Returns rules to prevent low-quality AI-generated code: surgical changes
    only, no comment spam, no filler content, no bloated output, no invented
    structure, no unnecessary abstractions, no dependency additions, no
    speculative code, no SPA leakage, and domain-specific naming.

    Call this before making any code changes to an AdonisJS project.
    """
    return CODE_QUALITY_GUIDELINES


@mcp.tool()
async def clear_cache() -> str:
    """Clear the local documentation cache.

    Use this if you want to force-refresh documentation from GitHub.
    """
    count = cache.clear()
    return f"Cleared {count} cached file(s)."


@mcp.prompt()
def adonisjs_stack() -> str:
    """Development guidelines for AdonisJS v7 + Edge.js monolithic projects.

    Load this prompt before working on an AdonisJS v7 + Edge.js monolithic
    project. It provides anti-AI-slop rules, architecture constraints, and
    conventions for server-rendered applications.
    """
    return ADONISJS_STACK_GUIDELINES


def main():
    """Entry point for the MCP server (stdio transport)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
