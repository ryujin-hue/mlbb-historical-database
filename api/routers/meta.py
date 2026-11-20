"""Meta router — 6 endpoints."""
import re

from fastapi import APIRouter, HTTPException

from .. import __version__
from ..data import (BASE_DIR, DESCRIPTION, envelope, load, report_path,
                    reports_list, reference_tables)

router = APIRouter(tags=["meta"])

DATASETS = ["hero_master", "hero_changes", "item_changes", "items_master",
            "patch_index", "mseries", "esports", "systems", "client",
            "business", "heroes_extra", "images_manifest"]


@router.get("/", summary="API index")
def index():
    return {
        "name": "MLBB Almanac — Archive API",
        "version": __version__,
        "description": DESCRIPTION,
        "repo": "https://github.com/ryujin-hue/mlbb-historical-database",
        "interactive_docs": "/docs",
        "openapi": "/openapi.json",
        "total_endpoints": 78,
        "datasets": DATASETS,
        "reference_tables": reference_tables(),
        "reports": reports_list(),
    }


@router.get("/api/v1/health", summary="Health check")
def health():
    n_rows = sum(len(load(f"{d}.csv")) for d in DATASETS)
    return {"status": "ok", "api_version": __version__,
            "dataset_rows_loaded": n_rows, "reference_tables": len(reference_tables())}


_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _patch_timeline() -> tuple[str, str, str]:
    """(versi terkini, tarikh patch terkini, tarikh data paling baru).

    Versi diambil dari baris terakhir patch_index (senarai kronologi).
    Tarikh data diambil daripada tarikh ISO paling baru - baris auto-update
    yang tiada tarikh tepat tak boleh jadi data_cutoff.
    """
    rows = load("patch_index.csv")
    if not rows:
        return ("UNKNOWN", "", "")
    last = rows[-1]
    newest = ""
    for r in rows:
        d = (r.get("date") or "").strip()
        if _ISO_DATE.match(d) and d > newest:
            newest = d
    return (last.get("version") or "UNKNOWN", last.get("date") or "", newest)


@router.get("/api/v1/version", summary="API and data version")
def version():
    patch, patch_date, newest = _patch_timeline()
    return {
        "api_version": __version__,
        "data_cutoff": newest,
        "current_live_patch": f"{patch} ({patch_date})" if patch_date else patch,
        "current_ranked_season": "Season 42 (ends 2026-12-16 08:00 UTC)",
        "hero_count": len(load("hero_master.csv")),
        "m_series_latest": "M7 (Jan 2026, Jakarta); M8 announced for Turkiye, Jan 2027",
    }


@router.get("/api/v1/stats", summary="Dataset statistics")
def stats():
    out = {}
    for d in DATASETS:
        out[d] = len(load(f"{d}.csv"))
    refs = {t: len(load(f"{t}.csv", ref=True)) for t in reference_tables()}
    return envelope("/api/v1/stats", {
        "datasets": out, "datasets_total_rows": sum(out.values()),
        "reference_tables": refs,
        "reference_total_rows": sum(refs.values()),
        "images_on_disk": len(list((BASE_DIR / "images").rglob("*.*"))),
    })


@router.get("/api/v1/datasets", summary="Data dictionary for all tables")
def datasets(limit: int = 50, offset: int = 0):
    rows = load("data_dictionary.csv", ref=True)
    page, total = paginate_local(rows, limit, offset)
    return envelope("/api/v1/datasets", page, total=total, limit=limit, offset=offset)


@router.get("/api/v1/reports/{report_name}", summary="Fetch a markdown report")
def reports(report_name: str):
    if report_name not in reports_list():
        raise HTTPException(404, detail=f"report not found; available: {reports_list()}")
    path = report_path(report_name)
    return envelope(f"/api/v1/reports/{report_name}", {
        "name": report_name, "content_type": "text/markdown",
        "content": path.read_text(encoding="utf-8"),
    })


def paginate_local(rows, limit, offset):
    return rows[offset: offset + limit], len(rows)
