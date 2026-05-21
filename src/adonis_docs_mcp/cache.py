"""File-based cache with TTL support for AdonisJS docs."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path


DEFAULT_TTL = 3600  # 1 hour
CACHE_DIR = Path(os.environ.get(
    "ADONIS_DOCS_CACHE_DIR",
    Path.home() / ".cache" / "adonis-docs-mcp",
))


def _get_ttl() -> int:
    return int(os.environ.get("ADONIS_DOCS_CACHE_TTL", str(DEFAULT_TTL)))


def _cache_key(version: str, path: str) -> str:
    raw = f"{version}/{path}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def get(version: str, path: str) -> str | None:
    """Get cached content if it exists and hasn't expired."""
    key = _cache_key(version, path)
    fp = _cache_path(key)
    if not fp.exists():
        return None

    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
        if time.time() - data["timestamp"] > _get_ttl():
            fp.unlink(missing_ok=True)
            return None
        return data["content"]
    except (json.JSONDecodeError, KeyError):
        fp.unlink(missing_ok=True)
        return None


def put(version: str, path: str, content: str) -> None:
    """Store content in cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = _cache_key(version, path)
    fp = _cache_path(key)
    data = {
        "version": version,
        "path": path,
        "content": content,
        "timestamp": time.time(),
    }
    fp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def clear() -> int:
    """Clear all cached files. Returns number of files removed."""
    if not CACHE_DIR.exists():
        return 0
    count = 0
    for fp in CACHE_DIR.glob("*.json"):
        fp.unlink()
        count += 1
    return count
