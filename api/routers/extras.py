"""Extras router — 2 endpoints (lore/skins/tiers from heroes_extra.csv)."""
from fastapi import APIRouter, HTTPException, Query

from ..data import envelope, load, paginate

router = APIRouter(tags=["extras"])

ROWS = lambda: load("heroes_extra.csv")  # noqa: E731


@router.get("/api/v1/extras", summary="Hero extras (lore, skins, tiers, counters)")
def extras(category: str | None = None, hero: str | None = None,
           limit: int = Query(50, le=1000), offset: int = 0):
    rows = ROWS()
    if category:
        rows = [r for r in rows if category.lower() in r["category"].lower()]
    if hero:
        rows = [r for r in rows if hero.lower() in r["hero"].lower()]
    page, total = paginate(rows, limit, offset)
    return envelope("/api/v1/extras", page, total=total, limit=limit, offset=offset)


@router.get("/api/v1/extras/category/{category}", summary="Extras by category")
def extras_category(category: str, limit: int = Query(50, le=1000), offset: int = 0):
    rows = [r for r in ROWS() if category.lower() == r["category"].lower()]
    if not rows:
        cats = sorted({r["category"] for r in ROWS()})
        raise HTTPException(404, detail=f"no extras category '{category}'; available: {cats}")
    page, total = paginate(rows, limit, offset)
    return envelope(f"/api/v1/extras/category/{category}", page, total=total,
                    limit=limit, offset=offset)
