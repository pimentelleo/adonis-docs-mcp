"""Data models for AdonisJS documentation structure."""

from __future__ import annotations

from dataclasses import dataclass, field


VERSIONS = {
    "v7": {
        "repo": "adonisjs/v7-docs",
        "branch": "main",
        "content_prefix": "content",
        "sections": ["start", "guides", "reference"],
        "nav_file": "db.json",
        "nav_format": "grouped",  # array of {category, children[]}
        "label": "AdonisJS v7 (latest)",
    },
    "v6": {
        "repo": "adonisjs/v6-docs",
        "branch": "main",
        "content_prefix": "content/docs",
        "sections": ["docs"],
        "nav_file": "db.json",
        "nav_format": "flat",  # flat array of entries with category field
        "label": "AdonisJS v6",
    },
    "v5": {
        "repo": "adonisjs/v5-docs",
        "branch": "develop",
        "content_prefix": "content",
        "sections": ["guides", "reference", "cookbooks"],
        "nav_file": "menu.json",
        "nav_format": "nested",  # [{name, categories: [{name, docs: []}]}]
        "label": "AdonisJS v5",
    },
}


@dataclass
class DocPage:
    title: str
    permalink: str
    content_path: str
    section: str
    category: str
    version: str
    content: str | None = None


@dataclass
class DocCategory:
    name: str
    pages: list[DocPage] = field(default_factory=list)


@dataclass
class DocSection:
    name: str
    version: str
    categories: list[DocCategory] = field(default_factory=list)


@dataclass
class SearchResult:
    title: str
    permalink: str
    version: str
    section: str
    category: str
    snippet: str
