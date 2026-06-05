"""Fetcher for the AdonisJS community packages registry."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass

import httpx
import yaml

from . import cache

logger = logging.getLogger(__name__)

REPO = "adonisjs-community/adonis-packages"
BRANCH = "main"
PACKAGES_PATH = "content/packages"
RAW_BASE = "https://raw.githubusercontent.com"
API_BASE = "https://api.github.com"
TIMEOUT = 30.0

# Cache namespace — keeps packages separate from docs cache keys
_CACHE_NS = "packages"


@dataclass
class PackageInfo:
    """Parsed package metadata from a YAML file."""

    name: str
    description: str
    category: str
    npm: str
    pkg_type: str  # "official" or "3rd-party"
    github: str
    website: str
    compatibility: str
    repo: str
    keywords: list[str]
    maintainers: list[str]


def _parse_package_yaml(raw: str) -> PackageInfo | None:
    """Parse a single package YAML string into a PackageInfo."""
    try:
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            return None

        compat = data.get("compatibility", {})
        adonis_compat = compat.get("adonis", "") if isinstance(compat, dict) else ""

        maintainers: list[str] = []
        for m in data.get("maintainers", []):
            if isinstance(m, dict):
                maintainers.append(str(m.get("name", m.get("github", ""))))
            elif isinstance(m, str):
                maintainers.append(m)

        return PackageInfo(
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=data.get("category", "Uncategorized"),
            npm=data.get("npm", ""),
            pkg_type=data.get("type", "3rd-party"),
            github=data.get("github", ""),
            website=data.get("website", ""),
            compatibility=adonis_compat,
            repo=data.get("repo", ""),
            keywords=data.get("keywords", []),
            maintainers=maintainers,
        )
    except yaml.YAMLError as exc:
        logger.warning("Failed to parse package YAML: %s", exc)
        return None


async def _fetch_file_list(client: httpx.AsyncClient) -> list[str]:
    """Fetch the list of YAML filenames from the packages directory."""
    cache_key = "file_list"
    cached = cache.get(_CACHE_NS, cache_key)
    if cached is not None:
        return json.loads(cached)

    url = f"{API_BASE}/repos/{REPO}/contents/{PACKAGES_PATH}?ref={BRANCH}"
    try:
        resp = await client.get(url, timeout=TIMEOUT)
        if resp.status_code != 200:
            logger.warning("Failed to fetch package list: %d", resp.status_code)
            return []

        entries = resp.json()
        filenames = [
            e["name"] for e in entries
            if isinstance(e, dict) and e.get("name", "").endswith(".yml")
        ]
        cache.put(_CACHE_NS, cache_key, json.dumps(filenames))
        return filenames
    except httpx.HTTPError as exc:
        logger.warning("HTTP error fetching package list: %s", exc)
        return []


async def _fetch_package_yaml(client: httpx.AsyncClient, filename: str) -> str | None:
    """Fetch raw YAML content for a single package file."""
    cache_key = f"yaml/{filename}"
    cached = cache.get(_CACHE_NS, cache_key)
    if cached is not None:
        return cached

    url = f"{RAW_BASE}/{REPO}/{BRANCH}/{PACKAGES_PATH}/{filename}"
    try:
        resp = await client.get(url, timeout=TIMEOUT)
        if resp.status_code != 200:
            logger.warning("Failed to fetch %s: %d", filename, resp.status_code)
            return None
        cache.put(_CACHE_NS, cache_key, resp.text)
        return resp.text
    except httpx.HTTPError as exc:
        logger.warning("HTTP error fetching %s: %s", filename, exc)
        return None


async def get_all_packages(client: httpx.AsyncClient) -> list[PackageInfo]:
    """Fetch and parse all packages from the registry."""
    filenames = await _fetch_file_list(client)
    packages: list[PackageInfo] = []

    # Limit concurrency to 15 to avoid github rate limits/disconnects
    sem = asyncio.Semaphore(15)

    async def fetch_and_parse(filename: str) -> PackageInfo | None:
        async with sem:
            raw = await _fetch_package_yaml(client, filename)
            if raw:
                return _parse_package_yaml(raw)
            return None

    results = await asyncio.gather(*(fetch_and_parse(f) for f in filenames))
    
    for pkg in results:
        if pkg:
            packages.append(pkg)

    return packages


async def get_package_readme(client: httpx.AsyncClient, pkg: PackageInfo) -> str | None:
    """Fetch the README from a package's GitHub repo."""
    if not pkg.repo:
        return None

    # repo field can be "owner/repo#branch" or just "owner/repo"
    repo = pkg.repo
    branch = "main"
    if "#" in repo:
        repo, branch = repo.rsplit("#", 1)

    cache_key = f"readme/{repo}"
    cached = cache.get(_CACHE_NS, cache_key)
    if cached is not None:
        return cached

    # Try common README filenames
    for readme_name in ("README.md", "readme.md", "Readme.md"):
        url = f"{RAW_BASE}/{repo}/{branch}/{readme_name}"
        try:
            resp = await client.get(url, timeout=TIMEOUT)
            if resp.status_code == 200:
                cache.put(_CACHE_NS, cache_key, resp.text)
                return resp.text
        except httpx.HTTPError:
            continue

    # Retry with "master" if "main" failed and no branch was specified
    if branch == "main" and "#" not in pkg.repo:
        for readme_name in ("README.md", "readme.md"):
            url = f"{RAW_BASE}/{repo}/master/{readme_name}"
            try:
                resp = await client.get(url, timeout=TIMEOUT)
                if resp.status_code == 200:
                    cache.put(_CACHE_NS, cache_key, resp.text)
                    return resp.text
            except httpx.HTTPError:
                continue

    logger.warning("No README found for %s", repo)
    return None


async def find_package_by_name(
    client: httpx.AsyncClient, name: str
) -> PackageInfo | None:
    """Find a package by name (case-insensitive, partial match)."""
    packages = await get_all_packages(client)
    name_lower = name.lower().strip()

    # Exact match first
    for pkg in packages:
        if pkg.name.lower() == name_lower or pkg.npm.lower() == name_lower:
            return pkg

    # Partial match
    for pkg in packages:
        if name_lower in pkg.name.lower() or name_lower in pkg.npm.lower():
            return pkg

    return None
