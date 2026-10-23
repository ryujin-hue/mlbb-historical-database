"""Meta router — 6 endpoints."""
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
        "name": "MLBB Historical Database API",
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


@router.get("/api/v1/version", summary="API and data version")
def version():
    return {
        "api_version": __version__,
        "data_cutoff": "2026-10-22",
        "current_live_patch": "2.2.16 (2026-09-16; hotfix 2.2.16a 2026-10-14)",
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
