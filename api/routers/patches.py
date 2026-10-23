"""Patches router — 8 endpoints."""
from fastapi import APIRouter, HTTPException, Query

from ..data import envelope, first_year, load, paginate

router = APIRouter(tags=["patches"])

PATCHES = lambda: load("patch_index.csv")  # noqa: E731
HERO_CH = lambda: load("hero_changes.csv")  # noqa: E731
ITEM_CH = lambda: load("item_changes.csv")  # noqa: E731


def _patch(version: str) -> dict:
    for p in PATCHES():
        if p["version"].lower() == version.lower():
            return p
    raise HTTPException(404, detail=f"patch not found: {version}")


@router.get("/api/v1/patches", summary="List all patch versions")
def patches(year: str | None = None, limit: int = Query(50, le=1000), offset: int = 0):
    rows = PATCHES()
    if year:
        rows = [p for p in rows if first_year(p["date"]) == year]
    page, total = paginate(rows, limit, offset)
    return envelope("/api/v1/patches", page, total=total, limit=limit, offset=offset)


@router.get("/api/v1/patches/count", summary="Patch count")
def patches_count():
    by_year: dict[str, int] = {}
    for p in PATCHES():
        y = first_year(p["date"]) or "unknown"
        by_year[y] = by_year.get(y, 0) + 1
    return envelope("/api/v1/patches/count", {"total": len(PATCHES()), "by_year": by_year})


@router.get("/api/v1/patches/latest", summary="Latest patch")
def patches_latest():
    return envelope("/api/v1/patches/latest", PATCHES()[-1])


@router.get("/api/v1/patches/year/{year}", summary="Patches released in a year")
def patches_year(year: str):
    rows = [p for p in PATCHES() if first_year(p["date"]) == year]
    if not rows:
        raise HTTPException(404, detail=f"no patches found for {year}")
    return envelope(f"/api/v1/patches/year/{year}", rows, total=len(rows))


@router.get("/api/v1/patches/{version}", summary="Patch detail")
def patch_detail(version: str):
    return envelope(f"/api/v1/patches/{version}", _patch(version))


@router.get("/api/v1/patches/{version}/hero-changes", summary="Hero changes in a patch")
def patch_hero_changes(version: str):
    rows = [r for r in HERO_CH() if r["version"].lower() == version.lower()]
    return envelope(f"/api/v1/patches/{version}/hero-changes", rows, total=len(rows))


@router.get("/api/v1/patches/{version}/item-changes", summary="Item changes in a patch")
def patch_item_changes(version: str):
    rows = [r for r in ITEM_CH() if r["version"].lower() == version.lower()]
    return envelope(f"/api/v1/patches/{version}/item-changes", rows, total=len(rows))


@router.get("/api/v1/patches/{version}/summary", summary="Patch summary (meta + change counts)")
def patch_summary(version: str):
    p = _patch(version)
    hc = [r for r in HERO_CH() if r["version"].lower() == version.lower()]
    ic = [r for r in ITEM_CH() if r["version"].lower() == version.lower()]
    by_type: dict[str, int] = {}
    for r in hc:
        by_type[r["change_type"]] = by_type.get(r["change_type"], 0) + 1
    return envelope(f"/api/v1/patches/{version}/summary", {
        "patch": p,
        "hero_change_count": len(hc),
        "hero_changes_by_type": by_type,
        "heroes_touched": sorted({r["hero"] for r in hc}),
        "item_change_count": len(ic),
        "items_touched": sorted({r["item"] for r in ic}),
    })
