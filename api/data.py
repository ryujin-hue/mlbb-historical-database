"""CSV data access layer for the MLBB Historical Database API."""
import csv
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

BASE_DIR = Path(__file__).resolve().parent.parent
REF_DIR = BASE_DIR / "references"

DESCRIPTION = ("Open REST API over the MLBB (Mobile Legends: Bang Bang) historical "
               "database 2016-2026: patches, hero/item balance history, M-Series world "
               "championships, esports events, game systems, client/collabs and "
               "business records. Exactly 78 endpoints, all read-only.")

YEAR_RE = re.compile(r"(19|20)\d{2}")


@lru_cache(maxsize=None)
def load(name: str, ref: bool = False) -> list[dict]:
    """Load a dataset CSV (repo root) or reference CSV (references/)."""
    path = (REF_DIR / name) if ref else (BASE_DIR / name)
    with open(path, newline="", encoding="utf-8") as f:
        return [dict(r) for r in csv.DictReader(f)]


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def first_year(text: str) -> str:
    m = YEAR_RE.search(text or "")
    return m.group(0) if m else ""


def paginate(rows: list[dict], limit: int = 50, offset: int = 0):
    total = len(rows)
    return rows[offset: offset + limit], total


def envelope(endpoint: str, data, *, total: int | None = None,
             limit: int | None = None, offset: int | None = None, **extra):
    body: dict = {"endpoint": endpoint, "data": data}
    if isinstance(data, list):
        body["count"] = len(data)
        body["total"] = total if total is not None else len(data)
        if limit is not None:
            body["limit"] = limit
        if offset is not None:
            body["offset"] = offset
    body.update(extra)
    return body


def reports_list() -> list[str]:
    return sorted(p.stem for p in BASE_DIR.glob("*.md"))


def report_path(name: str) -> Path | None:
    for p in BASE_DIR.glob("*.md"):
        if p.stem == name:
            return p
    return None


def reference_tables() -> list[str]:
    return sorted(p.stem for p in REF_DIR.glob("*.csv"))


def image_url(image_path: str) -> str | None:
    """Absolute /img/ URL for a repo-local image path."""
    if not image_path or image_path.startswith(("MISSING", "NONE")):
        return None
    return "/img/" + quote(image_path)


def with_image_url(rows: list[dict]) -> list[dict]:
    for r in rows:
        r["image_url"] = image_url(r.get("image_path", ""))
    return rows
