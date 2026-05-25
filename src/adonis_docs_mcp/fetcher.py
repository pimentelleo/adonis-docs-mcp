"""GitHub raw content fetcher for AdonisJS documentation repos."""

from __future__ import annotations

import json
import logging

import httpx

from . import cache
from .models import VERSIONS, DocCategory, DocPage, DocSection

logger = logging.getLogger(__name__)

RAW_BASE = "https://raw.githubusercontent.com"
TIMEOUT = 30.0


def _raw_url(repo: str, branch: str, path: str) -> str:
    return f"{RAW_BASE}/{repo}/{branch}/{path}"


async def _fetch_raw(client: httpx.AsyncClient, repo: str, branch: str, path: str) -> str | None:
    """Fetch raw file content from GitHub."""
    url = _raw_url(repo, branch, path)
    try:
        resp = await client.get(url, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.text
        logger.warning("Failed to fetch %s: %d", url, resp.status_code)
        return None
    except httpx.HTTPError as exc:
        logger.warning("HTTP error fetching %s: %s", url, exc)
        return None


async def fetch_nav_json(client: httpx.AsyncClient, version: str, section: str) -> list[dict] | None:
    """Fetch and parse a section's navigation JSON file."""
    cache_key = f"nav/{section}"
    cached = cache.get(version, cache_key)
    if cached is not None:
        return json.loads(cached)

    vinfo = VERSIONS.get(version)
    if not vinfo:
        return None

    nav_file = vinfo["nav_file"]

    # v6 has a single db.json at the content_prefix level (no per-section)
    if vinfo["nav_format"] == "flat":
        path = f"{vinfo['content_prefix']}/{nav_file}"
    else:
        path = f"{vinfo['content_prefix']}/{section}/{nav_file}"

    content = await _fetch_raw(client, vinfo["repo"], vinfo["branch"], path)
    if content is None:
        return None

    cache.put(version, cache_key, content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON in %s/%s nav file", version, section)
        return None


async def fetch_doc_page(client: httpx.AsyncClient, version: str, section: str, content_path: str) -> str | None:
    """Fetch a specific documentation page's markdown content."""
    clean_path = content_path.lstrip("./")
    cache_key = f"pages/{section}/{clean_path}"
    cached = cache.get(version, cache_key)
    if cached is not None:
        return cached

    vinfo = VERSIONS.get(version)
    if not vinfo:
        return None

    full_path = f"{vinfo['content_prefix']}/{clean_path}" if vinfo["nav_format"] == "flat" else f"{vinfo['content_prefix']}/{section}/{clean_path}"
    content = await _fetch_raw(client, vinfo["repo"], vinfo["branch"], full_path)
    if content is None:
        return None

    cache.put(version, cache_key, content)
    return content


def _parse_grouped_nav(data: list[dict], section: str, version: str) -> list[DocCategory]:
    """Parse v7 format: [{category, children: [{title, permalink, contentPath}]}]"""
    categories = []
    for group in data:
        category_name = group.get("category", "Uncategorized")
        cat = DocCategory(name=category_name)
        for child in group.get("children", []):
            if "variations" in child:
                for var in child["variations"]:
                    cat.pages.append(DocPage(
                        title=f"{child.get('title', '')} ({var.get('name', '')})",
                        permalink=var.get("permalink", ""),
                        content_path=var.get("contentPath", ""),
                        section=section,
                        category=category_name,
                        version=version,
                    ))
            else:
                cat.pages.append(DocPage(
                    title=child.get("title", ""),
                    permalink=child.get("permalink", ""),
                    content_path=child.get("contentPath", ""),
                    section=section,
                    category=category_name,
                    version=version,
                ))
        categories.append(cat)
    return categories


def _parse_flat_nav(data: list[dict], section: str, version: str) -> list[DocCategory]:
    """Parse v6/edge format: [{title, permalink, contentPath, category}]"""
    cat_map: dict[str, DocCategory] = {}
    for entry in data:
        if entry.get("draft"):
            continue
        category_name = entry.get("category", "Uncategorized")
        if category_name not in cat_map:
            cat_map[category_name] = DocCategory(name=category_name)
        cat_map[category_name].pages.append(DocPage(
            title=entry.get("title", ""),
            permalink=entry.get("permalink", ""),
            content_path=entry.get("contentPath", ""),
            section=section,
            category=category_name,
            version=version,
        ))
    return list(cat_map.values())


def _parse_nested_nav(data: list[dict], section: str, version: str) -> list[DocCategory]:
    """Parse v5 format: [{name, categories: [{name, docs: [{title, permalink, contentPath}]}]}]"""
    categories = []
    for group in data:
        for cat_data in group.get("categories", []):
            category_name = cat_data.get("name", "Uncategorized")
            cat = DocCategory(name=category_name)
            for doc in cat_data.get("docs", []):
                cat.pages.append(DocPage(
                    title=doc.get("title", ""),
                    permalink=doc.get("permalink", ""),
                    content_path=doc.get("contentPath", ""),
                    section=section,
                    category=category_name,
                    version=version,
                ))
            categories.append(cat)
    return categories


async def get_section_structure(client: httpx.AsyncClient, version: str, section: str) -> DocSection | None:
    """Get the full structure of a documentation section."""
    nav_data = await fetch_nav_json(client, version, section)
    if nav_data is None:
        return None

    vinfo = VERSIONS[version]
    nav_format = vinfo["nav_format"]

    if nav_format == "grouped":
        categories = _parse_grouped_nav(nav_data, section, version)
    elif nav_format == "flat":
        categories = _parse_flat_nav(nav_data, section, version)
    elif nav_format == "nested":
        categories = _parse_nested_nav(nav_data, section, version)
    else:
        return None

    return DocSection(name=section, version=version, categories=categories)


async def get_all_pages(client: httpx.AsyncClient, version: str) -> list[DocPage]:
    """Get flat list of all pages across all sections for a version."""
    vinfo = VERSIONS.get(version)
    if not vinfo:
        return []

    all_pages = []
    for section_name in vinfo["sections"]:
        section = await get_section_structure(client, version, section_name)
        if section:
            for cat in section.categories:
                all_pages.extend(cat.pages)

    return all_pages


async def find_page_by_permalink(
    client: httpx.AsyncClient, version: str, permalink: str
) -> DocPage | None:
    """Find a page by its permalink across all sections."""
    permalink = permalink.strip("/").lower()

    pages = await get_all_pages(client, version)
    for page in pages:
        if page.permalink.strip("/").lower() == permalink:
            return page

    return None
