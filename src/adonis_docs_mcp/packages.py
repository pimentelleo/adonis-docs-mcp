"""Fetcher for the AdonisJS community packages registry."""

from __future__ import annotations

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

        maintainers = []
        for m in data.get("maintainers", []):
            if isinstance(m, dict):
                maintainers.append(m.get("name", m.get("github", "")))
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

    for filename in filenames:
        raw = await _fetch_package_yaml(client, filename)
        if raw:
            pkg = _parse_package_yaml(raw)
            if pkg:
                packages.append(pkg)

    return packages
